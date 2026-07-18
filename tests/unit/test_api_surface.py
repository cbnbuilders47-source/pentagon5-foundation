"""API gateway route-scope and authentication fail-closed tests."""

from __future__ import annotations

import asyncio
from typing import cast

import pytest
from fastapi.testclient import TestClient
from pentagon5_auth.app import create_app
from pentagon5_auth.config import AuthSettings
from pentagon5_auth.models import LoginRedirect
from pentagon5_auth.service import AuthenticationError, AuthenticationService
from pentagon5_gateway.app import create_app as create_gateway_app
from pentagon5_runtime.config import RuntimeSettings
from pentagon5_runtime.envelopes import websocket_envelope
from pentagon5_runtime.uuid7 import is_uuid7, uuid7
from sqlalchemy import create_engine
from starlette.websockets import WebSocketDisconnect

TEST_CLIENT_SECRET = "test-secret"  # pragma: allowlist secret


class RejectingService:
    def authenticate(self, token: str) -> object:
        raise AuthenticationError("session is invalid or expired")


class WebSocketService(RejectingService):
    def consume_ws_ticket(self, ticket: str, channel: str) -> object:
        assert ticket == "fixture-ticket"
        assert channel in {"system.health", "session.events"}
        return uuid7()


class CallbackService(RejectingService):
    async def complete_login(self, *, state: str, code: str) -> LoginRedirect:
        assert state and code
        return LoginRedirect(
            "one-time-code",
            "pentagon5://auth/callback?code=one-time-code",
        )


class SlowService(RejectingService):
    async def start_login(self, *, device_key: str, platform: str) -> str:
        await asyncio.sleep(0.1)
        return "http://oidc.test/authorize"


def test_route_surface_is_limited_to_system_and_authentication() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings("api-test", "test", "postgresql://db/test"),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    app = create_app(
        settings,
        service=cast(AuthenticationService, RejectingService()),
        engine=create_engine("sqlite://"),
    )
    paths = set(app.openapi()["paths"])
    assert paths == {
        "/v1/system/health/live",
        "/v1/system/health/ready",
        "/v1/system/health/startup",
        "/v1/auth/oidc/start",
        "/v1/auth/oidc/callback",
        "/v1/auth/oidc/exchange",
        "/v1/auth/session",
        "/v1/auth/logout",
        "/v1/auth/devices",
        "/v1/auth/devices/{device_id}",
        "/v1/auth/ws-tickets",
    }
    assert not any(
        fragment in path
        for path in paths
        for fragment in ("broker", "market", "strategy", "order", "risk", "execution", "ai")
    )

    with TestClient(app) as client:
        health = client.get("/v1/system/health/live")
        assert health.status_code == 200
        assert health.json()["category"] == "health"
        assert is_uuid7(health.headers["x-request-id"])
        unauthorized = client.get("/v1/auth/session")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["category"] == "error"
        assert unauthorized.json()["payload"]["code"] == "SESSION_INVALID"
        assert (
            unauthorized.json()["metadata"]["correlationId"] == unauthorized.headers["x-request-id"]
        )
        supplied_id = str(uuid7())
        propagated = client.get(
            "/v1/system/health/live",
            headers={"x-request-id": supplied_id},
        )
        assert propagated.headers["x-request-id"] == supplied_id
        assert propagated.json()["metadata"]["correlationId"] == supplied_id
        replaced = client.get(
            "/v1/system/health/live",
            headers={"x-request-id": "550e8400-e29b-41d4-a716-446655440000"},
        )
        assert is_uuid7(replaced.headers["x-request-id"])
        assert replaced.headers["x-request-id"] != ("550e8400-e29b-41d4-a716-446655440000")


def test_authentication_and_gateway_factories_start_independently() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings("factory-test", "test", "postgresql://db/test"),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    fake_service = cast(AuthenticationService, RejectingService())
    for factory in (create_app, create_gateway_app):
        app = factory(settings, service=fake_service, engine=create_engine("sqlite://"))
        with TestClient(app) as client:
            assert client.get("/v1/system/health/startup").status_code == 200


