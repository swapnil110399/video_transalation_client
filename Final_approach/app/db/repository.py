from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from .models import TranslationJobDB
from ..models.schemas import TranslationJob, JobStatus


class TranslationRepository:
    """
    Repository for managing translation job persistence operations.

    Provides an abstraction layer for database operations related to translation jobs
    using SQLAlchemy async sessions. Handles CRUD operations and status-based queries
    while maintaining consistent transaction boundaries.

    Example:
        async with db.get_session() as session:
            repo = TranslationRepository(session)
            job = await repo.create_job(translation_job)
            await repo.update_job_status(updated_job)

    Attributes:
        session: SQLAlchemy async session for database operations
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Active SQLAlchemy async session
        """
        self.session = session

    async def create_job(self, job: TranslationJob) -> TranslationJobDB:
        """
        Create a new translation job record in the database.

        Converts the domain model to a database model and persists it.
        Performs a flush to ensure the record is created but doesn't commit.

        Args:
            job: TranslationJob domain model instance

        Returns:
            Created TranslationJobDB database model instance

        Note:
            Caller is responsible for committing the transaction
        """
        db_job = TranslationJobDB(
            job_id=job.job_id,
            source_language=job.source_language,
            target_language=job.target_language,
            status=job.status,
            created_at=job.created_at,
            job_metadata=job.metadata,
        )
        self.session.add(db_job)
        await self.session.flush()
        return db_job

    async def update_job_status(
        self, job: TranslationJob
    ) -> Optional[TranslationJobDB]:
        """
        Update job status and related completion fields.

        Updates status, completion timestamp, and error message if applicable.
        Uses RETURNING clause to fetch the updated record.

        Args:
            job: TranslationJob with updated status

        Returns:
            Updated TranslationJobDB instance if found, None otherwise
        """
        stmt = (
            update(TranslationJobDB)
            .where(TranslationJobDB.job_id == job.job_id)
            .values(
                status=job.status,
                completed_at=job.completed_at,
                error_message=job.error_message,
            )
            .returning(TranslationJobDB)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_job(self, job_id: str) -> Optional[TranslationJobDB]:
        """
        Retrieve a single job by its ID.

        Args:
            job_id: Unique identifier of the job

        Returns:
            TranslationJobDB instance if found, None otherwise
        """
        stmt = select(TranslationJobDB).where(TranslationJobDB.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_jobs_by_status(self, status: JobStatus) -> List[TranslationJobDB]:
        """
        Retrieve all jobs with a specific status.

        Args:
            status: JobStatus enum value to filter by

        Returns:
            List of TranslationJobDB instances matching the status
        """
        stmt = select(TranslationJobDB).where(TranslationJobDB.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_jobs(self) -> List[TranslationJobDB]:
        """
        Retrieve all jobs with PENDING status.

        Returns:
            List of pending TranslationJobDB instances

        Note:
            Convenience method that wraps get_jobs_by_status(JobStatus.PENDING)
        """
        return await self.get_jobs_by_status(JobStatus.PENDING)
