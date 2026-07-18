"""Independent FastAPI application exposing explicit auth and system routes."""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated, Literal

import httpx
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pentagon5_runtime.database import create_database_engine, database_is_ready
from pentagon5_runtime.envelopes import error_envelope, health_envelope, websocket_envelope
from pentagon5_runtime.logging import configure_logging, request_id
from pentagon5_runtime.observability import instrument
from pentagon5_runtime.uuid7 import is_uuid7, uuid7
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine
from starlette.responses import JSONResponse, RedirectResponse

from pentagon5_auth.config import AuthSettings, load_auth_settings
from pentagon5_auth.models import Principal
from pentagon5_auth.oidc import OIDCClient, OIDCError
from pentagon5_auth.repository import PostgresAuthRepository
from pentagon5_auth.service import AuthenticationError, AuthenticationService, PermissionDenied

COOKIE_NAME = "__Host-p5_session"
LOGGER = logging.getLogger(__name__)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginStart(StrictModel):
    device_key: str = Field(min_length=8, max_length=200)
    platform: Literal["macos", "windows", "linux", "ios", "android", "web"]


class LoginStartResponse(StrictModel):
    authorization_url: str


class SessionResponse(StrictModel):
    user_id: uuid.UUID
    session_id: uuid.UUID
    email: str
    display_name: str
    roles: tuple[str, ...]
    permissions: frozenset[str]
    expires_at: datetime


class LoginGrantExchange(StrictModel):
    code: str = Field(min_length=32, max_length=512)


class LoginGrantResponse(StrictModel):
    session_token: str
    session: SessionResponse


class DeviceResponse(StrictModel):
    id: uuid.UUID
    platform: str
    last_seen_at: datetime | None
    revoked_at: datetime | None


class TicketRequest(StrictModel):
    channel: Literal["system.health", "session.events"]


class TicketResponse(StrictModel):
    ticket: str
    channel: Literal["system.health", "session.events"]
    expires_in_seconds: int


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, *, retryable: bool = False
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable


def _correlation_id() -> str:
    return request_id.get() or str(uuid7())


