from typing import Dict, Optional, Set
from fastapi import WebSocket
import asyncio
import logging
from ..models.schemas import JobStatus, TranslationJob
from .dlq_manager import DLQManager
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and job status updates for translation jobs.

    Handles real-time client notifications for job status changes, connection lifecycle,
    and dead letter queue (DLQ) management for missed updates. Provides thread-safe
    operations using asyncio locks.

    Example:
        manager = ConnectionManager()
        await manager.connect(job_id, websocket)
        await manager.update_job_status(job)
        await manager.disconnect(job_id, websocket)

    Attributes:
        _active_connections: Mapping of job IDs to sets of active WebSocket connections
        _completed_jobs: Cache of completed translation jobs
        _error_jobs: Cache of failed translation jobs
        _lock: Asyncio lock for thread-safe operations
        dlq_manager: Manager for handling missed job updates
    """

    def __init__(self, dlq_manager: Optional[DLQManager] = None):
        """
        Initialize connection manager with optional DLQ manager.

        Args:
            dlq_manager: Custom DLQ manager instance, creates default if None
        """
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._completed_jobs: Dict[str, TranslationJob] = {}
        self._error_jobs: Dict[str, TranslationJob] = {}
        self._lock = asyncio.Lock()
        self.dlq_manager = dlq_manager or DLQManager()

    async def connect(self, job_id: str, websocket: WebSocket):
        """
        Register and initialize a new WebSocket connection for a job.

        Handles initial connection setup including:
        - Accepting the WebSocket connection
        - Checking for existing job results
        - Managing DLQ entries
        - Registering the connection for future updates

        Args:
            job_id: Unique identifier for the translation job
            websocket: FastAPI WebSocket connection to register
        """
        await websocket.accept()

        # First check if job is already completed
        if completed_job := self.get_job_status(job_id):
            await websocket.send_json(json.loads(completed_job.model_dump_json()))
            return

        # Check DLQ for stored result
        if result := await self.dlq_manager.get_result(job_id):
            await websocket.send_json(result)
            return

        async with self._lock:
            if job_id not in self._active_connections:
                self._active_connections[job_id] = set()
            self._active_connections[job_id].add(websocket)
            logger.info(f"New connection registered for job {job_id}")

            # If job was in DLQ, remove it since we now have an active connection
            if await self.dlq_manager.is_in_dlq(job_id):
                await self.dlq_manager.remove_from_dlq(job_id)

    async def disconnect(self, job_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection and handle cleanup.

        Manages connection removal including:
        - Removing the connection from active set
        - Cleaning up empty job entries
        - Moving job results to DLQ if needed

        Args:
            job_id: Unique identifier for the translation job
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if job_id in self._active_connections:
                self._active_connections[job_id].discard(websocket)
                if not self._active_connections[job_id]:
                    del self._active_connections[job_id]
                    # If job has a result but no connections, add to DLQ
                    if result := self.get_job_status(job_id):
                        await self.dlq_manager.add_to_dlq(job_id)
            logger.info(f"Connection removed for job {job_id}")

    async def update_job_status(self, job: TranslationJob):
        """
        Update job status and notify all connected clients.

        Handles status updates including:
        - Storing completed/error states
        - Persisting results to Redis
        - Broadcasting updates to connected clients
        - Managing failed connections
        - DLQ handling for jobs without active connections

        Args:
            job: Updated translation job instance
        """
        async with self._lock:
            if job.status == JobStatus.COMPLETED:
                self._completed_jobs[job.job_id] = job
            elif job.status == JobStatus.ERROR:
                self._error_jobs[job.job_id] = job

            # Store result in Redis
            await self.dlq_manager.store_result(job)

            # Notify all waiting clients
            if job.job_id in self._active_connections:
                disconnected = set()
                json_data = json.loads(job.model_dump_json())
                for connection in self._active_connections[job.job_id]:
                    try:
                        await connection.send_json(json_data)
                    except Exception as e:
                        logger.error(f"Failed to send update to client: {e}")
                        disconnected.add(connection)

                # Clean up disconnected clients
                for connection in disconnected:
                    await self.disconnect(job.job_id, connection)
            else:
                # If no active connections, add to DLQ
                await self.dlq_manager.add_to_dlq(job.job_id)

    def get_job_status(self, job_id: str) -> Optional[TranslationJob]:
        """
        Retrieve current job status if completed or errored.

        Args:
            job_id: Unique identifier for the translation job

        Returns:
            TranslationJob if found in completed or error cache, None otherwise
        """
        return self._completed_jobs.get(job_id) or self._error_jobs.get(job_id)
