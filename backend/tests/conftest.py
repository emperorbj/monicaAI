"""Shared pytest fixtures. pytest loads this file automatically.

Every database fixture runs inside a transaction that is ALWAYS rolled back afterwards,
so tests can insert freely against the real (migrated) Neon database without leaving
any data behind.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import cache

import pytest
from fastapi.testclient import TestClient
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


@contextmanager
def _rolled_back_session() -> Iterator[Session]:
    """A session whose every change is erased when the `with` block ends."""
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
        yield session
    finally:
        session.close()
        outer_transaction.rollback()  # erase everything the test did
        connection.close()


@pytest.fixture
def db_session() -> Iterator[Session]:
    """A fresh rolled-back session for ONE test. Use for tests that write data."""
    with _rolled_back_session() as session:
        yield session


@pytest.fixture
def api_client(db_session: Session) -> Iterator[TestClient]:
    """Calls the real app in memory, with every request using the rolled-back db_session.

    dependency_overrides swaps get_session for our test session: endpoints don't change,
    but nothing they write survives the test.
    """
    from app.api.deps import get_session
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    # raise_server_exceptions=False: return the 500 response like a real server would,
    # instead of re-raising the error inside the test.
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(scope="module")
def seeded_session() -> Iterator[Session]:
    """ONE session per test file with the demo data seeded (seeding takes ~1 minute).

    Shared by all tests in the file, so those tests must only READ. A test that changes
    data should use db_session instead.
    """
    from seed.seed_demo import run_seed

    with _rolled_back_session() as session:
        run_seed(session)
        yield session
