"""Authentication domain security and replay tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import cast
from urllib.parse import parse_qs, urlparse

import pytest
from pentagon5_auth.config import AuthSettings
from pentagon5_auth.models import Device, Flow, Identity, Principal
from pentagon5_auth.oidc import OIDCClient
from pentagon5_auth.repository import AuthRepository
from pentagon5_auth.service import AuthenticationError, AuthenticationService
from pentagon5_runtime.config import RuntimeSettings
from pentagon5_runtime.uuid7 import uuid7


class FixtureOIDC:
    verifier = ""

    async def authorization_url(self, *, state: str, nonce: str, code_challenge: str) -> str:
        assert state and nonce and code_challenge
        return f"http://oidc.test/authorize?state={state}"

    async def exchange(self, *, code: str, verifier: str, nonce: str) -> dict[str, object]:
        assert code == "fixture-code"
        assert nonce
        self.verifier = verifier
        return {
            "sub": "fixture-subject",
            "email": "USER@example.test",
            "email_verified": True,
            "name": "Fixture User",
        }


class MemoryRepository:
    user_id = uuid7()
    device_id = uuid7()
    session_id = uuid7()

    def __init__(self) -> None:
        self.flow: tuple[str, Flow, datetime] | None = None
        self.login_grant: tuple[str, str, datetime] | None = None
        self.session_fingerprint = ""
        self.ticket: tuple[str, str, datetime] | None = None

    def put_flow(
        self, fingerprint: str, encrypted_payload: str, redirect_uri: str, expires_at: datetime
    ) -> None:
        self.flow = (fingerprint, Flow(encrypted_payload, redirect_uri), expires_at)

    def consume_flow(self, fingerprint: str, now: datetime) -> Flow | None:
        value = self.flow
        self.flow = None
        if value is None or value[0] != fingerprint or value[2] <= now:
            return None
        return value[1]

    def put_login_grant(
        self, fingerprint: str, encrypted_payload: str, expires_at: datetime
    ) -> None:
        self.login_grant = (fingerprint, encrypted_payload, expires_at)

    def consume_login_grant(self, fingerprint: str, now: datetime) -> str | None:
        value = self.login_grant
        self.login_grant = None
        if value is None or value[0] != fingerprint or value[2] <= now:
            return None
        return value[1]

    def provision_identity(self, identity: Identity) -> uuid.UUID:
        assert identity.email == "user@example.test"
        return self.user_id

    def register_device(
        self, user_id: uuid.UUID, device_fingerprint: str, platform: str, now: datetime
    ) -> uuid.UUID:
        assert user_id == self.user_id
        assert device_fingerprint != "fixture-device"
        assert platform == "macos"
        return self.device_id

    def create_session(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        token_fingerprint: str,
        expires_at: datetime,
    ) -> uuid.UUID:
        assert user_id == self.user_id and device_id == self.device_id
        self.session_fingerprint = token_fingerprint
        return self.session_id

    def resolve_session(self, token_fingerprint: str, now: datetime) -> Principal | None:
        if token_fingerprint != self.session_fingerprint:
            return None
        return Principal(
            self.user_id,
            self.session_id,
            self.device_id,
            "user@example.test",
            "Fixture User",
            ("viewer",),
            frozenset({"system.health.read"}),
            now + timedelta(hours=1),
        )

    def revoke_session(self, session_id: uuid.UUID, now: datetime) -> None:
        self.session_fingerprint = ""

    def list_devices(self, user_id: uuid.UUID) -> tuple[Device, ...]:
        return ()

    def revoke_device(self, user_id: uuid.UUID, device_id: uuid.UUID, now: datetime) -> bool:
        return device_id == self.device_id

    def put_ws_ticket(
        self,
        ticket_fingerprint: str,
        session_id: uuid.UUID,
        channel: str,
        expires_at: datetime,
    ) -> None:
        self.ticket = (ticket_fingerprint, channel, expires_at)

    def consume_ws_ticket(
        self, ticket_fingerprint: str, channel: str, now: datetime
    ) -> uuid.UUID | None:
        value = self.ticket
        self.ticket = None
        if (
            value is None
            or value[0] != ticket_fingerprint
            or value[1] != channel
            or value[2] <= now
        ):
            return None
        return self.session_id


def fixture_service() -> tuple[AuthenticationService, MemoryRepository, FixtureOIDC]:
    settings = AuthSettings(
        runtime=RuntimeSettings("auth-test", "test", "postgresql://db/test"),
        issuer="http://oidc.test",
        client_id="fixture-client",
        client_secret="fixture-secret",  # pragma: allowlist secret
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
        desktop_callback_uri="pentagon5://auth/callback",
    )
    repository = MemoryRepository()
    oidc = FixtureOIDC()
    service = AuthenticationService(
        settings,
        cast(AuthRepository, repository),
        cast(OIDCClient, oidc),
    )
    return service, repository, oidc


@pytest.mark.asyncio
async def test_login_flow_encrypts_pkce_material_and_rejects_replay() -> None:
    service, repository, oidc = fixture_service()
    authorization_url = await service.start_login(
        device_key="fixture-device",
        platform="macos",
    )
    assert "state=" in authorization_url
    assert repository.flow is not None
    assert "fixture-device" not in repository.flow[1].encrypted_payload

    state = authorization_url.split("state=", maxsplit=1)[1]
    login_redirect = await service.complete_login(state=state, code="fixture-code")
    parsed = urlparse(login_redirect.redirect_uri)
    assert (parsed.scheme, parsed.netloc, parsed.path) == ("pentagon5", "auth", "/callback")
    assert set(parse_qs(parsed.query)) == {"code"}
    assert parse_qs(parsed.query)["code"] == [login_redirect.code]
    assert repository.login_grant is not None
    assert login_redirect.code not in repository.login_grant[1]
    assert "session" not in login_redirect.redirect_uri
    assert len(oidc.verifier) >= 64
    grant = service.exchange_login_grant(login_redirect.code)
    assert service.authenticate(grant.token).user_id == repository.user_id
    with pytest.raises(AuthenticationError, match="invalid or expired"):
        service.exchange_login_grant(login_redirect.code)

    with pytest.raises(AuthenticationError, match="invalid or expired"):
        await service.complete_login(state=state, code="fixture-code")


@pytest.mark.asyncio
async def test_expired_login_grant_cannot_be_exchanged() -> None:
    service, repository, _ = fixture_service()
    authorization_url = await service.start_login(device_key="fixture-device", platform="macos")
    state = authorization_url.split("state=", maxsplit=1)[1]
    login_redirect = await service.complete_login(state=state, code="fixture-code")
    assert repository.login_grant is not None
    stored = repository.login_grant
    repository.login_grant = (stored[0], stored[1], datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(AuthenticationError, match="invalid or expired"):
        service.exchange_login_grant(login_redirect.code)


def test_websocket_tickets_are_channel_bound_and_single_use() -> None:
    service, repository, _ = fixture_service()
    repository.session_fingerprint = "unused"
    principal = Principal(
        repository.user_id,
        repository.session_id,
        repository.device_id,
        "user@example.test",
        "Fixture User",
        (),
        frozenset({"system.health.read"}),
        datetime.now(UTC) + timedelta(hours=1),
    )
    ticket = service.issue_ws_ticket(principal, "system.health")
    assert service.consume_ws_ticket(ticket, "system.health") == repository.session_id
    with pytest.raises(AuthenticationError, match="invalid or expired"):
        service.consume_ws_ticket(ticket, "system.health")
    with pytest.raises(AuthenticationError, match="unsupported"):
        service.issue_ws_ticket(principal, "orders")
