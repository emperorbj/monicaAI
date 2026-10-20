"""The FastAPI application.

Run the development server from backend/:   uv run fastapi dev app/main.py
Then open http://127.0.0.1:8000/docs for the interactive API documentation.
"""

from fastapi import FastAPI

from app.api import health
from app.api.errors import register_error_handlers


def create_app() -> FastAPI:
    """Build the app. A function (not just a global) so tests can build fresh copies."""
    app = FastAPI(
        title="AI Health Service Navigator Nigeria API",
        version="0.1.0",
        description=(
            "Find health facilities, services, and contact persons in Nigeria. "
            "POC: all facility data is fictional demo data unless marked otherwise."
        ),
    )
    register_error_handlers(app)
    app.include_router(health.router)
    return app


# The object `fastapi dev` / uvicorn look for.
app = create_app()
