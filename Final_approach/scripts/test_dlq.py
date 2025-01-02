import os
import sys
from pathlib import Path

"""
Dead Letter Queue (DLQ) operations test script.

Tests the functionality of the DLQ management system including:
- Job result storage and retrieval in Redis
- DLQ membership operations
- Bulk DLQ operations and queries
"""

# Setup project imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
print(f"Adding to path: {project_root}")
sys.path.insert(0, str(project_root))

import asyncio
from datetime import datetime, UTC
from app.models.schemas import TranslationJob, JobStatus
from app.core.dlq_manager import DLQManager


async def test_dlq_operations():
    """
    Test suite for DLQ manager functionality.

    Executes a series of tests to verify DLQ operations:
    1. Result storage and retrieval
    2. DLQ membership management
    3. Bulk DLQ queries
    4. Cleanup operations

    The test requires a running Redis instance and performs actual
    Redis operations. Ensure Redis is available before running.

    Raises:
        Exception: If any DLQ operation fails or Redis is unavailable
    """
    try:
        # Initialize DLQ manager with Redis connection
        dlq = DLQManager()

        # Create test translation job
        test_job = TranslationJob(
            job_id="test-dlq-123",
            source_language="en",
            target_language="es",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            metadata={"test": "data"},
        )
        print(f"Created test job: {test_job}")

        # Test result storage and DLQ addition
        await dlq.store_result(test_job)
        await dlq.add_to_dlq(test_job.job_id)
        print("Added job to DLQ")

        # Test DLQ membership check
        in_dlq = await dlq.is_in_dlq(test_job.job_id)
        print(f"Job in DLQ: {in_dlq}")

        # Test result retrieval
        result = await dlq.get_result(test_job.job_id)
        print(f"Retrieved result: {result}")

        # Test bulk DLQ operations
        dlq_jobs = await dlq.get_dlq_jobs()
        print(f"All DLQ jobs: {dlq_jobs}")

        # Test cleanup operations
        await dlq.remove_from_dlq(test_job.job_id)
        print("Removed job from DLQ")

        print("\nTest successful!")

    except Exception as e:
        print(f"Error during test: {e}")
        raise


if __name__ == "__main__":
    """
    Script entry point.

    Executes the DLQ test suite in an async context. Handles proper
    initialization and execution of async test operations.

    Note:
        Requires Redis to be running and accessible at default
        connection settings (localhost:6379).
    """
    # Run the async test function
    asyncio.run(test_dlq_operations())
