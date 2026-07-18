"""Structural checks for the Milestone 2 JSON Schema source of truth."""

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "packages/shared-types/schemas/v1"
EVENTS = ROOT / "packages/event-contracts/schemas/v1"

REQUIRED_DOMAINS = {
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


JsonObject = dict[str, Any]


def load(path: Path) -> JsonObject:
    return cast(JsonObject, json.loads(path.read_text()))


def test_all_schemas_are_valid_draft_2020_12() -> None:
    schemas = [load(path) for path in (*SHARED.glob("*.json"), *EVENTS.glob("*.json"))]
    assert schemas
    for schema in schemas:
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)


def test_all_required_domains_are_defined() -> None:
    definitions = load(SHARED / "domain.schema.json")["$defs"]
    assert REQUIRED_DOMAINS <= definitions.keys()


def test_contract_uses_immutable_v1_schema_version() -> None:
    common = load(SHARED / "common.schema.json")
    assert common["$defs"]["SchemaVersion"]["const"] == "1.0.0"


def test_order_commands_require_client_idempotency_keys() -> None:
    definitions = load(EVENTS / "message.schema.json")["$defs"]
    for command in ("PlaceOrder", "CancelOrder", "ClosePosition"):
        assert "idempotencyKey" in definitions[command]["required"]
    assert "clientOrderId" in definitions["PlaceOrder"]["required"]


def test_manual_broker_exit_is_a_structured_reconciliation_outcome() -> None:
    definitions = load(SHARED / "domain.schema.json")["$defs"]
    assert "ManualBrokerExit" in definitions
    outcome = definitions["ReconciliationOutcome"]
    assert "manual_broker_exit" in outcome["properties"]["kind"]["enum"]
    assert outcome["properties"]["manualExit"]["$ref"] == "#/$defs/ManualBrokerExit"
