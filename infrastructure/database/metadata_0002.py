"""Immutable SQLAlchemy metadata snapshot for identity migration 0002."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)
UUID_TYPE = UUID(as_uuid=True)
UTC_TIMESTAMP = DateTime(timezone=True)
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


def _id() -> Column[Any]:
    return Column("id", UUID_TYPE, primary_key=True)


# Reference-only declarations let this immutable snapshot compile foreign keys.
users = Table("users", metadata, _id(), schema="identity")
sessions = Table("sessions", metadata, _id(), schema="identity")

oidc_identities = Table(
    "oidc_identities",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("issuer", String(512), nullable=False),
    Column("subject", String(512), nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("issuer", "subject", name="uq_oidc_identity_issuer_subject"),
    schema="identity",
)
oidc_flows = Table(
    "oidc_flows",
    metadata,
    _id(),
    Column("state_fingerprint", String(64), nullable=False, unique=True),
    Column("encrypted_payload", Text, nullable=False),
    Column("redirect_uri", Text, nullable=False),
    Column("expires_at", UTC_TIMESTAMP, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)
login_grants = Table(
    "login_grants",
    metadata,
    _id(),
    Column("code_fingerprint", String(64), nullable=False, unique=True),
    Column("encrypted_payload", Text, nullable=False),
    Column("expires_at", UTC_TIMESTAMP, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)
websocket_tickets = Table(
    "websocket_tickets",
    metadata,
    _id(),
    Column("ticket_fingerprint", String(64), nullable=False, unique=True),
    Column(
        "session_id",
        UUID_TYPE,
        ForeignKey("identity.sessions.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("channel", String(32), nullable=False),
    Column("expires_at", UTC_TIMESTAMP, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    CheckConstraint(
        "channel IN ('system.health', 'session.events')",
        name="channel",
    ),
    schema="identity",
)
session_events = Table(
    "session_events",
    metadata,
    _id(),
    Column("session_id", UUID_TYPE, ForeignKey("identity.sessions.id", ondelete="CASCADE")),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("event_type", String(80), nullable=False),
    Column("payload", JSON_TYPE, nullable=False, server_default="{}"),
    Column("occurred_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)

Index("ix_identity_oidc_identities_user_id", oidc_identities.c.user_id)
Index("ix_identity_oidc_flows_expires_at", oidc_flows.c.expires_at)
Index("ix_identity_login_grants_expires_at", login_grants.c.expires_at)
Index("ix_identity_websocket_tickets_expires_at", websocket_tickets.c.expires_at)
Index(
    "ix_identity_session_events_user_occurred",
    session_events.c.user_id,
    session_events.c.occurred_at,
)

ADDITION_TABLES = (
    oidc_identities,
    oidc_flows,
    login_grants,
    websocket_tickets,
    session_events,
)
