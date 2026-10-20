"""Tests for app.config.

Each test passes _env_file=None so it never reads your real .env file:
tests must give the same result on every machine.
"""

import pytest
from pydantic import ValidationError

from app.config import Settings

FAKE_DATABASE_URL = "postgresql://demo_user:demo_password@example.neon.tech/demo_db"


def test_settings_load_from_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    # monkeypatch sets env vars for this test only and undoes them afterwards.
    monkeypatch.setenv("DATABASE_URL", FAKE_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "test")

    settings = Settings(_env_file=None)

    assert settings.app_env == "test"
    assert settings.database_url.get_secret_value() == FAKE_DATABASE_URL


def test_missing_database_url_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


def test_invalid_app_env_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", FAKE_DATABASE_URL)
    monkeypatch.setenv("APP_ENV", "staging")  # not one of the allowed values

    with pytest.raises(ValidationError, match="app_env"):
        Settings(_env_file=None)


def test_migrations_prefer_the_direct_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    # Different host from FAKE_DATABASE_URL, so the test can tell which one was chosen.
    direct_url = "postgresql://demo_user:demo_password@direct.example.neon.tech/demo_db"
    monkeypatch.setenv("DATABASE_URL", FAKE_DATABASE_URL)
    monkeypatch.setenv("DATABASE_URL_UNPOOLED", direct_url)

    assert Settings(_env_file=None).migration_database_url == direct_url


def test_migrations_fall_back_to_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", FAKE_DATABASE_URL)
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)

    assert Settings(_env_file=None).migration_database_url == FAKE_DATABASE_URL


def test_database_password_is_hidden_when_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", FAKE_DATABASE_URL)

    settings = Settings(_env_file=None)

    # If someone logs the settings object, the password must not appear.
    assert "demo_password" not in repr(settings)
    assert "demo_password" not in str(settings.database_url)
