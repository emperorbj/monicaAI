"""Application settings, loaded from environment variables and the project-root .env file.

Every other module gets settings by calling get_settings(); nothing reads os.environ directly.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives in monicaAI/backend/app/, so parents[2] is the project root (monicaAI/).
# Using an absolute path means the .env file is found no matter which folder we run from.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All configuration the backend needs. Field names match env var names (case-insensitive)."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # The shared .env will also hold settings for later modules (Telegram, LangSmith, Next.js).
        # Ignore ones this class doesn't declare yet instead of failing.
        extra="ignore",
    )

    # Which environment we are running in. Literal means only these three values are accepted.
    app_env: Literal["development", "test", "production"] = "development"

    # NeonDB connection string. No default: the app must refuse to start without it.
    # SecretStr hides the value (which contains the password) when printed or logged.
    database_url: SecretStr


@lru_cache
def get_settings() -> Settings:
    """Return the settings, reading the environment only once and reusing the result."""
    return Settings()
