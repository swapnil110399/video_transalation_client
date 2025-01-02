import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """
    Custom exception for translation service errors.

    Raised when translation operations fail due to API errors,
    connection issues, or timeout conditions.
    """

    pass


class JobStatus(str, Enum):
    """
    Enum representing possible translation job states.

    Values:
        PENDING: Job is queued or in progress
        COMPLETED: Job finished successfully
        ERROR: Job failed with an error
    """

    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class TranslationClient:
    """
    Async client for interacting with the video translation service.

    Provides methods to start translation jobs and monitor their status
    via WebSocket connections. Handles connection lifecycle, retries,
    and heartbeat maintenance.

    Example:
        async with TranslationClient("http://api.example.com") as client:
            job = await client.start_translation("en", "es")
            result = await client.wait_for_completion(job["job_id"])

    Attributes:
        base_url: Base URL of the translation service
        max_retries: Maximum retry attempts for failed operations
        retry_delay: Delay between retries in seconds
        timeout: Operation timeout in seconds
        heartbeat_interval: WebSocket ping interval in seconds
    """

    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        heartbeat_interval: float = 5.0,
    ):
        """
        Initialize translation client.

        Args:
            base_url: Service base URL
            max_retries: Max retry attempts for operations
            retry_delay: Seconds between retries
            timeout: Operation timeout in seconds
            heartbeat_interval: WebSocket ping interval
        """
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """
        Context manager entry - initialize HTTP session.

        Returns:
            Initialized client instance
        """
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - cleanup HTTP session.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception instance if raised
            exc_tb: Exception traceback if raised
        """
        if self._session:
            await self._session.close()

    async def start_translation(
        self,
        source_language: str,
        target_language: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Start a new translation job.

        Args:
            source_language: Source language code
            target_language: Target language code
            metadata: Optional job metadata

        Returns:
            API response containing job ID and status

        Raises:
            TranslationError: If request fails or session not initialized
        """
        if not self._session:
            raise TranslationError("Client session not initialized")

        try:
            async with self._session.post(
                f"{self.base_url}/translate",
                json={
                    "source_language": source_language,
                    "target_language": target_language,
                    "metadata": metadata or {},
                },
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            raise TranslationError(f"Failed to start translation: {e}")

    async def _send_heartbeat(self, ws: aiohttp.ClientWebSocketResponse):
        """
        Send periodic ping messages to keep WebSocket alive.

        Args:
            ws: Active WebSocket connection

        Note:
            Runs until connection closes or error occurs
        """
        try:
            while True:
                await ws.ping()
                await asyncio.sleep(self.heartbeat_interval)
        except Exception:
            pass

    async def wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        """
        Wait for job completion via WebSocket connection.

        Establishes WebSocket connection to monitor job status with:
        - Automatic reconnection on failures
        - Connection heartbeat maintenance
        - Status processing and error handling

        Args:
            job_id: ID of job to monitor

        Returns:
            Final job status data if successful

        Raises:
            TranslationError: On connection failure, timeout, or job error
        """
        if not self._session:
            raise TranslationError("Client session not initialized")

        ws_url = f"ws://{self.base_url.split('://')[-1]}/ws/job/{job_id}"
        retries = 0

        while retries < self.max_retries:
            try:
                async with self._session.ws_connect(ws_url) as ws:
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._send_heartbeat(ws))

                    try:
                        async with asyncio.timeout(self.timeout):
                            async for msg in ws:
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    data = msg.json()
                                    status = data.get("status")

                                    if status == JobStatus.COMPLETED:
                                        logger.info(
                                            f"Job {job_id} completed successfully"
                                        )
                                        return data
                                    elif status == JobStatus.ERROR:
                                        error_msg = data.get(
                                            "error_message", "Unknown error"
                                        )
                                        raise TranslationError(
                                            f"Translation failed: {error_msg}"
                                        )

                                elif msg.type in (
                                    aiohttp.WSMsgType.CLOSED,
                                    aiohttp.WSMsgType.ERROR,
                                ):
                                    raise TranslationError(
                                        f"WebSocket error: Connection closed"
                                    )

                    except asyncio.TimeoutError:
                        logger.warning(
                            f"Connection timeout for job {job_id}, retrying..."
                        )
                    finally:
                        heartbeat_task.cancel()
                        try:
                            await heartbeat_task
                        except asyncio.CancelledError:
                            pass

            except Exception as e:
                logger.error(f"Error while waiting for job {job_id}: {e}")

            retries += 1
            if retries < self.max_retries:
                await asyncio.sleep(self.retry_delay)

        raise TranslationError(
            f"Failed to get job result after {self.max_retries} retries"
        )
