import asyncio
import aiohttp
import time
from uuid import uuid4
from typing import Dict, Any, Optional
import logging

client_logger = logging.getLogger(__name__)  # Get a logger for this module
client_logger.setLevel(logging.INFO)  # Set the logging level
handler = logging.StreamHandler()  # Output to console
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
client_logger.addHandler(handler)


class TranslationConfig:
    def __init__(
        self, base_timeout=30, min_delay=0.5, max_delay=3.0, progressive_delay=True
    ):
        self.base_timeout = base_timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.progressive_delay = progressive_delay


class TranslationError(Exception):
    """Custom exception for translation service errors."""

    pass


class VideoTranslationClient:
    def __init__(self, base_url: str, config: Optional[TranslationConfig] = None):
        self.base_url = base_url.rstrip("/")
        self.config = config or TranslationConfig()
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *err):
        if self.session:
            await self.session.close()

    async def start_translation(
        self, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
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
        async with self.session.get(
            f"{self.base_url}/job/{job_id}", timeout=5
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def wait_for_completion(self, job_id: str) -> Dict[str, Any]:
        client_logger.info(
            f"Starting to wait for job {job_id} completion."
        )  # added logging
        start_time = asyncio.get_event_loop().time()
        current_delay = self.config.min_delay
        last_status = None
        consecutive_unchanged = 0

        while asyncio.get_event_loop().time() - start_time < self.config.base_timeout:
            try:
                client_logger.debug(
                    f"Checking status for job {job_id}..."
                )  # added logging
                status = await self.get_status(job_id)
                client_logger.debug(f"Received status: {status}")  # added logging
                if status["status"] != last_status:
                    client_logger.info(f"Status changed: {status['status']}")
                    current_delay = self.config.min_delay
                    consecutive_unchanged = 0
                elif self.config.progressive_delay and consecutive_unchanged > 2:
                    current_delay = min(current_delay * 1.5, self.config.max_delay)
                    client_logger.debug(
                        f"Increasing delay to {current_delay}"
                    )  # added logging
                    consecutive_unchanged += 1
                last_status = status["status"]

                if status["status"] == "completed":
                    client_logger.info(
                        f"Job {job_id} completed successfully."
                    )  # added logging
                    return status
                elif status["status"] == "error":
                    error_message = status.get("error_message", "Unknown error")
                    client_logger.error(
                        f"Translation failed: {error_message}"
                    )  # added logging
                    raise TranslationError(f"Translation failed: {error_message}")
                await asyncio.sleep(current_delay)
            except aiohttp.ClientError as e:
                client_logger.exception(
                    f"Error communicating with server: {e}"
                )  # log exception with traceback
                raise TranslationError(f"Error communicating with server: {e}") from e
        client_logger.error(
            f"Job {job_id} did not complete within {self.config.base_timeout} seconds"
        )  # added logging
        raise TimeoutError(
            f"Job {job_id} did not complete within {self.config.base_timeout} seconds"
        )
