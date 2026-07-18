"""Internal authentication domain models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Flow:
    """A consumed, encrypted OIDC authorization transaction."""

    encrypted_payload: str
    redirect_uri: str


@dataclass(frozen=True, slots=True)
class Identity:
    """Validated provider identity claims."""

    issuer: str
    subject: str
    email: str
    display_name: str


@dataclass(frozen=True, slots=True)
class Principal:
    """A current global authorization principal."""

    user_id: uuid.UUID
    session_id: uuid.UUID
    device_id: uuid.UUID | None
    email: str
    display_name: str
    roles: tuple[str, ...]
    permissions: frozenset[str]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SessionGrant:
    """A newly-issued opaque session and its public metadata."""

    token: str
    principal: Principal


@dataclass(frozen=True, slots=True)
class LoginRedirect:
    """Desktop redirect containing only a one-time login code."""

    code: str
    redirect_uri: str


@dataclass(frozen=True, slots=True)
class Device:
    """A registered client device."""

    id: uuid.UUID
    platform: str
    last_seen_at: datetime | None
    revoked_at: datetime | None