def _is_utc_z(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


def _websocket_control(text: str, expected_channel: str) -> tuple[str, str, str | None]:
    try:
        message = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("malformed JSON") from error
    if not isinstance(message, dict) or set(message) != {
        "schemaVersion",
        "messageId",
        "category",
        "occurredAt",
        "metadata",
        "payload",
    }:
        raise ValueError("invalid WebSocket envelope")
    metadata = message.get("metadata")
    payload = message.get("payload")
    if (
        message.get("schemaVersion") != "1.0.0"
        or message.get("category") != "websocket"
        or not is_uuid7(str(message.get("messageId", "")))
        or not _is_utc_z(message.get("occurredAt"))
        or not isinstance(metadata, dict)
        or set(metadata) - {"correlationId", "causationId"}
        or not is_uuid7(str(metadata.get("correlationId", "")))
        or (metadata.get("causationId") is not None and not is_uuid7(str(metadata["causationId"])))
        or not isinstance(payload, dict)
        or set(payload) - {"operation", "channel", "subscriptionId"}
    ):
        raise ValueError("invalid WebSocket envelope")
    operation = payload.get("operation")
    channel = payload.get("channel")
    subscription_id = payload.get("subscriptionId")
    if operation not in {"subscribe", "unsubscribe", "heartbeat"}:
        raise ValueError("unsupported WebSocket operation")
    if channel != expected_channel:
        raise ValueError("WebSocket channel does not match ticket")
    if subscription_id is not None and not is_uuid7(str(subscription_id)):
        raise ValueError("invalid subscription ID")
    if operation in {"subscribe", "unsubscribe"} and subscription_id is None:
        raise ValueError("subscription ID is required")
    return (
        str(operation),
        str(metadata["correlationId"]),
        (None if subscription_id is None else str(subscription_id)),
    )


def _session_response(principal: Principal) -> SessionResponse:
    return SessionResponse(
        user_id=principal.user_id,
        session_id=principal.session_id,
        email=principal.email,
        display_name=principal.display_name,
        roles=principal.roles,
        permissions=principal.permissions,
        expires_at=principal.expires_at,
    )


def create_app(
    settings: AuthSettings | None = None,
    *,
    service: AuthenticationService | None = None,
    engine: Engine | None = None,
) -> FastAPI:
    """Build the independently deployable authentication application."""
    resolved_settings = settings or load_auth_settings()
    configure_logging(
        resolved_settings.runtime.log_level,
        environment=resolved_settings.runtime.environment,
    )
    resolved_engine = engine or create_database_engine(resolved_settings.runtime.database_url)
    oidc_http: httpx.AsyncClient | None = None
    if service is None:
        oidc_http = httpx.AsyncClient(timeout=httpx.Timeout(10.0), follow_redirects=False)
        service = AuthenticationService(
            resolved_settings,
            PostgresAuthRepository(resolved_engine),
            OIDCClient(resolved_settings, oidc_http),
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if oidc_http is not None:
            await oidc_http.aclose()
        if engine is None:
            resolved_engine.dispose()

    app = FastAPI(
        title="PENTAGON5 Authentication",
        version="1.0.0",
        docs_url=None if resolved_settings.runtime.environment == "production" else "/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    if resolved_settings.runtime.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.runtime.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
            max_age=600,
        )
    instrument(app, resolved_settings.runtime)

    def error_response(
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        field: str | None = None,
    ) -> JSONResponse:
        return JSONResponse(
            error_envelope(
                _correlation_id(),
                code=code,
                message=message,
                retryable=retryable,
                field=field,
            ),
            status_code=status_code,
        )

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, error: ApiError) -> JSONResponse:
        return error_response(
            error.status_code,
            error.code,
            error.message,
            retryable=error.retryable,
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
        codes = {
            404: ("NOT_FOUND", "Resource not found", False),
            405: ("METHOD_NOT_ALLOWED", "Method not allowed", False),
        }
        code, message, retryable = codes.get(
            error.status_code,
            ("HTTP_ERROR", "Request could not be completed", False),
        )
        return error_response(error.status_code, code, message, retryable=retryable)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        first = error.errors()[0] if error.errors() else {}
        location = first.get("loc", ())
        field = ".".join(str(item) for item in location[1:]) or None
        return error_response(
            422,
            "REQUEST_VALIDATION_FAILED",
            "Request validation failed",
            field=field,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, error: Exception) -> JSONResponse:
        LOGGER.error("Unhandled request failure: %s", type(error).__name__)
        return error_response(
            500,
            "INTERNAL_ERROR",
            "An internal error occurred",
            retryable=True,
        )

    def current_principal(request: Request) -> Principal:
        authorization = request.headers.get("authorization", "")
        token = ""
        if authorization:
            scheme, separator, credentials = authorization.partition(" ")
            if not separator or scheme.lower() != "bearer":
                raise ApiError(
                    status.HTTP_401_UNAUTHORIZED,
                    "AUTHORIZATION_SCHEME_INVALID",
                    "Authorization must use Bearer",
                )
            token = credentials
        elif resolved_settings.web_cookie_mode:
            token = request.cookies.get(COOKIE_NAME, "")
        try:
            return service.authenticate(token)
        except AuthenticationError as error:
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "SESSION_INVALID",
                "Session is invalid or expired",
            ) from error

    PrincipalDependency = Annotated[Principal, Depends(current_principal)]

    @app.get("/v1/system/health/startup")
    def startup() -> dict[str, object]:
        return health_envelope(
            _correlation_id(),
            component=resolved_settings.runtime.service_name,
            status="healthy",
            detail="application startup completed",
        )

    @app.get("/v1/system/health/live")
    def live() -> dict[str, object]:
        return health_envelope(
            _correlation_id(),
            component=resolved_settings.runtime.service_name,
            status="healthy",
        )

    @app.get("/v1/system/health/ready")
    async def ready() -> dict[str, object]:
        try:
            available = await asyncio.wait_for(
                asyncio.to_thread(database_is_ready, resolved_engine),
                timeout=min(2.0, resolved_settings.runtime.request_timeout_seconds),
            )
        except TimeoutError:
            available = False
        if not available:
            raise ApiError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "DATABASE_UNAVAILABLE",
                "Database is unavailable",
                retryable=True,
            )
        return health_envelope(
            _correlation_id(),
            component=resolved_settings.runtime.service_name,
            status="healthy",
            detail="database connection available",
        )

    @app.post("/v1/auth/oidc/start", response_model=LoginStartResponse)
    async def start_login(body: LoginStart) -> LoginStartResponse:
        try:
            url = await service.start_login(device_key=body.device_key, platform=body.platform)
        except AuthenticationError as error:
            raise ApiError(
                status.HTTP_400_BAD_REQUEST,
                "LOGIN_REQUEST_INVALID",
                "Login request is invalid",
            ) from error
        return LoginStartResponse(authorization_url=url)

    @app.get("/v1/auth/oidc/callback", response_class=RedirectResponse)
    async def callback(
        code: Annotated[str, Query(min_length=1, max_length=4096)],
        state_value: Annotated[str, Query(alias="state", min_length=32, max_length=512)],
    ) -> RedirectResponse:
        try:
            login_redirect = await service.complete_login(state=state_value, code=code)
        except (AuthenticationError, OIDCError, httpx.HTTPError) as error:
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "OIDC_LOGIN_FAILED",
                "OIDC login failed",
            ) from error
        return RedirectResponse(login_redirect.redirect_uri, status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/v1/auth/oidc/exchange", response_model=LoginGrantResponse)
    def exchange(body: LoginGrantExchange, response: Response) -> LoginGrantResponse:
        try:
            grant = service.exchange_login_grant(body.code)
        except AuthenticationError as error:
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "LOGIN_GRANT_INVALID",
                "Login grant is invalid or expired",
            ) from error
        if resolved_settings.web_cookie_mode:
            response.set_cookie(
                COOKIE_NAME,
                grant.token,
                max_age=resolved_settings.session_ttl_seconds,
                secure=True,
                httponly=True,
                samesite="strict",
                path="/",
            )
        return LoginGrantResponse(
            session_token=grant.token,
            session=_session_response(grant.principal),
        )

    @app.get("/v1/auth/session", response_model=SessionResponse)
    def session(principal: PrincipalDependency) -> SessionResponse:
        return _session_response(principal)

    @app.post("/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(response: Response, principal: PrincipalDependency) -> None:
        service.logout(principal)
        if resolved_settings.web_cookie_mode:
            response.delete_cookie(
                COOKIE_NAME,
                secure=True,
                httponly=True,
                samesite="strict",
                path="/",
            )

    @app.get("/v1/auth/devices", response_model=list[DeviceResponse])
    def devices(principal: PrincipalDependency) -> list[DeviceResponse]:
        return [
            DeviceResponse(
                id=device.id,
                platform=device.platform,
                last_seen_at=device.last_seen_at,
                revoked_at=device.revoked_at,
            )
            for device in service.devices(principal)
        ]

    @app.delete("/v1/auth/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
    def revoke_device(device_id: uuid.UUID, principal: PrincipalDependency) -> None:
        try:
            service.revoke_device(principal, device_id)
        except AuthenticationError as error:
            raise ApiError(
                status.HTTP_404_NOT_FOUND,
                "DEVICE_NOT_FOUND",
                "Device was not found",
            ) from error

    @app.post("/v1/auth/ws-tickets", response_model=TicketResponse)
    def ws_ticket(body: TicketRequest, principal: PrincipalDependency) -> TicketResponse:
        try:
            ticket = service.issue_ws_ticket(principal, body.channel)
        except PermissionDenied as error:
            raise ApiError(
                status.HTTP_403_FORBIDDEN,
                "PERMISSION_DENIED",
                "Permission denied",
            ) from error
        return TicketResponse(
            ticket=ticket,
            channel=body.channel,
            expires_in_seconds=resolved_settings.ws_ticket_ttl_seconds,
        )

    @app.websocket("/v1/ws/{channel}")
    async def websocket(websocket: WebSocket, channel: str, ticket: str = Query()) -> None:
        try:
            service.consume_ws_ticket(ticket, channel)
        except AuthenticationError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await websocket.accept()
        subscriptions: set[str] = set()
        try:
            while True:
                incoming = await websocket.receive()
                if incoming["type"] == "websocket.disconnect":
                    return
                frame = incoming.get("text")
                if not isinstance(frame, str):
                    await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
                    return
                if len(frame.encode()) > resolved_settings.ws_max_frame_bytes:
                    await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                    return
                try:
                    operation, correlation_id, subscription_id = _websocket_control(frame, channel)
                except ValueError:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
                if operation == "subscribe":
                    if (
                        subscription_id not in subscriptions
                        and len(subscriptions) >= resolved_settings.ws_max_subscriptions
                    ):
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        return
                    if subscription_id is not None:
                        subscriptions.add(subscription_id)
                elif operation == "unsubscribe" and subscription_id is not None:
                    subscriptions.discard(subscription_id)
                await websocket.send_json(
                    websocket_envelope(
                        correlation_id,
                        operation="ack" if operation != "heartbeat" else "heartbeat",
                        channel=channel,
                        subscription_id=subscription_id,
                    )
                )
                if operation == "subscribe" and channel == "system.health":
                    await websocket.send_json(
                        health_envelope(
                            correlation_id,
                            component=resolved_settings.runtime.service_name,
                            status="healthy",
                        )
                    )
        except WebSocketDisconnect:
            return

    return app
