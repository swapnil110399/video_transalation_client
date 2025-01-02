from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import logging
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages asynchronous database connections and session lifecycles.

    Provides a centralized way to handle SQLAlchemy async database operations including
    connection pooling, session management, and schema initialization. Implements context
    managers for safe session handling with automatic commit/rollback.

    Example:
        db = DatabaseManager("postgresql+asyncpg://user:pass@localhost/dbname")
        await db.init_db()

        async with db.get_session() as session:
            # Perform database operations
            result = await session.execute(query)

    Attributes:
        engine: SQLAlchemy async engine instance
        async_session: Session factory for creating new sessions
    """

    def __init__(self, database_url: str):
        """
        Initialize database manager with connection settings.

        Args:
            database_url: SQLAlchemy connection URL for the database

        Connection pool is configured with:
        - pool_size: 5 concurrent connections
        - max_overflow: 10 additional connections when pool is full
        """
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL logging
            pool_size=5,
            max_overflow=10,
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """
        Initialize database schemas and tables.

        Creates all tables defined in SQLAlchemy models if they don't exist.
        Safe to call multiple times as SQLAlchemy handles "CREATE IF NOT EXISTS".

        Raises:
            Exception: If database connection or schema creation fails
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def get_session(self):
        """
        Context manager for database session handling.

        Provides transaction management with automatic commit on success and
        rollback on exceptions. Session is always closed after use.

        Yields:
            AsyncSession: SQLAlchemy async session instance

        Raises:
            Exception: If database operations fail, session is rolled back

        Example:
            async with db.get_session() as session:
                await session.execute(query)
        """
        session = self.async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()

    async def close(self):
        """
        Close database connection pool.

        Cleanly shuts down the connection pool and releases all resources.
        Should be called when the application shuts down.
        """
        await self.engine.dispose()
