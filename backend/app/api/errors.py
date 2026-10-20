"""One JSON shape for every error the API returns:

    {"error": {"code": "not_found", "message": "...", "details": [...] or null}}

The admin app and the bot can then handle all errors the same way, and unexpected crashes
never leak internal details (stack traces, SQL, file paths) to the caller.
"""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def error_response(
    status_code: int, code: str, message: str, details: list[dict[str, Any]] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def _code_for(status_code: int) -> str:
    """404 -> "not_found", 401 -> "unauthorized": a stable, machine-readable error code."""
    return HTTPStatus(status_code).phrase.lower().replace(" ", "_").replace("-", "_")


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Errors raised on purpose (e.g. raise HTTPException(404)), plus unknown URLs."""
    message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    response = error_response(exc.status_code, _code_for(exc.status_code), message)
    # Keep headers such as WWW-Authenticate, which login errors need (Step 4).
    response.headers.update(exc.headers or {})
    return response


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Input that doesn't match the declared types, e.g. ?lga_id=abc where a UUID is expected."""
    details = [
        # loc is e.g. ("query", "lga_id"); joined it reads "query.lga_id".
        {"field": ".".join(str(part) for part in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        "The request contains invalid or missing values.",
        details,
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Any bug we didn't anticipate. Full details go to OUR logs, never to the caller."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "Something went wrong on our side. Please try again later.",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
