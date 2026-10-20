"""Shared pytest fixtures. pytest loads this file automatically.

db_session gives each test a database session inside a transaction that is ALWAYS rolled
back afterwards, so tests can insert freely against the real (migrated) Neon database
without leaving any data behind.
"""

from collections.abc import Iterator
from functools import cache

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.config import get_settings


@cache  # the answer can't change during one test run, so ask the database only once
def _skip_reason() -> str | None:
    """Why database tests can't run here, or None if they can."""
    try:
        get_settings()
    except ValidationError:
        return "DATABASE_URL not configured"

    from app.database import get_engine

    if not inspect(get_engine()).has_table("alembic_version"):
        return "database not migrated: run `uv run alembic upgrade head`"
    return None


@pytest.fixture
def db_session() -> Iterator[Session]:
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)

    from app.database import get_engine

    connection = get_engine().connect()
    outer_transaction = connection.begin()
    # create_savepoint: anything the test does (even session.commit()) stays inside
    # our outer transaction, which we roll back below.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session  # the test runs here
    finally:
        session.close()
        outer_transaction.rollback()  # erase everything the test did
        connection.close()
