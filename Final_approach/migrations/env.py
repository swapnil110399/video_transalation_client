import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import your models
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.db.models import Base

"""
Alembic migrations configuration and execution script.

This module configures and runs database migrations using Alembic with support for
both synchronous and asynchronous execution modes. It handles configuration loading,
logging setup, and migration execution for both online and offline scenarios.

Key components:
- Configuration loading from alembic.ini
- Logging setup via fileConfig
- Model metadata registration for autogeneration
- Migration execution in both online and offline modes
- Async support for modern database operations
"""

# Initialize Alembic config object
config = context.config

# Setup Python logging if config file exists
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Register model metadata for migration autogeneration
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Execute migrations in 'offline' mode.

    Configures migrations to run without requiring a live database connection.
    Instead, generates SQL commands that would perform the migrations. Useful
    for generating migration scripts that can be run manually.

    This mode:
    - Requires only a database URL
    - Doesn't need a DBAPI
    - Outputs migration SQL to script
    - Uses named parameter style
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Execute migrations using provided database connection.

    Core migration execution function that runs within a transaction.
    Used by both sync and async execution paths.

    Args:
        connection: SQLAlchemy database connection
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Execute migrations asynchronously.

    Creates an async engine and manages connection lifecycle for running
    migrations in async context. Uses NullPool to prevent connection pooling
    during migrations.

    Implementation:
    1. Creates async engine from config
    2. Establishes connection
    3. Runs migrations synchronously within async context
    4. Properly disposes engine
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Execute migrations in 'online' mode.

    Main entry point for running migrations with a live database connection.
    Delegates to async implementation using asyncio.run().

    This is the preferred way to run migrations in most scenarios.
    """
    asyncio.run(run_async_migrations())


# Determine execution mode and run appropriate migration function
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
