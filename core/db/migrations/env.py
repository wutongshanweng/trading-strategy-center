"""Alembic environment configuration — async support for PostgreSQL + SQLite fallback."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from core.db.models import Base

# Alembic Config object
config = context.config

# Set up logging (gracefully handle missing config file)
try:
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)
except (KeyError, FileNotFoundError):
    pass  # alembic.ini may not have logger sections in dev mode

# Target metadata for autogenerate
target_metadata = Base.metadata


def _get_async_url() -> str:
    """
    获取异步 DB URL。
    优先顺序: 1) 环境变量 SQLALCHEMY_URL  2) alembic.ini 配置
    """
    env_url = os.environ.get("SQLALCHEMY_URL")
    if env_url:
        return env_url
    return config.get_main_option("sqlalchemy.url", "")


def _get_sync_url() -> str:
    """Derive a sync DB URL from the async URL."""
    async_url = _get_async_url()
    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("+asyncpg", "")
    if async_url.startswith("sqlite+aiosqlite://"):
        return async_url.replace("+aiosqlite", "")
    return async_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    async_url = _get_async_url()
    connectable = create_async_engine(async_url, poolclass=pool.NullPool)

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
