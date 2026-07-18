"""Monotonic RFC 9562 UUIDv7 generation."""

from __future__ import annotations

import secrets
import threading
import time
import uuid

_LOCK = threading.Lock()
_LAST_MILLISECOND = -1
_LAST_RANDOM = 0
_RANDOM_MASK = (1 << 74) - 1


def uuid7() -> uuid.UUID:
    """Return a lowercase, time-ordered UUIDv7.

    Values generated in one process are monotonically increasing, including
    calls made during the same millisecond or after a small clock rollback.
    """
    global _LAST_MILLISECOND, _LAST_RANDOM
    with _LOCK:
        millisecond = time.time_ns() // 1_000_000
        if millisecond > _LAST_MILLISECOND:
            random_bits = secrets.randbits(74)
        else:
            millisecond = _LAST_MILLISECOND
            random_bits = (_LAST_RANDOM + 1) & _RANDOM_MASK
            if random_bits == 0:
                millisecond += 1
        _LAST_MILLISECOND = millisecond
        _LAST_RANDOM = random_bits
    random_a = random_bits >> 62
    random_b = random_bits & ((1 << 62) - 1)
    value = (millisecond & ((1 << 48) - 1)) << 80 | 7 << 76 | random_a << 64 | 2 << 62 | random_b
    return uuid.UUID(int=value)


def is_uuid7(value: str) -> bool:
    """Return whether value is a canonical lowercase RFC 9562 UUIDv7."""
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return False
    return str(parsed) == value and parsed.version == 7 and parsed.variant == uuid.RFC_4122
