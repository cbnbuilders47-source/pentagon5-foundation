"""Validation and security invariants for the separate auth contract package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from pentagon5_runtime.envelopes import error_envelope, health_envelope, websocket_envelope
from pentagon5_runtime.uuid7 import uuid7
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
AUTH_SCHEMA = ROOT / "packages/auth-contracts/schemas/v1/auth.schema.json"
COMMON_SCHEMA = ROOT / "packages/shared-types/schemas/v1/common.schema.json"
DOMAIN_SCHEMA = ROOT / "packages/shared-types/schemas/v1/domain.schema.json"
MESSAGE_SCHEMA = ROOT / "packages/event-contracts/schemas/v1/message.schema.json"


def load(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


COMMON = load(COMMON_SCHEMA)
DOMAIN = load(DOMAIN_SCHEMA)
MESSAGE = load(MESSAGE_SCHEMA)
AUTH = load(AUTH_SCHEMA)
REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in (COMMON, DOMAIN, MESSAGE, AUTH)
)


def validator(reference: str) -> Draft202012Validator:
    return Draft202012Validator(
        {"$ref": reference},
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )


def test_auth_contract_is_valid_and_versioned_separately() -> None:
    Draft202012Validator.check_schema(AUTH)
    assert AUTH["$id"] == "https://schemas.pentagon5.dev/auth/v1/auth.schema.json"


def test_auth_contract_limits_websocket_channels() -> None:
    channels = AUTH["$defs"]["websocketTicketRequest"]["properties"]["channel"]["enum"]
    assert channels == ["system.health", "session.events"]


def test_auth_contract_never_exposes_session_tokens() -> None:
    schema_text = AUTH_SCHEMA.read_text(encoding="utf-8")
    assert "access_token" not in schema_text
    assert "refresh_token" not in schema_text
    assert "password" not in schema_text


def test_auth_uuid_fields_use_common_uuidv7_contract() -> None:
    session = {
        "user_id": str(uuid7()),
        "session_id": str(uuid7()),
        "email": "user@example.test",
        "display_name": "User",
        "roles": [],
        "permissions": [],
        "expires_at": "2026-07-18T12:00:00Z",
    }
    session_validator = validator(f"{AUTH['$id']}#/$defs/session")
    session_validator.validate(session)
    session["user_id"] = "550e8400-e29b-41d4-a716-446655440000"
    with pytest.raises(ValidationError):
        session_validator.validate(session)


def test_runtime_error_health_and_websocket_envelopes_match_registry() -> None:
    correlation_id = str(uuid7())
    instances = (
        (
            "Error",
            error_envelope(
                correlation_id,
                code="SESSION_INVALID",
                message="Session is invalid",
                retryable=False,
            ),
        ),
        (
            "Health",
            health_envelope(
                correlation_id,
                component="api",
                status="healthy",
            ),
        ),
        (
            "WebSocket",
            websocket_envelope(
                correlation_id,
                operation="ack",
                channel="system.health",
                subscription_id=str(uuid7()),
            ),
        ),
    )
    for definition, instance in instances:
        validator(f"{MESSAGE['$id']}#/$defs/{definition}").validate(instance)
