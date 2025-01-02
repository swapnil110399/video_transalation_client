import asyncio
import random
from datetime import datetime, UTC
import logging
from typing import Optional, Callable, Awaitable, List
from ..models.schemas import TranslationJob, JobStatus

logger = logging.getLogger(__name__)


class JobProcessor:
    """
    Simulates video translation processing with configurable behavior and error handling.

    Provides a mock implementation of a translation processing system with configurable
    processing times and error rates. Supports callback registration for job status
    updates and manages concurrent job processing.

    Example:
        processor = JobProcessor(min_processing_time=5.0, error_rate=0.1)

        @processor.on_job_update
        async def handle_update(job):
            print(f"Job {job.job_id} status: {job.status}")

        await processor.start_job(translation_job)

    Attributes:
        min_processing_time: Minimum processing duration in seconds
        max_processing_time: Maximum processing duration in seconds
        error_rate: Probability of job failure (0.0 to 1.0)
        _active_jobs: Dictionary of currently processing jobs
        _update_callbacks: List of registered status update callback functions
    """

    def __init__(
        self,
        min_processing_time: float = 5.0,
        max_processing_time: float = 15.0,
        error_rate: float = 0.1,
    ):
        """
        Initialize the job processor with configurable parameters.

        Args:
            min_processing_time: Minimum job processing time in seconds
            max_processing_time: Maximum job processing time in seconds
            error_rate: Probability of job failure (0.0 to 1.0)
        """
        self.min_processing_time = min_processing_time
        self.max_processing_time = max_processing_time
        self.error_rate = error_rate
        self._active_jobs = {}
        self._update_callbacks: List[Callable[[TranslationJob], Awaitable[None]]] = []

    def on_job_update(self, callback: Callable[[TranslationJob], Awaitable[None]]):
        """
        Decorator to register callback functions for job status updates.

        Args:
            callback: Async function that takes a TranslationJob parameter

        Returns:
            The registered callback function (for decorator usage)

        Example:
            @processor.on_job_update
            async def handle_update(job):
                print(f"Job {job.job_id} updated")
        """
        self._update_callbacks.append(callback)
        return callback

    async def _notify_update(self, job: TranslationJob):
        """
        Notify all registered callbacks of job status changes.

        Executes all registered callbacks with the updated job instance.
        Handles and logs any errors that occur during callback execution.

        Args:
            job: Updated TranslationJob instance
        """
        for callback in self._update_callbacks:
            try:
                await callback(job)
            except Exception as e:
                logger.error(f"Error in job update callback: {e}")

    async def start_job(self, job: TranslationJob) -> None:
        """
        Begin processing a translation job asynchronously.

        Creates a new processing task for the job and adds it to active jobs.
        Processing occurs in the background while this method returns immediately.

        Args:
            job: TranslationJob instance to process
        """
        logger.info(f"Starting processing for job: {job.job_id}")
        self._active_jobs[job.job_id] = job
        asyncio.create_task(self._process_job(job))

    async def _process_job(self, job: TranslationJob) -> None:
        """
        Simulate the translation processing workflow.

        Internal method that:
        - Simulates variable processing time
        - Introduces random failures based on error_rate
        - Updates job status and timestamps
        - Notifies callbacks of completion or failure
        - Handles cleanup of completed jobs

        Args:
            job: TranslationJob instance to process
        """
        try:
            # Simulate processing time
            processing_time = random.uniform(
                self.min_processing_time, self.max_processing_time
            )
            logger.info(f"Job {job.job_id} will take {processing_time:.2f} seconds")
            await asyncio.sleep(processing_time)

            # Simulate random errors
            if random.random() < self.error_rate:
                raise Exception("Random translation error occurred")

            # Update job status
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(UTC)
            logger.info(f"Job {job.job_id} completed successfully")
            await self._notify_update(job)

        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            job.status = JobStatus.ERROR
            job.error_message = str(e)
            job.completed_at = datetime.now(UTC)
            await self._notify_update(job)

        finally:
            # Cleanup
            if job.job_id in self._active_jobs:
                del self._active_jobs[job.job_id]

    def get_job(self, job_id: str) -> Optional[TranslationJob]:
        """
        Retrieve current status of an active job.

        Args:
            job_id: ID of the job to retrieve

        Returns:
            TranslationJob if job is active, None otherwise
        """
        return self._active_jobs.get(job_id)
