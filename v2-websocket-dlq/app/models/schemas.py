from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, UTC
import json


class JobStatus(str, Enum):
    """
    Enum representing possible states of a translation job.

    Values:
        PENDING: Job is queued or in progress
        COMPLETED: Job finished successfully
        ERROR: Job failed with an error
    """

    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


def datetime_handler(dt):
    """
    JSON serialization handler for datetime objects.

    Args:
        dt: DateTime object to serialize

    Returns:
        ISO format string representation

    Raises:
        TypeError: If object is not a datetime
    """
    if isinstance(dt, datetime):
        return dt.isoformat()
    raise TypeError(f"Object of type {type(dt)} is not JSON serializable")


class TranslationJob(BaseModel):
    """
    Pydantic model representing a video translation job.

    Tracks the complete lifecycle of a translation job including status,
    timestamps, and metadata. Provides custom JSON serialization for
    datetime fields.

    Example:
        job = TranslationJob(
            job_id="123",
            source_language="en",
            target_language="es",
            metadata={"duration": 120}
        )

    Attributes:
        job_id: Unique identifier for the job
        source_language: Original language code
        target_language: Target language code for translation
        status: Current job status (defaults to PENDING)
        created_at: UTC timestamp of creation
        completed_at: UTC timestamp of completion (if finished)
        error_message: Error details if failed
        metadata: Additional job-related data
    """

    job_id: str
    source_language: str
    target_language: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_encoders={datetime: datetime_handler})

    def model_dump_json(self, **kwargs):
        """
        Serialize model to JSON string with datetime handling.

        Returns:
            JSON string representation of the model
        """
        return json.dumps(self.model_dump(), default=datetime_handler)


class TranslationRequest(BaseModel):
    """
    Pydantic model for incoming translation requests.

    Represents the initial request to create a translation job
    with required language pair and optional metadata.

    Attributes:
        source_language: Original language code
        target_language: Target language code
        metadata: Optional additional request data
    """

    source_language: str
    target_language: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TranslationResponse(BaseModel):
    """
    Pydantic model for translation job responses.

    Used to provide job status updates to clients including
    success/error messages and current status.

    Attributes:
        job_id: Identifier of the translation job
        status: Current job status
        message: Optional status or error message
    """

    job_id: str
    status: JobStatus
    message: Optional[str] = None
