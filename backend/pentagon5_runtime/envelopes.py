"""Builders for accepted Milestone 2 message envelopes."""

from __future__ import annotations

from datetime import UTC, datetime

from pentagon5_runtime.uuid7 import uuid7


def utc_z(now: datetime | None = None) -> str:
    """Format an aware timestamp as RFC 3339 UTC with a Z suffix."""
    value = now or datetime.now(UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def error_envelope(
    correlation_id: str,
    *,
    code: str,
    message: str,
    retryable: bool,
    field: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    if field:
        payload["field"] = field
    return _base("error", correlation_id, payload)


def health_envelope(
    correlation_id: str,
    *,
    component: str,
    status: str,
    detail: str | None = None,
) -> dict[str, object]:
    observed_at = utc_z()
    payload: dict[str, object] = {
        "schemaVersion": "1.0.0",
        "id": str(uuid7()),
        "component": component,
        "status": status,
        "observedAt": observed_at,
    }
    if detail:
        payload["detail"] = detail
    return _base("health", correlation_id, payload, occurred_at=observed_at)


def websocket_envelope(
    correlation_id: str,
    *,
    operation: str,
    channel: str,
    subscription_id: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"operation": operation, "channel": channel}
    if subscription_id:
        payload["subscriptionId"] = subscription_id
    return _base("websocket", correlation_id, payload)


def _base(
    category: str,
    correlation_id: str,
    payload: dict[str, object],
    *,
    occurred_at: str | None = None,
) -> dict[str, object]:
    return {
        "schemaVersion": "1.0.0",
        "messageId": str(uuid7()),
        "category": category,
        "occurredAt": occurred_at or utc_z(),
        "metadata": {"correlationId": correlation_id},
        "payload": payload,
    }
