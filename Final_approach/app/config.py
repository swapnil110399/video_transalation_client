from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application configuration settings with environment variable support.

    Manages centralized configuration for the translation service including
    database connections, job processing parameters, and WebSocket settings.
    Values can be overridden via environment variables or .env file.

    Example:
        Override in .env file:
        DATABASE_URL=postgresql+asyncpg://user:pass@host/db
        ERROR_RATE=0.1

        Override with environment variables:
        export DATABASE_URL=postgresql+asyncpg://user:pass@host/db

    Attributes:
        DATABASE_URL: SQLAlchemy connection string for PostgreSQL
        MIN_PROCESSING_TIME: Minimum job processing duration in seconds
        MAX_PROCESSING_TIME: Maximum job processing duration in seconds
        ERROR_RATE: Probability of simulated job failures (0.0 to 1.0)
        WS_HEARTBEAT_INTERVAL: WebSocket ping interval in seconds
    """

    # Database connection string
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/translation_db"
    )

    # Job processing simulation parameters
    MIN_PROCESSING_TIME: float = 1.0  # Minimum processing time in seconds
    MAX_PROCESSING_TIME: float = 3.0  # Maximum processing time in seconds
    ERROR_RATE: float = 0.2  # Probability of job failure

    # WebSocket configuration
    WS_HEARTBEAT_INTERVAL: float = 5.0  # Ping interval in seconds

    class Config:
        """Pydantic settings configuration"""

        env_file = ".env"  # Load settings from .env file


@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache application settings.

    Returns cached Settings instance to avoid repeatedly parsing
    environment variables or .env file.

    Returns:
        Cached Settings instance

    Note:
        Uses functools.lru_cache to maintain single instance
    """
    return Settings()
