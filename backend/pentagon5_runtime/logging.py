"""JSON structured logging with request correlation and secret redaction."""

from __future__ import annotations

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_INCLUDE_EXCEPTIONS = False
_REDACTED_KEYS = {
    "authorization",
    "cookie",
    "id_token",
    "password",
    "refresh_token",
    "secret",
    "session",
    "token",
}
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]+")
_NAMED_SECRET = re.compile(r"(?i)\b(token|secret|password|authorization|cookie)=([^&\s]+)")


def _safe(value: Any, key: str = "") -> Any:
    if any(fragment in key.lower() for fragment in _REDACTED_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): _safe(item, str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    """Format records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _safe_message(record.getMessage()),
        }
        correlation_id = request_id.get()
        if correlation_id:
            payload["request_id"] = correlation_id
        details = getattr(record, "details", None)
        if details is not None:
            payload["details"] = _safe(details)
        if record.exc_info and _INCLUDE_EXCEPTIONS:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _safe_message(message: str) -> str:
    redacted = _BEARER.sub("Bearer [REDACTED]", message)
    return _NAMED_SECRET.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)


def configure_logging(level: str = "INFO", *, environment: str = "production") -> None:
    """Install the structured formatter on the process root logger."""
    global _INCLUDE_EXCEPTIONS
    _INCLUDE_EXCEPTIONS = environment in {"development", "test"}
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
