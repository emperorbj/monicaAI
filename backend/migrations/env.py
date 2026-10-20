"""Alembic environment: tells Alembic which database to use and which models to compare against.

Alembic runs this file for every command (revision, upgrade, downgrade, ...).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import get_settings
from app.database import to_sqlalchemy_url

# Importing the package (not just Base) registers all nine tables on Base.metadata.
from app.models import Base

config = context.config

# Use the logging settings from alembic.ini (shows "Running upgrade ..." lines).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The "desired" schema: autogenerate compares this with the real database.
target_metadata = Base.metadata

# Direct (non-pooled) Neon URL, read from .env — never from alembic.ini.
DATABASE_URL = to_sqlalchemy_url(get_settings().migration_database_url)

# Shared options for both modes. compare_server_default lets autogenerate notice
# changed DEFAULTs (e.g. if we change a status default from 'unknown').
CONFIGURE_OPTIONS = {"target_metadata": target_metadata, "compare_server_default": True}


def run_migrations_offline() -> None:
    """'Offline' mode: print the SQL instead of running it (`alembic upgrade head --sql`).

    Useful for reviewing exactly what a migration will do before touching the database.
    """
    context.configure(
        url=DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **CONFIGURE_OPTIONS,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """'Online' mode: connect to the database and apply the migrations."""
    # NullPool: open one connection, use it, close it. A migration run is a one-off command,
    # so there is nothing to gain from keeping a pool of connections around.
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(connection=connection, **CONFIGURE_OPTIONS)
        # PostgreSQL can run schema changes inside a transaction, so a failed migration
        # rolls back completely instead of leaving half-created tables behind.
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
