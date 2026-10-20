"""Dependencies: things endpoints ask FastAPI to provide (dependency injection).

An endpoint writes `session: DbSession` in its parameters, and FastAPI calls get_session()
to create the session before the endpoint runs, then finishes the generator afterwards
(closing the session). Tests replace get_session with a rolled-back session via
app.dependency_overrides, without changing any endpoint code.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_engine


def get_session() -> Iterator[Session]:
    """One database session per request, always closed when the request ends.

    Endpoints that change data call session.commit() themselves. Anything not committed
    is discarded when the session closes, so a failed request never half-saves.
    """
    with Session(get_engine()) as session:
        yield session  # the endpoint runs here


# "A Session, provided by get_session". Using this alias keeps endpoint signatures short.
DbSession = Annotated[Session, Depends(get_session)]
