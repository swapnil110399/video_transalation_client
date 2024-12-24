import asyncio
import aiohttp
from uuid import uuid4
from typing import Dict, Any, Optional
import logging

"""
    An asynchronous client library for managing translation jobs.

    This module provides a client implementation for interacting with the translation
    service, handling job creation, status monitoring, and result retrieval.

    The client implements intelligent polling with configurable backoff strategies
    to efficiently monitor job status while minimizing API load.

    Key Components:
        - Asynchronous HTTP communication using aiohttp
        - Configurable timeout and polling behavior
        - Intelligent backoff strategy for status checks
        - Comprehensive error handling and logging
    
    Raises:
        TranslationError: When translation or communication fails
        aiohttp.ClientError: For HTTP-related errors
        ValueError: For invalid configuration parameters
"""

# Set up logging
client_logger = logging.getLogger(__name__)
client_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
client_logger.addHandler(handler)


class TranslationConfig:
    def __init__(
        self, base_timeout=30, min_delay=0.5, max_delay=3.0, progressive_delay=True
    ):
        """
        Configuration class for managing translation job timeouts and polling behavior.

        This class handles the timing configuration for translation job monitoring,
        including how long to wait for completion and how frequently to check status.

        :param base_timeout: Maximum time (in seconds) to wait for a job to complete.
                           After this duration, the job will be considered timed out.
                           Defaults to 30 seconds.

        :param min_delay: Minimum delay (in seconds) between consecutive status checks.
                         This prevents too frequent API calls when checking job status.
                         Defaults to 0.5 seconds.

        :param max_delay: Maximum delay (in seconds) between consecutive status checks.
                         Ensures that the status is checked at least this frequently.
                         Should be less than base_timeout. Defaults to 3.0 seconds.

        :param progressive_delay: If True, the delay between status checks will gradually
                                increase if the job status remains unchanged. This helps
                                reduce unnecessary API calls for longer-running jobs.
                                If False, uses constant min_delay between checks.
                                Defaults to True.
        """
        self.base_timeout = base_timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.progressive_delay = progressive_delay


class TranslationError(Exception):
    """Custom exception for translation service errors."""

    pass


class VideoTranslationClient:
    """
    An asynchronous client for managing video translation jobs.

    The client uses exponential backoff with configurable parameters to efficiently
    poll for job status while avoiding excessive API calls.

    :param base_url: The base URL of the translation API service.
    :param config: Configuration object controlling timeouts and polling behavior.
                  If None, uses default TranslationConfig settings.

    Raises:
        TranslationError: When the translation job fails or API communication fails
        TimeoutError: When the job doesn't complete within configured timeout
        aiohttp.ClientError: For HTTP-related errors
    """

    def __init__(self, base_url: str, config: Optional[TranslationConfig] = None):
        """Initialize the translation client with the given base URL and config."""
        self.base_url = base_url.rstrip("/")
        self.config = config or TranslationConfig()
        self.session = None

    async def __aenter__(self):
        """
        Set up the HTTP session when entering the async context.

        Returns:
            self: The client instance for use in the async with block.
        """
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *err):
        """
        Clean up the HTTP session when exiting the async context.

        Ensures proper cleanup of network resources even if an error occurred.
        """
        if self.session:
            await self.session.close()

    async def start_translation(
        self, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
        """
        Start a new translation job.

        Initiates a new translation job for the specified language pair.
        Automatically generates a unique job ID for tracking.

        :param source_lang: Source language code (e.g., 'en')
        :param target_lang: Target language code (e.g., 'es')
        :returns: API response containing job details including job_id
        :raises: aiohttp.ClientError: On API communication failures
        """
        # Send an asynchronous HTTP POST request to the translation endpoint
        async with self.session.post(
            f"{self.base_url}/translate",
            json={
                "job_id": str(uuid4()),
                "source_language": source_lang,
                "target_language": target_lang,
            },
            timeout=10,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the current status of a translation job.

        :param job_id: The ID of the job to check
        :returns: API response containing current job status and details
        :raises: aiohttp.ClientError: On API communication failures
        """
        # Send an asynchronous HTTP GET request to retrieve the job status
        async with self.session.get(
            f"{self.base_url}/job/{job_id}", timeout=5
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        """
        Wait for a translation job to complete.

        Polls the job status with intelligent backoff until the job completes
        or fails. Uses progressive delay strategy if configured to reduce API load
        for longer-running jobs.

        :param job_id: The ID of the job to monitor
        :returns: Final job status and results when complete
        :raises:
            TimeoutError: If job doesn't complete within base_timeout
            TranslationError: If job fails or API communication fails

        The polling behavior is controlled by the TranslationConfig settings:
        - Starts with min_delay between checks
        - If status remains unchanged, progressively increases delay up to max_delay
        - Resets delay to min_delay when status changes
        - Gives up after base_timeout seconds
        """
        # Setup initial variables for tracking job status polling
        client_logger.info(f"Starting to wait for job {job_id} completion.")
        start_time = asyncio.get_event_loop().time()
        current_delay = self.config.min_delay
        last_status = None
        consecutive_unchanged = 0

        # Loop until the elapsed time exceeds the base timeout
        while asyncio.get_event_loop().time() - start_time < self.config.base_timeout:
            try:
                client_logger.debug(f"Checking status for job {job_id}...")

                status = await self.get_status(
                    job_id
                )  # Asynchronously get the status of the job

                client_logger.debug(f"Received status: {status}")

                # Check if the status has changed since the last check
                if status["status"] != last_status:
                    client_logger.info(f"Status changed: {status['status']}")
                    current_delay = (
                        self.config.min_delay
                    )  # Reset the delay to the minimum delay
                    consecutive_unchanged = (
                        0  # Reset the counter for consecutive unchanged statuses
                    )

                elif self.config.progressive_delay and consecutive_unchanged > 2:
                    # If progressive delay is enabled and the status has been unchanged for more than 2 checks
                    # Increase the delay, but do not exceed the maximum delay
                    current_delay = min(current_delay * 1.5, self.config.max_delay)
                    client_logger.debug(f"Increasing delay to {current_delay}")
                    # Increment the counter for consecutive unchanged statuses
                    consecutive_unchanged += 1
                # Update the last status to the current status
                last_status = status["status"]

                # Check if the job status is "completed" or "error"
                if status["status"] == "completed":
                    client_logger.info(f"Job {job_id} completed successfully.")
                    return status
                elif status["status"] == "error":
                    error_message = status.get("error_message", "Unknown error")
                    client_logger.error(f"Translation failed: {error_message}")
                    raise TranslationError(f"Translation failed: {error_message}")

                await asyncio.sleep(
                    current_delay
                )  # Wait for the current delay before checking the status again
            except aiohttp.ClientError as e:
                # If there is a client error, log the exception with traceback
                client_logger.exception(f"Error communicating with server: {e}")
                # Raise a TranslationError with the original exception
                raise TranslationError(f"Error communicating with server: {e}") from e
        client_logger.error(
            f"Job {job_id} did not complete within {self.config.base_timeout} seconds"
        )
        raise TimeoutError(
            f"Job {job_id} did not complete within {self.config.base_timeout} seconds"
        )

    async def cancel_translation(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running translation job.

        :param job_id: The ID of the job to cancel
        :returns: API response containing cancelled job status
        :raises:
            TranslationError: If cancellation fails
            aiohttp.ClientError: For HTTP-related errors
        """
        try:
            async with self.session.post(
                f"{self.base_url}/job/{job_id}/cancel", timeout=5
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise TranslationError(f"Failed to cancel job: {e}") from e
