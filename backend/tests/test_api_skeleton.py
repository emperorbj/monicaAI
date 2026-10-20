"""Tests for the FastAPI skeleton: health check and the shared error format.

Most tests here need no database: they use a fresh app with test-only routes, or a fake
session that simulates a database outage.
"""

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.deps import get_session
from app.main import create_app


def _assert_error_shape(body: dict, code: str) -> None:
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == code


@pytest.fixture
def client_with_test_routes() -> Iterator[TestClient]:
    """A fresh app plus routes that fail on purpose, to exercise the error handlers."""
    app = create_app()

    @app.get("/test/not-found")
    def raise_not_found() -> None:
        raise HTTPException(status_code=404, detail="Facility not found.")

    @app.get("/test/needs-uuid")
    def needs_uuid(lga_id: UUID) -> dict:
        return {"lga_id": str(lga_id)}

    @app.get("/test/crash")
    def crash() -> None:
        raise RuntimeError("secret internal detail: password=hunter2")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


# ---------------------------------------------------------------- error format (no database)


def test_deliberate_404_uses_the_error_format(client_with_test_routes: TestClient) -> None:
    response = client_with_test_routes.get("/test/not-found")

    assert response.status_code == 404
    _assert_error_shape(response.json(), "not_found")
    assert response.json()["error"]["message"] == "Facility not found."


def test_unknown_url_uses_the_error_format(client_with_test_routes: TestClient) -> None:
    response = client_with_test_routes.get("/no/such/page")

    assert response.status_code == 404
    _assert_error_shape(response.json(), "not_found")


def test_invalid_input_lists_each_bad_field(client_with_test_routes: TestClient) -> None:
    response = client_with_test_routes.get("/test/needs-uuid", params={"lga_id": "abc"})

    assert response.status_code == 422
    body = response.json()
    _assert_error_shape(body, "validation_error")
    assert body["error"]["details"][0]["field"] == "query.lga_id"


def test_crash_returns_500_without_leaking_internals(client_with_test_routes: TestClient) -> None:
    response = client_with_test_routes.get("/test/crash")

    assert response.status_code == 500
    _assert_error_shape(response.json(), "internal_error")
    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text


# ---------------------------------------------------------------- health check


class _UnreachableDatabaseSession:
    """Stands in for a Session whose database is down."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_health_reports_503_when_database_is_down() -> None:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: _UnreachableDatabaseSession()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
    assert "connection refused" not in response.text  # no internal details


@pytest.mark.integration
def test_health_is_ok_with_the_real_database(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_openapi_docs_are_served() -> None:
    with TestClient(create_app()) as client:
        assert client.get("/docs").status_code == 200
        assert "/health" in client.get("/openapi.json").json()["paths"]
