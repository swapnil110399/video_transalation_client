import pytest
import threading
import time
import uvicorn
from server.app import app
from client.client import VideoTranslationClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def server_fixture():
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000)
    )
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)
    yield


@pytest.mark.asyncio
async def test_translation_flow(server_fixture):
    """Simple integration test demonstrating the translation service"""
    logger.info("Starting translation test")

    async with VideoTranslationClient("http://localhost:8000") as client:
        # Start a translation job
        logger.info("Starting a translation job")
        response = await client.start_translation("en", "es")
        job_id = response["job_id"]
        logger.info(f"Created job with ID: {job_id}")

        # Wait for completion
        try:
            result = await client.wait_for_completion(job_id)
            logger.info(f"Job completed with status: {result['status']}")
        except Exception as e:
            logger.info(f"Job failed with error: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
