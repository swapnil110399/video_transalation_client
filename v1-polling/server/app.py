from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import threading
import random
import logging
from typing import Optional
import asyncio
import logging

"""
    An asynchronous server for managing translation jobs.

    This server implements translation job processing with simulated delays and errors
    to mimic real-world translation service behavior. It provides a REST API for
    job submission and status monitoring.

    The server maintains thread-safe job storage and implements configurable
    processing times and error rates for testing and simulation purposes.

    Key Components:
        - RESTful API endpoints for job management
        - Async job processing with random completion times
        - Configurable error rate simulation
        - Thread-safe job storage
        - Comprehensive logging system

    :param logging_level: Logging level for the server (defaults to INFO)
    
    Raises:
        HTTPException: When API endpoints encounter errors
        RuntimeError: When job storage operations fail
"""

# Configure logging for the server
server_logger = logging.getLogger(__name__)
server_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
server_logger.addHandler(handler)

app = FastAPI()


class TranslationJob(BaseModel):
    """
    Data model representing a translation job.

    Tracks the state and metadata of a translation job throughout its lifecycle.

    :param job_id: Unique identifier for the translation job
    :param status: Current job status ('processing', 'completed', or 'error')
    :param source_language: Source language code
    :param target_language: Target language code
    :param created_at: Timestamp when the job was created
    :param error_message: Error details if job failed, None otherwise
    """

    job_id: str
    status: str
    source_language: str
    target_language: str
    created_at: datetime
    error_message: Optional[str] = None


class TranslationServer:
    """
    Core server implementation for translation job processing.

    Manages job lifecycle including creation, processing, and status tracking
    with simulated processing times and configurable error rates.

    :param error_rate: Probability of random translation errors (0.0 to 1.0)

    Raises:
        RuntimeError: When job storage operations fail
        Exception: When translation processing fails
    """

    def __init__(self, error_rate=0.05):
        """
        Initialize the translation server.

        :param error_rate: Probability of random translation errors (default: 0.05)
        """
        self.jobs = {}
        self.error_rate = error_rate
        self._lock = threading.Lock()

    def start_processing(self, job_id: str):
        """
        Begin asynchronous processing of a translation job.

        Simulates translation processing with random delays and potential
        errors based on the configured error rate.

        :param job_id: Identifier of the job to process
        :raises:
            Exception: When random translation error occurs
            RuntimeError: When job storage access fails
        """

        async def process():
            server_logger.info(f"Starting processing for job: {job_id}")
            try:
                # Simulate processing time between 5 and 15 seconds
                processing_time = random.uniform(5, 15)
                await asyncio.sleep(processing_time)

                # Simulate random translation errors
                if random.random() < self.error_rate:
                    raise Exception("Random translation error occurred")

                self.jobs[job_id].status = "completed"
                server_logger.info(f"Job {job_id} completed successfully.")

            except Exception as e:
                server_logger.exception(f"Error processing job {job_id}: {e}")
                self.jobs[job_id].status = "error"
                self.jobs[job_id].error_message = str(e)

        asyncio.create_task(process())

    def create_job(
        self, job_id: str, source_lang: str, target_lang: str
    ) -> TranslationJob:
        """
        Create a new translation job.

        :param job_id: Unique identifier for the job
        :param source_lang: Source language code
        :param target_lang: Target language code
        :returns: Created TranslationJob instance
        :raises:
            RuntimeError: If job creation fails
        """
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
        """
        Retrieve a job by its identifier.

        :param job_id: Identifier of the job to retrieve
        :returns: TranslationJob if found, None otherwise
        """
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> Optional[TranslationJob]:
        """
        Cancel a running translation job.

        :param job_id: Identifier of the job to cancel
        :returns: Updated TranslationJob if found and cancelled, None otherwise
        """
        job = self.get_job(job_id)
        if job and job.status == "processing":
            job.status = "cancelled"
            job.error_message = "Job cancelled by user request"
            server_logger.info(f"Job {job_id} cancelled")
            return job
        return None


# Create singleton server instance
server = TranslationServer()


class TranslationRequest(BaseModel):
    """
    Data model for translation request payload.

    :param job_id: Unique identifier for the translation job
    :param source_language: Source language code
    :param target_language: Target language code
    """

    job_id: str
    source_language: str
    target_language: str


@app.post("/translate")
async def translate(request: TranslationRequest):
    """
    Endpoint to submit a new translation job.

    Creates a new translation job and begins asynchronous processing.

    :param request: Translation request containing job details
    :returns: Dictionary containing job ID and status message
    :raises:
        HTTPException: If job creation or processing fails
        RuntimeError: If server operations fail
    """
    try:
        job = server.create_job(
            request.job_id, request.source_language, request.target_language
        )
        server.start_processing(request.job_id)
        server_logger.info(f"Translation started for job id: {request.job_id}")
        return {"message": "Translation started", "job_id": request.job_id}
    except Exception as e:
        server_logger.exception(f"Error starting translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Endpoint to check translation job status.

    :param job_id: Identifier of the job to check
    :returns: Current job status and details
    :raises:
        HTTPException: If job is not found or status check fails
    """
    server_logger.debug(f"Getting status for job: {job_id}")
    job = server.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/job/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Endpoint to cancel a running translation job.

    :param job_id: Identifier of the job to cancel
    :returns: Updated job status
    :raises:
        HTTPException: If job is not found or cannot be cancelled
    """
    server_logger.info(f"Attempting to cancel job: {job_id}")
    job = server.cancel_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404, detail="Job not found or already completed/cancelled"
        )
    return job
