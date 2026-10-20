"""Tests for app.database.

The URL tests are pure functions: no network needed.
The connection test talks to the real NeonDB, so it is marked "integration" and is skipped
automatically when no DATABASE_URL is configured (for example on a fresh clone).
"""

import pytest
from pydantic import ValidationError

from app.config import get_settings
from app.database import check_database_connection, to_sqlalchemy_url


@pytest.mark.parametrize(
    ("neon_url", "expected"),
    [
        (
            "postgresql://u:p@host/db?sslmode=require",
            "postgresql+psycopg://u:p@host/db?sslmode=require",
        ),
        ("postgres://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
        ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ],
)
def test_to_sqlalchemy_url_selects_psycopg_driver(neon_url: str, expected: str) -> None:
    assert to_sqlalchemy_url(neon_url) == expected


def _database_configured() -> bool:
    try:
        get_settings()
        return True
    except ValidationError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not _database_configured(), reason="DATABASE_URL not configured")
def test_can_connect_to_neon() -> None:
    version = check_database_connection()

    assert version.startswith("PostgreSQL")
