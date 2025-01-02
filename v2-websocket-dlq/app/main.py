from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Depends
from prometheus_client import make_asgi_app
from uuid import uuid4
import logging
from datetime import datetime, UTC

from .models.schemas import (
    TranslationJob,
    TranslationRequest,
    TranslationResponse,
    JobStatus,
)
from .core.connection_manager import ConnectionManager
from .core.job_processor import JobProcessor
from .core.dlq_manager import DLQManager
from .core.cache_manager import CacheManager
from .core.metrics import MetricsManager
from .db.database import DatabaseManager
from .db.repository import TranslationRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Video Translation Service")

# Initialize managers
dlq_manager = DLQManager()
cache_manager = CacheManager()
metrics_manager = MetricsManager()
connection_manager = ConnectionManager(dlq_manager=dlq_manager)
job_processor = JobProcessor(
    min_processing_time=1.0, max_processing_time=3.0, error_rate=0.2
)
db = DatabaseManager("postgresql+asyncpg://postgres:postgres@localhost/translation_db")

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await db.init_db()


@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on shutdown"""
    await db.close()


async def get_repository():
    """Dependency for getting database repository"""
    async with db.get_session() as session:
        yield TranslationRepository(session)


@app.post("/translate", response_model=TranslationResponse)
async def start_translation(
    request: TranslationRequest, repo: TranslationRepository = Depends(get_repository)
):
    """Start a new translation job"""
    with metrics_manager.track_processing_time():
        job_id = str(uuid4())
        job = TranslationJob(
            job_id=job_id,
            source_language=request.source_language,
            target_language=request.target_language,
            metadata=request.metadata,
        )

        # Store in database
        await repo.create_job(job)

        # Start processing
        await job_processor.start_job(job)

        # Update metrics
        metrics_manager.track_job_created()

        return TranslationResponse(
            job_id=job_id, status=JobStatus.PENDING, message="Translation job started"
        )


@app.websocket("/ws/job/{job_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    job_id: str,
    repo: TranslationRepository = Depends(get_repository),
):
    """WebSocket endpoint for job status updates"""
    try:
        # Check cache first
        if cached_status := await cache_manager.get_cached_status(job_id):
            await websocket.accept()
            await websocket.send_json(cached_status)
            return

        # Check database
        if db_job := await repo.get_job(job_id):
            if db_job.status in (JobStatus.COMPLETED, JobStatus.ERROR):
                await websocket.accept()
                await websocket.send_json(db_job.model_dump())
                return

        await connection_manager.connect(job_id, websocket)
        metrics_manager.set_active_connections(
            len(connection_manager._active_connections)
        )

        try:
            while True:
                data = await websocket.receive()
                if data["type"] == "websocket.disconnect":
                    break
                elif data["type"] == "websocket.ping":
                    await websocket.send_bytes(b"pong")
        except WebSocketDisconnect:
            pass
        finally:
            await connection_manager.disconnect(job_id, websocket)
            metrics_manager.set_active_connections(
                len(connection_manager._active_connections)
            )

    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        if websocket.client_state.CONNECTED:
            await websocket.close()


# Update job processor to use all components
@job_processor.on_job_update
async def handle_job_update(job: TranslationJob):
    """Handle job status updates"""
    async with db.get_session() as session:
        repo = TranslationRepository(session)
        await repo.update_job_status(job)

    await cache_manager.cache_job_status(job)
    await connection_manager.update_job_status(job)

    # Update metrics
    if job.status == JobStatus.COMPLETED:
        metrics_manager.track_job_completed()
    elif job.status == JobStatus.ERROR:
        metrics_manager.track_job_error()

    dlq_size = len(await dlq_manager.get_dlq_jobs())
    metrics_manager.set_dlq_size(dlq_size)
