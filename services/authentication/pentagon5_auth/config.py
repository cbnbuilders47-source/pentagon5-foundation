"""Authentication service configuration."""

from __future__ import annotations

import base64
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

from pentagon5_runtime.config import (
    ConfigurationError,
    RuntimeSettings,
    load_runtime_settings,
    secret_value,
)

AUTH_KEYS = frozenset(
    {
        "P5_OIDC_CLIENT_ID",
        "P5_OIDC_CLIENT_SECRET",
        "P5_OIDC_CLIENT_SECRET_FILE",
        "P5_OIDC_ISSUER",
        "P5_OIDC_REDIRECT_URI",
        "P5_DESKTOP_CALLBACK_URI",
        "P5_LOGIN_GRANT_TTL_SECONDS",
        "P5_SESSION_HMAC_KEY",
        "P5_SESSION_HMAC_KEY_FILE",
        "P5_SESSION_TTL_SECONDS",
        "P5_OIDC_FLOW_TTL_SECONDS",
        "P5_WS_TICKET_TTL_SECONDS",
        "P5_WS_MAX_FRAME_BYTES",
        "P5_WS_MAX_SUBSCRIPTIONS",
        "P5_WEB_COOKIE_MODE",
    }
)


@dataclass(frozen=True, slots=True)
class AuthSettings:
    """Complete authentication process settings."""

    runtime: RuntimeSettings
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    hmac_key: bytes
    desktop_callback_uri: str = "pentagon5://auth/callback"
    session_ttl_seconds: int = 28800
    flow_ttl_seconds: int = 300
    login_grant_ttl_seconds: int = 60
    ws_ticket_ttl_seconds: int = 30
    ws_max_frame_bytes: int = 16_384
    ws_max_subscriptions: int = 1
    web_cookie_mode: bool = False


def _positive_int(values: Mapping[str, str], name: str, default: int, maximum: int) -> int:
    try:
        value = int(values.get(name, str(default)))
    except ValueError as error:
        raise ConfigurationError(f"{name} must be an integer") from error
    if not 1 <= value <= maximum:
        raise ConfigurationError(f"{name} must be between 1 and {maximum}")
    return value


def load_auth_settings(environ: Mapping[str, str] | None = None) -> AuthSettings:
    """Load strict OIDC and session settings."""
    values = dict(os.environ if environ is None else environ)
    runtime = load_runtime_settings(values, allowed_extra=AUTH_KEYS)
    issuer = values.get("P5_OIDC_ISSUER", "").rstrip("/")
    redirect_uri = values.get("P5_OIDC_REDIRECT_URI", "")
    client_id = values.get("P5_OIDC_CLIENT_ID", "")
    desktop_callback_uri = values.get("P5_DESKTOP_CALLBACK_URI", "")
    if not issuer or not client_id or not redirect_uri or not desktop_callback_uri:
        raise ConfigurationError(
            "OIDC issuer, client ID, provider redirect URI, and desktop callback URI are required"
        )
    issuer_url = urlparse(issuer)
    redirect_url = urlparse(redirect_uri)
    desktop_url = urlparse(desktop_callback_uri)
    if runtime.environment not in {"development", "test"}:
        if issuer_url.scheme != "https" or redirect_url.scheme != "https":
            raise ConfigurationError("OIDC issuer and redirect URI must use HTTPS")
    elif issuer_url.scheme not in {"http", "https"}:
        raise ConfigurationError("OIDC issuer must use HTTP or HTTPS")
    if (
        not desktop_url.scheme
        or desktop_url.scheme in {"http", "https"}
        or desktop_url.query
        or desktop_url.fragment
        or not desktop_url.netloc
    ):
        raise ConfigurationError(
            "P5_DESKTOP_CALLBACK_URI must be an exact custom URI without query or fragment"
        )
    web_cookie_value = values.get("P5_WEB_COOKIE_MODE", "false").lower()
    if web_cookie_value not in {"true", "false"}:
        raise ConfigurationError("P5_WEB_COOKIE_MODE must be true or false")
    raw_key = secret_value("P5_SESSION_HMAC_KEY", values)
    try:
        hmac_key = base64.b64decode(
            raw_key + "=" * (-len(raw_key) % 4),
            altchars=b"-_",
            validate=True,
        )
    except ValueError as error:
        raise ConfigurationError("P5_SESSION_HMAC_KEY must be URL-safe base64") from error
    if len(hmac_key) < 32:
        raise ConfigurationError("P5_SESSION_HMAC_KEY must decode to at least 32 bytes")
    ws_max_frame_bytes = _positive_int(values, "P5_WS_MAX_FRAME_BYTES", 16384, 65536)
    if ws_max_frame_bytes < 1024:
        raise ConfigurationError("P5_WS_MAX_FRAME_BYTES must be at least 1024")
    return AuthSettings(
        runtime=runtime,
        issuer=issuer,
        client_id=client_id,
        client_secret=secret_value("P5_OIDC_CLIENT_SECRET", values),
        redirect_uri=redirect_uri,
        hmac_key=hmac_key,
        desktop_callback_uri=desktop_callback_uri,
        session_ttl_seconds=_positive_int(values, "P5_SESSION_TTL_SECONDS", 28800, 86400),
        flow_ttl_seconds=_positive_int(values, "P5_OIDC_FLOW_TTL_SECONDS", 300, 600),
        login_grant_ttl_seconds=_positive_int(values, "P5_LOGIN_GRANT_TTL_SECONDS", 60, 120),
        ws_ticket_ttl_seconds=_positive_int(values, "P5_WS_TICKET_TTL_SECONDS", 30, 60),
        ws_max_frame_bytes=ws_max_frame_bytes,
        ws_max_subscriptions=_positive_int(values, "P5_WS_MAX_SUBSCRIPTIONS", 1, 4),
        web_cookie_mode=web_cookie_value == "true",
    )
