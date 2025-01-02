import redis.asyncio as redis
import json
import logging
from typing import Optional, List
from datetime import datetime, UTC
from ..models.schemas import TranslationJob

logger = logging.getLogger(__name__)


class DLQManager:
    """
    Manages Dead Letter Queue (DLQ) operations using Redis.

    Provides functionality to track and manage failed or missed job notifications
    using Redis as a persistent store. Maintains both a set of DLQ job IDs and
    a hash of job results for recovery.

    Example:
        dlq = DLQManager("redis://localhost:6379/0")
        await dlq.add_to_dlq(job_id)
        result = await dlq.get_result(job_id)

    Attributes:
        redis: Redis client connection
        dlq_key: Redis key for the DLQ set ("translation:dlq")
        results_key: Redis key for job results hash ("translation:results")
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize DLQ manager with Redis connection.

        Args:
            redis_url: Redis connection URL (default: "redis://localhost:6379/0")
        """
        self.redis = redis.from_url(redis_url)
        self.dlq_key = "translation:dlq"
        self.results_key = "translation:results"

    async def add_to_dlq(self, job_id: str) -> None:
        """
        Add a job ID to the Dead Letter Queue set.

        Args:
            job_id: ID of the job to add to DLQ

        Raises:
            Exception: If Redis operation fails
        """
        try:
            await self.redis.sadd(self.dlq_key, job_id)
            logger.info(f"Added job {job_id} to DLQ")
        except Exception as e:
            logger.error(f"Error adding job {job_id} to DLQ: {e}")
            raise

    async def remove_from_dlq(self, job_id: str) -> None:
        """
        Remove a job ID from the Dead Letter Queue set.

        Args:
            job_id: ID of the job to remove from DLQ

        Raises:
            Exception: If Redis operation fails
        """
        try:
            await self.redis.srem(self.dlq_key, job_id)
            logger.info(f"Removed job {job_id} from DLQ")
        except Exception as e:
            logger.error(f"Error removing job {job_id} from DLQ: {e}")
            raise

    async def is_in_dlq(self, job_id: str) -> bool:
        """
        Check if a job ID exists in the Dead Letter Queue.

        Args:
            job_id: ID of the job to check

        Returns:
            True if job is in DLQ, False otherwise

        Raises:
            Exception: If Redis operation fails
        """
        try:
            return await self.redis.sismember(self.dlq_key, job_id)
        except Exception as e:
            logger.error(f"Error checking job {job_id} in DLQ: {e}")
            raise

    async def store_result(self, job: TranslationJob) -> None:
        """
        Store job result data in Redis hash.

        Serializes job status, completion time, and error details to JSON
        for persistent storage.

        Args:
            job: TranslationJob instance containing result data

        Raises:
            Exception: If Redis operation fails
        """
        try:
            result = {
                "job_id": job.job_id,
                "status": job.status,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "error_message": job.error_message,
            }
            await self.redis.hset(self.results_key, job.job_id, json.dumps(result))
            logger.info(f"Stored result for job {job.job_id}")
        except Exception as e:
            logger.error(f"Error storing result for job {job.job_id}: {e}")
            raise

    async def get_result(self, job_id: str) -> Optional[dict]:
        """
        Retrieve job result data from Redis hash.

        Args:
            job_id: ID of the job to retrieve

        Returns:
            Dict containing job result data if found, None otherwise

        Raises:
            Exception: If Redis operation fails
        """
        try:
            result = await self.redis.hget(self.results_key, job_id)
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            logger.error(f"Error getting result for job {job_id}: {e}")
            raise

    async def get_dlq_jobs(self) -> List[str]:
        """
        Get list of all job IDs currently in the DLQ.

        Returns:
            List of job ID strings from the DLQ set

        Raises:
            Exception: If Redis operation fails
        """
        try:
            return [job.decode() for job in await self.redis.smembers(self.dlq_key)]
        except Exception as e:
            logger.error(f"Error getting DLQ jobs: {e}")
            raise