def test_provider_callback_redirect_contains_only_one_time_code() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings("callback-test", "test", "postgresql://db/test"),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    app = create_app(
        settings,
        service=cast(AuthenticationService, CallbackService()),
        engine=create_engine("sqlite://"),
    )
    with TestClient(app) as client:
        response = client.get(
            "/v1/auth/oidc/callback",
            params={"state": "s" * 32, "code": "provider-code"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == ("pentagon5://auth/callback?code=one-time-code")
    assert "session" not in response.headers["location"]
    assert "token" not in response.headers["location"]
    assert "set-cookie" not in response.headers


def test_exact_cors_and_body_limit_are_enforced() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings(
            "security-test",
            "test",
            "postgresql://db/test",
            cors_origins=("https://desktop.example.test",),
            max_body_bytes=64,
        ),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    app = create_app(
        settings,
        service=cast(AuthenticationService, RejectingService()),
        engine=create_engine("sqlite://"),
    )
    with TestClient(app) as client:
        preflight = client.options(
            "/v1/auth/oidc/start",
            headers={
                "Origin": "https://desktop.example.test",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert preflight.headers["access-control-allow-origin"] == ("https://desktop.example.test")
        denied = client.options(
            "/v1/auth/oidc/start",
            headers={
                "Origin": "https://evil.example.test",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.status_code == 400
        assert denied.json()["payload"]["code"] == "CORS_ORIGIN_DENIED"
        rejected = client.post(
            "/v1/auth/oidc/start",
            content=b"x" * 65,
            headers={"content-type": "application/json"},
        )
        assert rejected.status_code == 413
        assert rejected.json()["payload"]["code"] == "REQUEST_BODY_TOO_LARGE"


def test_request_timeout_returns_accepted_error_envelope() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings(
            "timeout-test",
            "test",
            "postgresql://db/test",
            request_timeout_seconds=0.01,
        ),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    app = create_app(
        settings,
        service=cast(AuthenticationService, SlowService()),
        engine=create_engine("sqlite://"),
    )
    with TestClient(app) as client:
        response = client.post(
            "/v1/auth/oidc/start",
            json={"device_key": "fixture-device", "platform": "macos"},
        )
    assert response.status_code == 504
    assert response.json()["payload"] == {
        "code": "REQUEST_TIMEOUT",
        "message": "Request processing timed out",
        "retryable": True,
    }


def test_websocket_controls_are_validated_and_subscription_count_is_bounded() -> None:
    settings = AuthSettings(
        runtime=RuntimeSettings("ws-test", "test", "postgresql://db/test"),
        issuer="http://oidc.test",
        client_id="test-client",
        client_secret=TEST_CLIENT_SECRET,
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
        ws_max_subscriptions=1,
    )
    app = create_app(
        settings,
        service=cast(AuthenticationService, WebSocketService()),
        engine=create_engine("sqlite://"),
    )
    correlation_id = str(uuid7())
    first_subscription = str(uuid7())
    with TestClient(app) as client:
        with client.websocket_connect("/v1/ws/system.health?ticket=fixture-ticket") as websocket:
            websocket.send_json(
                websocket_envelope(
                    correlation_id,
                    operation="subscribe",
                    channel="system.health",
                    subscription_id=first_subscription,
                )
            )
            acknowledgement = websocket.receive_json()
            assert acknowledgement["category"] == "websocket"
            assert acknowledgement["payload"]["operation"] == "ack"
            assert websocket.receive_json()["category"] == "health"
            websocket.send_json(
                websocket_envelope(
                    correlation_id,
                    operation="subscribe",
                    channel="system.health",
                    subscription_id=str(uuid7()),
                )
            )
            with pytest.raises(WebSocketDisconnect) as closed:
                websocket.receive_json()
            assert closed.value.code == 1008

        with client.websocket_connect("/v1/ws/session.events?ticket=fixture-ticket") as websocket:
            websocket.send_text("{not-json")
            with pytest.raises(WebSocketDisconnect) as closed:
                websocket.receive_json()
            assert closed.value.code == 1008

        with client.websocket_connect("/v1/ws/session.events?ticket=fixture-ticket") as websocket:
            websocket.send_text("x" * (settings.ws_max_frame_bytes + 1))
            with pytest.raises(WebSocketDisconnect) as closed:
                websocket.receive_json()
            assert closed.value.code == 1009
