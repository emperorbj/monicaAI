"""Database connection: one SQLAlchemy engine for the whole app.

Other modules call get_engine() instead of creating their own, so the connection pool is shared.
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


def to_sqlalchemy_url(database_url: str) -> str:
    """Tell SQLAlchemy to use the psycopg (v3) driver.

    Neon gives URLs starting with "postgresql://". On its own, SQLAlchemy reads that as
    "use psycopg2" (the old driver, which we don't install), so we name the driver explicitly.
    """
    for prefix in ("postgresql://", "postgres://"):
        if database_url.startswith(prefix):
            return "postgresql+psycopg://" + database_url.removeprefix(prefix)
    return database_url  # already has a driver (e.g. postgresql+psycopg://) — leave it alone


@lru_cache
def get_engine() -> Engine:
    """Create the engine once and reuse it (it owns the connection pool)."""
    settings = get_settings()
    return create_engine(
        to_sqlalchemy_url(settings.database_url.get_secret_value()),
        # Neon suspends idle databases (scale-to-zero), which can silently close pooled
        # connections. pre_ping tests each connection before use and replaces dead ones.
        pool_pre_ping=True,
    )


def check_database_connection() -> str:
    """Run a trivial query and return the server's PostgreSQL version. Raises if unreachable."""
    with get_engine().connect() as connection:
        return connection.execute(text("SELECT version()")).scalar_one()


if __name__ == "__main__":
    # Lets us run `uv run python -m app.database` as a quick manual connection check.
    print("Connected to:", check_database_connection())
