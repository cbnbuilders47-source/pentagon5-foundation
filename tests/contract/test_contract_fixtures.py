"""Validate positive, negative, and frozen-v1 contract fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
COMMON_PATH = ROOT / "packages/shared-types/schemas/v1/common.schema.json"
DOMAIN_PATH = ROOT / "packages/shared-types/schemas/v1/domain.schema.json"
MESSAGE_PATH = ROOT / "packages/event-contracts/schemas/v1/message.schema.json"
FIXTURES = ROOT / "packages/test-fixtures"
JsonObject = dict[str, Any]


def load(path: Path) -> Any:
    return json.loads(path.read_text())


COMMON = load(COMMON_PATH)
DOMAIN = load(DOMAIN_PATH)
MESSAGE = load(MESSAGE_PATH)

REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in (COMMON, DOMAIN, MESSAGE)
)


def validator(schema: JsonObject) -> Draft202012Validator:
    return Draft202012Validator(
        schema,
        registry=REGISTRY,
        format_checker=FormatChecker(),
    )


def test_every_required_domain_has_a_valid_fixture() -> None:
    fixtures = load(FIXTURES / "valid/domains.json")
    assert fixtures.keys() == {
        "User",
        "Role",
        "Permission",
        "Device",
        "Session",
        "UserPreference",
        "Theme",
        "BackgroundAsset",
        "SoundPreference",
        "NotificationPreference",
        "NotificationEvent",
        "DashboardLayout",
        "Workspace",
        "SystemHealthEvent",
        "AuditEvent",
        "TradingMode",
        "ServerConnection",
        "Instrument",
        "Quote",
        "Signal",
        "Order",
        "Execution",
        "Position",
        "P&L",
        "RiskState",
        "BrokerHealth",
        "MarketFeedHealth",
        "ReconciliationState",
    }
    for name, instance in fixtures.items():
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": f"{DOMAIN['$id']}#/$defs/{name}",
        }
        validator(schema).validate(instance)


def test_valid_message_fixture_covers_every_category() -> None:
    messages = load(FIXTURES / "valid/messages.json")
    assert {message["category"] for message in messages} == {
        "command",
        "query",
        "response",
        "error",
        "domain_event",
        "health",
        "websocket",
        "audit",
    }
    for message in messages:
        validator(MESSAGE).validate(message)


def test_contract_messages_round_trip_without_numeric_coercion() -> None:
    messages = load(FIXTURES / "valid/messages.json")
    encoded = json.dumps(messages, sort_keys=True, separators=(",", ":"))
    assert json.loads(encoded) == messages
    order = next(message for message in messages if message["category"] == "command")
    assert isinstance(order["payload"]["quantity"], str)
    assert isinstance(order["payload"]["limitPrice"], str)


def test_domain_event_envelope_carries_trace_and_sequence_metadata() -> None:
    messages = load(FIXTURES / "valid/messages.json")
    event = next(message for message in messages if message["category"] == "domain_event")
    validator(MESSAGE).validate(event)
    assert event["metadata"]["correlationId"]
    assert event["metadata"]["causationId"]
    assert event["payload"]["sequence"] == 1
    assert event["payload"]["aggregateId"]


@pytest.mark.parametrize(
    "fixture", load(FIXTURES / "invalid/messages.json"), ids=lambda item: item["case"]
)
def test_invalid_messages_are_rejected(fixture: JsonObject) -> None:
    with pytest.raises(ValidationError):
        validator(MESSAGE).validate(fixture["instance"])


def test_frozen_v1_fixture_remains_valid() -> None:
    fixture = load(FIXTURES / "backward-compatible/v1.0.0.json")
    validator(MESSAGE).validate(fixture)
