import redis.asyncio as redis
import json
import logging
from typing import Optional
from ..models.schemas import TranslationJob

logger = logging.getLogger(__name__)


class CacheManager:
    """A Redis cache manager for efficient translation job status retrieval.

    Provides caching operations to store and fetch translation job statuses using Redis as
    a caching layer. Implements automatic key expiration and error-safe operations to ensure
    caching issues don't impact core functionality.

    Example:
        cache = CacheManager("redis://localhost:6379/1")
        await cache.cache_job_status(job)
        status = await cache.get_cached_status(job_id)

    Attributes:
        redis: The Redis client connection instance
        cache_prefix: Prefix for Redis keys to namespace job entries ("job_status:")
        cache_ttl: Time-to-live for cached entries in seconds (3600)
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        """Initialize Redis cache manager.

        Args:
            redis_url: Redis connection URL (default: "redis://localhost:6379/1")
        """
        self.redis = redis.from_url(redis_url)
        self.cache_prefix = "job_status:"
        self.cache_ttl = 3600  # 1 hour

    async def cache_job_status(self, job: TranslationJob) -> None:
        """Store translation job status in Redis cache.

        Caches the serialized job data with automatic expiration after cache_ttl seconds.

        Args:
            job: TranslationJob instance to cache
        """
        key = f"{self.cache_prefix}{job.job_id}"
        try:
            await self.redis.setex(key, self.cache_ttl, job.model_dump_json())
        except Exception as e:
            logger.error(f"Error caching job status: {e}")

    async def get_cached_status(self, job_id: str) -> Optional[dict]:
        """Retrieve cached job status.

        Fetches and deserializes the cached job status data if available.

        Args:
            job_id: ID of the translation job

        Returns:
            Deserialized job status dict if found, None otherwise
        """
        key = f"{self.cache_prefix}{job_id}"
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting cached status: {e}")
            return None
