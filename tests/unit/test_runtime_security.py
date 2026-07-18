"""Security-focused tests for shared runtime configuration and tokens."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

import pytest
from pentagon5_auth.config import load_auth_settings
from pentagon5_runtime.config import ConfigurationError, load_runtime_settings, secret_value
from pentagon5_runtime.logging import JsonFormatter, configure_logging
from pentagon5_runtime.security import fingerprint, pkce_challenge, random_token
from pentagon5_runtime.uuid7 import is_uuid7, uuid7

PROVIDER_SECRET = "provider-secret"  # pragma: allowlist secret
TEST_SECRET = "secret"  # pragma: allowlist secret


def test_secret_file_is_supported_without_environment_secret(tmp_path: Path) -> None:
    secret = tmp_path / "database-url"
    secret.write_text("postgresql+psycopg://db/app\n", encoding="utf-8")
    values = {"P5_DATABASE_URL_FILE": str(secret)}
    assert secret_value("P5_DATABASE_URL", values) == "postgresql+psycopg://db/app"


def test_direct_and_file_secret_are_rejected_together(tmp_path: Path) -> None:
    secret = tmp_path / "secret"
    secret.write_text("file-value", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="mutually exclusive"):
        secret_value(
            "P5_DATABASE_URL",
            {"P5_DATABASE_URL": "direct", "P5_DATABASE_URL_FILE": str(secret)},
        )


def test_unknown_prefixed_configuration_fails_closed() -> None:
    with pytest.raises(ConfigurationError, match="P5_DATABSE_URL"):
        load_runtime_settings(
            {
                "P5_SERVICE_NAME": "test",
                "P5_DATABASE_URL": "postgresql://db/test",
                "P5_DATABSE_URL": "typo",
            }
        )


def test_fingerprints_are_keyed_and_do_not_contain_token() -> None:
    token = random_token()
    key = b"a" * 32
    digest = fingerprint(token, key)
    assert token not in digest
    assert len(digest) == 64
    assert fingerprint(token, key) != fingerprint(token, b"b" * 32)


def test_pkce_uses_rfc7636_s256() -> None:
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"  # pragma: allowlist secret
    assert pkce_challenge(verifier) == (
        "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"  # pragma: allowlist secret
    )


def test_example_hmac_key_encoding_is_256_bits() -> None:
    assert len(base64.urlsafe_b64decode(base64.urlsafe_b64encode(b"k" * 32))) == 32


def test_production_authentication_requires_https() -> None:
    with pytest.raises(ConfigurationError, match="must use HTTPS"):
        load_auth_settings(
            {
                "P5_SERVICE_NAME": "auth",
                "P5_DATABASE_URL": "postgresql://db/auth",
                "P5_OIDC_ISSUER": "http://oidc.test",
                "P5_OIDC_CLIENT_ID": "client",
                "P5_OIDC_CLIENT_SECRET": TEST_SECRET,
                "P5_OIDC_REDIRECT_URI": "http://gateway.test/callback",
                "P5_DESKTOP_CALLBACK_URI": "pentagon5://auth/callback",
                "P5_SESSION_HMAC_KEY": base64.urlsafe_b64encode(b"k" * 32).decode(),
            }
        )


def test_authentication_secrets_support_file_sources(tmp_path: Path) -> None:
    client_secret = tmp_path / "client-secret"
    session_key = tmp_path / "session-key"
    client_secret.write_text(f"{PROVIDER_SECRET}\n", encoding="utf-8")
    session_key.write_text(base64.urlsafe_b64encode(b"k" * 32).decode(), encoding="utf-8")
    loaded = load_auth_settings(
        {
            "P5_ENVIRONMENT": "test",
            "P5_SERVICE_NAME": "auth",
            "P5_DATABASE_URL": "postgresql://db/auth",
            "P5_OIDC_ISSUER": "http://oidc.test",
            "P5_OIDC_CLIENT_ID": "client",
            "P5_OIDC_CLIENT_SECRET_FILE": str(client_secret),
            "P5_OIDC_REDIRECT_URI": "http://gateway.test/callback",
            "P5_DESKTOP_CALLBACK_URI": "pentagon5://auth/callback",
            "P5_SESSION_HMAC_KEY_FILE": str(session_key),
        }
    )
    assert loaded.client_secret == PROVIDER_SECRET
    assert loaded.hmac_key == b"k" * 32


def test_uuid7_has_expected_version_variant_and_canonical_form() -> None:
    value = uuid7()
    assert value.version == 7
    assert value.variant == "specified in RFC 4122"
    assert is_uuid7(str(value))
    assert str(value) == str(value).lower()


def test_uuid7_generation_is_monotonically_sortable() -> None:
    values = [uuid7() for _ in range(1000)]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_production_json_logging_redacts_secrets_and_stack_traces() -> None:
    configure_logging(environment="production")
    record = logging.LogRecord(
        "security",
        logging.ERROR,
        __file__,
        1,
        "authorization=Bearer abc.secret token=raw-token",
        (),
        (ValueError, ValueError("secret"), None),
    )
    payload = json.loads(JsonFormatter().format(record))
    assert "abc.secret" not in payload["message"]
    assert "raw-token" not in payload["message"]
    assert "exception" not in payload


def test_runtime_configuration_rejects_wildcard_cors() -> None:
    with pytest.raises(ConfigurationError, match="exact HTTP"):
        load_runtime_settings(
            {
                "P5_SERVICE_NAME": "api",
                "P5_DATABASE_URL": "postgresql://db/api",
                "P5_CORS_ORIGINS": "*",
            }
        )


def test_authentication_rejects_non_exact_desktop_callback() -> None:
    with pytest.raises(ConfigurationError, match="exact custom URI"):
        load_auth_settings(
            {
                "P5_ENVIRONMENT": "test",
                "P5_SERVICE_NAME": "auth",
                "P5_DATABASE_URL": "postgresql://db/auth",
                "P5_OIDC_ISSUER": "http://oidc.test",
                "P5_OIDC_CLIENT_ID": "client",
                "P5_OIDC_CLIENT_SECRET": TEST_SECRET,
                "P5_OIDC_REDIRECT_URI": "http://gateway.test/callback",
                "P5_DESKTOP_CALLBACK_URI": "pentagon5://auth/callback?next=unsafe",
                "P5_SESSION_HMAC_KEY": base64.urlsafe_b64encode(b"k" * 32).decode(),
            }
        )
