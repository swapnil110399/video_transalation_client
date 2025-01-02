from sqlalchemy import Column, String, DateTime, Enum as SQLAEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, UTC
from ..models.schemas import JobStatus

Base = declarative_base()


class TranslationJobDB(Base):
    """
    SQLAlchemy model representing a translation job in the database.

    Maps translation job attributes to database columns including job identifiers,
    language pairs, status tracking, timestamps, and additional metadata. Uses
    timezone-aware timestamps and JSON storage for flexible metadata.

    Example:
        job = TranslationJobDB(
            job_id="123",
            source_language="en",
            target_language="es",
            status=JobStatus.PENDING
        )

    Attributes:
        job_id: Unique identifier for the translation job (primary key)
        source_language: Source language code of the content
        target_language: Target language code for translation
        status: Current job status (from JobStatus enum)
        created_at: UTC timestamp of job creation
        completed_at: UTC timestamp of job completion (null if not completed)
        error_message: Error details if job failed (null if successful)
        job_metadata: Additional job-related data stored as JSON

    Table: translation_jobs
    """

    __tablename__ = "translation_jobs"

    job_id = Column(String, primary_key=True)
    source_language = Column(String, nullable=False)
    target_language = Column(String, nullable=False)
    status = Column(
        SQLAEnum(JobStatus), nullable=False, doc="Current status of the translation job"
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        doc="Timestamp when job was created (UTC)",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when job finished processing (UTC)",
    )
    error_message = Column(String, nullable=True, doc="Error details if job failed")
    job_metadata = Column(
        JSON, default=dict, doc="Additional job-related data stored as JSON"
    )
