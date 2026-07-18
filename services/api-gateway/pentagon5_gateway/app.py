"""Independent API gateway process for the Milestone 3 route surface."""

from __future__ import annotations

from fastapi import FastAPI
from pentagon5_auth.app import create_app as create_auth_surface
from pentagon5_auth.config import AuthSettings
from pentagon5_auth.service import AuthenticationService
from sqlalchemy import Engine


def create_app(
    settings: AuthSettings | None = None,
    *,
    service: AuthenticationService | None = None,
    engine: Engine | None = None,
) -> FastAPI:
    """Build a separate gateway app constrained to system and auth APIs."""
    app = create_auth_surface(settings, service=service, engine=engine)
    app.title = "PENTAGON5 API Gateway"
    app.description = (
        "Milestone 3 gateway exposing only system health, authentication, "
        "device, session, and ticketed WebSocket routes."
    )
    return app
