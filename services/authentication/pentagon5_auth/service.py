"""Authentication, session, device, ticket, and RBAC domain service."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pentagon5_runtime.security import fingerprint, pkce_challenge, random_token

from pentagon5_auth.config import AuthSettings
from pentagon5_auth.models import Device, Identity, LoginRedirect, Principal, SessionGrant
from pentagon5_auth.oidc import OIDCClient
from pentagon5_auth.repository import AuthRepository

WS_CHANNELS = frozenset({"system.health", "session.events"})


class AuthenticationError(ValueError):
    """Raised for invalid or expired authentication material."""


class PermissionDenied(PermissionError):
    """Raised when a principal lacks a global permission."""


class AuthenticationService:
    """Coordinates provider-neutral login and opaque local sessions."""

    def __init__(
        self,
        settings: AuthSettings,
        repository: AuthRepository,
        oidc: OIDCClient,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._oidc = oidc
        self._encryption = AESGCM(hashlib.sha256(settings.hmac_key + b":oidc-flow").digest())

    async def start_login(self, *, device_key: str, platform: str) -> str:
        if not 8 <= len(device_key) <= 200:
            raise AuthenticationError("device key must contain 8 to 200 characters")
        if platform not in {"macos", "windows", "linux", "ios", "android", "web"}:
            raise AuthenticationError("unsupported device platform")
        state = random_token()
        nonce = random_token()
        verifier = random_token(48)
        payload = self._seal(
            {"verifier": verifier, "nonce": nonce, "device_key": device_key, "platform": platform},
            b"p5-oidc-flow-v1",
        )
        now = datetime.now(UTC)
        self._repository.put_flow(
            fingerprint(state, self._settings.hmac_key),
            payload,
            self._settings.redirect_uri,
            now + timedelta(seconds=self._settings.flow_ttl_seconds),
        )
        return await self._oidc.authorization_url(
            state=state,
            nonce=nonce,
            code_challenge=pkce_challenge(verifier),
        )

    async def complete_login(self, *, state: str, code: str) -> LoginRedirect:
        if not state or not code:
            raise AuthenticationError("state and authorization code are required")
        now = datetime.now(UTC)
        flow = self._repository.consume_flow(
            fingerprint(state, self._settings.hmac_key),
            now,
        )
        if flow is None:
            raise AuthenticationError("authorization transaction is invalid or expired")
        if flow.redirect_uri != self._settings.redirect_uri:
            raise AuthenticationError("authorization redirect URI does not match")
        payload = self._open(flow.encrypted_payload, b"p5-oidc-flow-v1")
        claims = await self._oidc.exchange(
            code=code,
            verifier=self._required(payload, "verifier"),
            nonce=self._required(payload, "nonce"),
        )
        identity = self._identity(claims)
        user_id = self._repository.provision_identity(identity)
        device_id = self._repository.register_device(
            user_id,
            fingerprint(self._required(payload, "device_key"), self._settings.hmac_key),
            self._required(payload, "platform"),
            now,
        )
        token = random_token()
        token_fingerprint = fingerprint(token, self._settings.hmac_key)
        expires_at = now + timedelta(seconds=self._settings.session_ttl_seconds)
        self._repository.create_session(user_id, device_id, token_fingerprint, expires_at)
        principal = self._repository.resolve_session(token_fingerprint, now)
        if principal is None:
            raise AuthenticationError("identity is not permitted to create a session")
        grant_code = random_token()
        self._repository.put_login_grant(
            fingerprint(grant_code, self._settings.hmac_key),
            self._seal({"session_token": token}, b"p5-login-grant-v1"),
            now + timedelta(seconds=self._settings.login_grant_ttl_seconds),
        )
        redirect_uri = f"{self._settings.desktop_callback_uri}?{urlencode({'code': grant_code})}"
        return LoginRedirect(grant_code, redirect_uri)

    def exchange_login_grant(self, code: str) -> SessionGrant:
        if not code:
            raise AuthenticationError("login grant code is required")
        now = datetime.now(UTC)
        encrypted = self._repository.consume_login_grant(
            fingerprint(code, self._settings.hmac_key),
            now,
        )
        if encrypted is None:
            raise AuthenticationError("login grant is invalid or expired")
        payload = self._open(encrypted, b"p5-login-grant-v1")
        token = self._required(payload, "session_token")
        return SessionGrant(token, self.authenticate(token))

    def authenticate(self, token: str) -> Principal:
        if not token:
            raise AuthenticationError("session token is required")
        principal = self._repository.resolve_session(
            fingerprint(token, self._settings.hmac_key),
            datetime.now(UTC),
        )
        if principal is None:
            raise AuthenticationError("session is invalid or expired")
        return principal

    def require(self, principal: Principal, permission: str) -> None:
        if permission not in principal.permissions:
            raise PermissionDenied(f"missing permission: {permission}")

    def logout(self, principal: Principal) -> None:
        self._repository.revoke_session(principal.session_id, datetime.now(UTC))

    def devices(self, principal: Principal) -> tuple[Device, ...]:
        return tuple(self._repository.list_devices(principal.user_id))

    def revoke_device(self, principal: Principal, device_id: uuid.UUID) -> None:
        if not self._repository.revoke_device(principal.user_id, device_id, datetime.now(UTC)):
            raise AuthenticationError("device was not found")

    def issue_ws_ticket(self, principal: Principal, channel: str) -> str:
        if channel not in WS_CHANNELS:
            raise AuthenticationError("unsupported WebSocket channel")
        if channel == "system.health":
            self.require(principal, "system.health.read")
        ticket = random_token()
        self._repository.put_ws_ticket(
            fingerprint(ticket, self._settings.hmac_key),
            principal.session_id,
            channel,
            datetime.now(UTC) + timedelta(seconds=self._settings.ws_ticket_ttl_seconds),
        )
        return ticket

    def consume_ws_ticket(self, ticket: str, channel: str) -> uuid.UUID:
        if channel not in WS_CHANNELS:
            raise AuthenticationError("unsupported WebSocket channel")
        session_id = self._repository.consume_ws_ticket(
            fingerprint(ticket, self._settings.hmac_key),
            channel,
            datetime.now(UTC),
        )
        if session_id is None:
            raise AuthenticationError("WebSocket ticket is invalid or expired")
        return session_id

    def _seal(self, payload: dict[str, str], associated_data: bytes) -> str:
        nonce = os.urandom(12)
        encoded = json.dumps(payload, separators=(",", ":")).encode()
        ciphertext = self._encryption.encrypt(nonce, encoded, associated_data)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def _open(self, value: str, associated_data: bytes) -> dict[str, Any]:
        try:
            encoded = base64.urlsafe_b64decode(value)
            decoded = self._encryption.decrypt(encoded[:12], encoded[12:], associated_data)
            payload = json.loads(decoded)
        except Exception as error:
            raise AuthenticationError("authorization transaction cannot be decrypted") from error
        if not isinstance(payload, dict):
            raise AuthenticationError("authorization transaction is malformed")
        return payload

    @staticmethod
    def _required(payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise AuthenticationError(f"authorization transaction is missing {key}")
        return value

    def _identity(self, claims: dict[str, Any]) -> Identity:
        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(subject, str) or not isinstance(email, str):
            raise AuthenticationError("ID token is missing subject or email")
        display_name = claims.get("name")
        if not isinstance(display_name, str) or not display_name.strip():
            display_name = email
        return Identity(self._settings.issuer, subject, email.lower(), display_name.strip())
