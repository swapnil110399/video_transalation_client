from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import threading
import time
import random
import logging
from typing import Optional
import asyncio
import logging

# Configure logging for the server
server_logger = logging.getLogger(__name__)
server_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
server_logger.addHandler(handler)

app = FastAPI()


class TranslationJob(BaseModel):
    job_id: str
    status: str
    source_language: str
    target_language: str
    created_at: datetime
    error_message: Optional[str] = None


class TranslationServer:
    def __init__(self, error_rate=0.05):
        self.jobs = {}
        self.error_rate = error_rate
        self._lock = threading.Lock()

    def start_processing(self, job_id: str):
        async def process():
            server_logger.info(
                f"Starting processing for job: {job_id}"
            )  # added logging
            try:
                processing_time = random.uniform(5, 15)
                await asyncio.sleep(processing_time)

                if random.random() < self.error_rate:
                    raise Exception("Random translation error occurred")

                self.jobs[job_id].status = "completed"
                server_logger.info(
                    f"Job {job_id} completed successfully."
                )  # added logging

            except Exception as e:
                server_logger.exception(
                    f"Error processing job {job_id}: {e}"
                )  # log exception with traceback
                self.jobs[job_id].status = "error"
                self.jobs[job_id].error_message = str(e)

        asyncio.create_task(process())

    def create_job(
        self, job_id: str, source_lang: str, target_lang: str
    ) -> TranslationJob:
        job = TranslationJob(
            job_id=job_id,
            status="processing",
            source_language=source_lang,
            target_language=target_lang,
            created_at=datetime.utcnow(),
        )
        self.jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[TranslationJob]:
        return self.jobs.get(job_id)


# Create server instance
server = TranslationServer()


class TranslationRequest(BaseModel):
    job_id: str
    source_language: str
    target_language: str


@app.post("/translate")
async def translate(request: TranslationRequest):
    try:
        job = server.create_job(
            request.job_id, request.source_language, request.target_language
        )
        server.start_processing(request.job_id)
        server_logger.info(
            f"Translation started for job id: {request.job_id}"
        )  # added logging
        return {"message": "Translation started", "job_id": request.job_id}
    except Exception as e:
        server_logger.exception(
            f"Error starting translation: {e}"
        )  # log exception with traceback
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    server_logger.debug(f"Getting status for job: {job_id}")  # added logging
    job = server.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
