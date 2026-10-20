"""GET /health: is the app running, and can it reach the database?"""

import logging
from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


@router.get("/health")
def health(session: DbSession, response: Response) -> HealthResponse:
    """200 when everything works; 503 (Service Unavailable) when the database can't be reached.

    Deliberately reveals nothing else (no versions, hostnames, or error text): anyone on
    the internet can call this endpoint.
    """
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Health check: database unreachable", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="degraded", database="unavailable")
    return HealthResponse(status="ok", database="ok")
