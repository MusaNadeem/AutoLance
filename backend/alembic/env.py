import asyncio
from logging.config import fileConfig
import os
import sys

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add backend root to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging. This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models to ensure metadata is populated for autogenerate
from app.database import Base
from app.models.user import User
from app.models.client import Client
from app.models.job import Job
from app.models.profile import FreelancerProfile
from app.models import (
    CVDocument,
    MatchScore,
    CoverLetter,
    Proposal,
    AlertConfig,
    AlertEvent,
    ActivityLog,
    ScrapingRun,
)

target_metadata = Base.metadata

def get_url():
    from app.config import settings
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
