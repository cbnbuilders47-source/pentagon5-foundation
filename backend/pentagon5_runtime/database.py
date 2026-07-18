"""Shared SQLAlchemy engine construction and database health checks."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine, text


def create_database_engine(database_url: str) -> Engine:
    """Create a bounded, pre-pinged PostgreSQL connection pool."""
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
    )


def database_is_ready(engine: Engine) -> bool:
    """Return whether a minimal database round trip succeeds."""
    try:
        with engine.connect() as connection:
            return bool(connection.execute(text("SELECT 1")).scalar_one() == 1)
    except Exception:
        return False
