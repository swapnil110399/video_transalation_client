import os
import sys
from pathlib import Path

"""
Database operations test script for the translation service.

This script tests the core database functionality of the translation service including:
- Database connection management
- CRUD operations for translation jobs
- Status updates and retrievals
- Query operations

The script sets up the Python path to allow imports from the main application,
creates test data, and exercises the database operations through the repository layer.
"""

# Setup project imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
print(f"Adding to path: {project_root}")
sys.path.insert(0, str(project_root))

# Application imports
import asyncio
from datetime import datetime, UTC
from app.models.schemas import TranslationJob, JobStatus
from app.db.database import DatabaseManager
from app.db.repository import TranslationRepository


async def test_db_operations():
    """
    Execute a series of database operations to verify functionality.

    Tests the following operations:
    1. Database connection and session management
    2. Job creation and persistence
    3. Job retrieval by ID
    4. Status updates
    5. Query by status

    The test uses a real database connection and performs actual database
    operations. Make sure the database is available before running.

    Raises:
        Exception: If any database operation fails
    """
    try:
        # Initialize database connection
        db = DatabaseManager(
            "postgresql+asyncpg://postgres:postgres@localhost/translation_db"
        )
        print("Database manager initialized")

        # Create test job instance
        test_job = TranslationJob(
            job_id="test-123",
            source_language="en",
            target_language="es",
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
            metadata={"test": "data"},
        )
        print(f"Created test job object: {test_job}")

        # Execute database operations within a session
        async with db.get_session() as session:
            print("Database session created")
            repo = TranslationRepository(session)

            # Test job creation
            db_job = await repo.create_job(test_job)
            print(f"\nCreated job in database: {db_job.job_id}")

            # Test job retrieval
            retrieved_job = await repo.get_job("test-123")
            print(f"Retrieved job status: {retrieved_job.status}")

            # Test status update
            test_job.status = JobStatus.COMPLETED
            test_job.completed_at = datetime.now(UTC)
            updated_job = await repo.update_job_status(test_job)
            print(f"Updated job status: {updated_job.status}")

            # Test status-based query
            completed_jobs = await repo.get_jobs_by_status(JobStatus.COMPLETED)
            print(f"Number of completed jobs: {len(completed_jobs)}")

        print("\nTest successful!")

    except Exception as e:
        print(f"Error during test: {e}")
        raise


if __name__ == "__main__":
    """
    Script entry point.

    Executes the test_db_operations function in an async context.
    This ensures proper handling of async/await operations throughout
    the test sequence.
    """
    # Run the async test function
    asyncio.run(test_db_operations())
