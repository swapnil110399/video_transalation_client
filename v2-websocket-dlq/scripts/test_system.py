import os
import sys
from pathlib import Path
import asyncio
import aiohttp
import logging
from datetime import datetime, UTC
import json

"""
End-to-end system test suite for the Translation Service.

Tests the complete system functionality including:
- HTTP API endpoints
- WebSocket connections
- Database operations
- Cache operations
- Dead Letter Queue
- Metrics collection

Requires all system components to be running:
- FastAPI application
- PostgreSQL database
- Redis server
"""

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app.models.schemas import TranslationJob, JobStatus
from app.db.database import DatabaseManager
from app.db.repository import TranslationRepository
from app.core.dlq_manager import DLQManager
from app.core.cache_manager import CacheManager


class SystemTester:
    """
    Comprehensive system test suite for the Translation Service.

    Provides methods to test all major system components and their interactions:
    - REST API endpoints
    - WebSocket connections and updates
    - Database operations and persistence
    - Redis caching layer
    - Dead Letter Queue operations
    - Prometheus metrics

    Attributes:
        base_url: Base URL for HTTP endpoints
        ws_url: Base URL for WebSocket connections
        db: Database manager instance
        dlq: Dead Letter Queue manager
        cache: Cache manager instance
    """

    def __init__(self):
        """Initialize test suite with service endpoints and component managers"""
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000"
        self.db = DatabaseManager(
            "postgresql+asyncpg://postgres:postgres@localhost/translation_db"
        )
        self.dlq = DLQManager()
        self.cache = CacheManager()

    async def test_create_job(self):
        """
        Test job creation via HTTP API.

        Returns:
            str: Created job ID if successful

        Raises:
            AssertionError: If job creation fails
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "source_language": "en",
                "target_language": "es",
                "metadata": {"test": "system test"},
            }
            async with session.post(
                f"{self.base_url}/translate", json=data
            ) as response:
                assert response.status == 200
                result = await response.json()
                logger.info(f"Created job: {result}")
                return result["job_id"]

    async def test_websocket_connection(self, job_id):
        """
        Test WebSocket connection and status updates.

        Monitors job status updates via WebSocket until completion
        or timeout (10 seconds).

        Args:
            job_id: ID of job to monitor

        Returns:
            dict: Final job status data if completed
            None: If timeout occurs
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"{self.ws_url}/ws/job/{job_id}") as ws:
                logger.info("WebSocket connected")

                try:
                    async with asyncio.timeout(10):
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                logger.info(f"Received status update: {data}")
                                if data["status"] in ["completed", "error"]:
                                    return data
                            elif msg.type in [
                                aiohttp.WSMsgType.CLOSED,
                                aiohttp.WSMsgType.ERROR,
                            ]:
                                break
                except asyncio.TimeoutError:
                    logger.warning(
                        "WebSocket timeout - job taking longer than expected"
                    )
                    return None

    async def test_database(self, job_id):
        """
        Test database record persistence.

        Args:
            job_id: ID of job to retrieve

        Returns:
            TranslationJobDB: Job database record if found
            None: If job not found
        """
        async with self.db.get_session() as session:
            repo = TranslationRepository(session)
            job = await repo.get_job(job_id)
            logger.info(f"Database record: {job.status if job else 'Not found'}")
            return job

    async def test_dlq(self, job_id):
        """
        Test DLQ membership and result storage.

        Args:
            job_id: ID of job to check

        Returns:
            tuple: (is_in_dlq: bool, result: dict)
        """
        in_dlq = await self.dlq.is_in_dlq(job_id)
        result = await self.dlq.get_result(job_id)
        logger.info(f"DLQ status - In queue: {in_dlq}, Result: {result}")
        return in_dlq, result

    async def test_cache(self, job_id):
        """
        Test cache storage and retrieval.

        Args:
            job_id: ID of job to check

        Returns:
            dict: Cached job data if found
            None: If not in cache
        """
        cached_status = await self.cache.get_cached_status(job_id)
        logger.info(f"Cache status: {cached_status}")
        return cached_status

    async def run_tests(self):
        """
        Execute complete system test suite.

        Tests all major components in sequence:
        1. Job creation via API
        2. WebSocket status monitoring
        3. Database persistence
        4. DLQ operations
        5. Cache operations
        6. Metrics endpoint

        Raises:
            Exception: If any test fails
        """
        try:
            logger.info("Starting system tests...")

            # Run test sequence
            job_id = await self.test_create_job()
            assert job_id, "Job creation failed"

            ws_result = await self.test_websocket_connection(job_id)
            assert ws_result, "WebSocket communication failed"

            db_result = await self.test_database(job_id)
            assert db_result, "Database operation failed"

            await self.test_dlq(job_id)
            await self.test_cache(job_id)

            # Check metrics endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    assert response.status == 200
                    metrics = await response.text()
                    logger.info(f"Metrics available: {'translation' in metrics}")

            logger.info("\nAll system tests completed successfully!")

        except Exception as e:
            logger.error(f"Error during system test: {e}")
            raise


async def main():
    """Script entry point - runs full test suite"""
    tester = SystemTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
