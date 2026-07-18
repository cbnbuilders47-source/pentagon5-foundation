"""Immutable SQLAlchemy metadata snapshot for migration 0001."""

from __future__ import annotations

from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
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
MONEY = Numeric(24, 8)
PRICE = Numeric(28, 12)
QUANTITY = Numeric(28, 12)
JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


def _id() -> Column[Any]:
    return Column("id", UUID_TYPE, primary_key=True)


def _timestamps() -> tuple[Column[Any], Column[Any]]:
    return (
        Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
        Column("updated_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    )


def _state_check(column: str, values: tuple[str, ...], name: str) -> CheckConstraint:
    allowed = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)


users = Table(
    "users",
    metadata,
    _id(),
    Column("email", String(320), nullable=False, unique=True),
    Column("display_name", String(120), nullable=False),
    Column("status", String(24), nullable=False, server_default="active"),
    *_timestamps(),
    _state_check("status", ("active", "disabled", "deleted"), "status"),
    schema="identity",
)
roles = Table(
    "roles",
    metadata,
    _id(),
    Column("name", String(80), nullable=False, unique=True),
    Column("description", Text),
    *_timestamps(),
    schema="identity",
)
permissions = Table(
    "permissions",
    metadata,
    _id(),
    Column("code", String(120), nullable=False, unique=True),
    Column("description", Text),
    *_timestamps(),
    schema="identity",
)
user_roles = Table(
    "user_roles",
    metadata,
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", UUID_TYPE, ForeignKey("identity.roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)
role_permissions = Table(
    "role_permissions",
    metadata,
    Column(
        "role_id", UUID_TYPE, ForeignKey("identity.roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        UUID_TYPE,
        ForeignKey("identity.permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)
devices = Table(
    "devices",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("device_key", String(200), nullable=False),
    Column("platform", String(40), nullable=False),
    Column("last_seen_at", UTC_TIMESTAMP),
    Column("revoked_at", UTC_TIMESTAMP),
    *_timestamps(),
    UniqueConstraint("user_id", "device_key", name="uq_devices_user_device"),
    schema="identity",
)
sessions = Table(
    "sessions",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("device_id", UUID_TYPE, ForeignKey("identity.devices.id", ondelete="SET NULL")),
    Column("token_fingerprint", String(128), nullable=False, unique=True),
    Column("expires_at", UTC_TIMESTAMP, nullable=False),
    Column("revoked_at", UTC_TIMESTAMP),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="identity",
)

themes = Table(
    "themes",
    metadata,
    _id(),
    Column("name", String(80), nullable=False, unique=True),
    Column("definition", JSON_TYPE, nullable=False),
    Column("is_system", Boolean, nullable=False, server_default="false"),
    *_timestamps(),
    schema="personalization",
)
background_assets = Table(
    "background_assets",
    metadata,
    _id(),
    Column("name", String(80), nullable=False, unique=True),
    Column("asset_uri", Text, nullable=False),
    Column("is_system", Boolean, nullable=False, server_default="false"),
    *_timestamps(),
    schema="personalization",
)
sound_assets = Table(
    "sound_assets",
    metadata,
    _id(),
    Column("name", String(80), nullable=False, unique=True),
    Column("asset_uri", Text, nullable=False),
    Column("is_system", Boolean, nullable=False, server_default="false"),
    *_timestamps(),
    schema="personalization",
)
user_preferences = Table(
    "user_preferences",
    metadata,
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("theme_id", UUID_TYPE, ForeignKey("personalization.themes.id", ondelete="SET NULL")),
    Column(
        "background_id",
        UUID_TYPE,
        ForeignKey("personalization.background_assets.id", ondelete="SET NULL"),
    ),
    Column(
        "sound_id", UUID_TYPE, ForeignKey("personalization.sound_assets.id", ondelete="SET NULL")
    ),
    Column("locale", String(16), nullable=False, server_default="en-US"),
    Column("timezone", String(64), nullable=False, server_default="UTC"),
    Column("settings", JSON_TYPE, nullable=False, server_default="{}"),
    *_timestamps(),
    schema="personalization",
)
sound_preferences = Table(
    "sound_preferences",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("event_type", String(80), nullable=False),
    Column(
        "sound_asset_id",
        UUID_TYPE,
        ForeignKey("personalization.sound_assets.id", ondelete="SET NULL"),
    ),
    Column("enabled", Boolean, nullable=False, server_default="true"),
    Column("volume", Numeric(4, 3), nullable=False, server_default="1.000"),
    *_timestamps(),
    UniqueConstraint("user_id", "event_type", name="uq_sound_preference"),
    CheckConstraint("volume >= 0 AND volume <= 1", name="volume_range"),
    schema="personalization",
)
notification_preferences = Table(
    "notification_preferences",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("channel", String(24), nullable=False),
    Column("event_type", String(80), nullable=False),
    Column("enabled", Boolean, nullable=False, server_default="true"),
    *_timestamps(),
    UniqueConstraint("user_id", "channel", "event_type", name="uq_notification_preference"),
    _state_check("channel", ("in_app", "email", "push", "sms"), "channel"),
    schema="personalization",
)
notification_events = Table(
    "notification_events",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("event_type", String(80), nullable=False),
    Column("payload", JSON_TYPE, nullable=False),
    Column("occurred_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    Column("read_at", UTC_TIMESTAMP),
    schema="personalization",
)
dashboard_layouts = Table(
    "dashboard_layouts",
    metadata,
    _id(),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False
    ),
    Column("name", String(100), nullable=False),
    Column("layout", JSON_TYPE, nullable=False),
    Column("is_default", Boolean, nullable=False, server_default="false"),
    *_timestamps(),
    UniqueConstraint("user_id", "name", name="uq_dashboard_user_name"),
    schema="personalization",
)

workspaces = Table(
    "workspaces",
    metadata,
    _id(),
    Column("name", String(120), nullable=False),
    Column(
        "owner_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("status", String(24), nullable=False, server_default="active"),
    *_timestamps(),
    _state_check("status", ("active", "suspended", "archived"), "status"),
    schema="workspace",
)
workspace_members = Table(
    "workspace_members",
    metadata,
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("member_role", String(24), nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check("member_role", ("owner", "admin", "trader", "viewer"), "member_role"),
    schema="workspace",
)

server_connections = Table(
    "server_connections",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("connection_type", String(40), nullable=False),
    Column("endpoint_label", String(120), nullable=False),
    Column("status", String(24), nullable=False),
    Column("last_connected_at", UTC_TIMESTAMP),
    Column("last_disconnected_at", UTC_TIMESTAMP),
    Column("details", JSON_TYPE, nullable=False, server_default="{}"),
    *_timestamps(),
    _state_check("status", ("unknown", "connected", "degraded", "disconnected"), "status"),
    UniqueConstraint(
        "workspace_id", "connection_type", "endpoint_label", name="uq_server_connection"
    ),
    schema="operations",
)
system_health_events = Table(
    "system_health_events",
    metadata,
    _id(),
    Column(
        "server_connection_id",
        UUID_TYPE,
        ForeignKey("operations.server_connections.id", ondelete="CASCADE"),
    ),
    Column("component", String(120), nullable=False),
    Column("status", String(24), nullable=False),
    Column("latency_ms", Integer),
    Column("details", JSON_TYPE, nullable=False, server_default="{}"),
    Column("observed_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check("status", ("healthy", "degraded", "unhealthy", "unknown"), "status"),
    CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="latency_nonnegative"),
    schema="operations",
)

instruments = Table(
    "instruments",
    metadata,
    _id(),
    Column("symbol", String(40), nullable=False),
    Column("venue", String(40), nullable=False),
    Column("asset_class", String(32), nullable=False),
    Column("currency", String(3), nullable=False),
    Column("price_increment", PRICE, nullable=False),
    Column("quantity_increment", QUANTITY, nullable=False),
    Column("active", Boolean, nullable=False, server_default="true"),
    *_timestamps(),
    UniqueConstraint("symbol", "venue", name="uq_instrument_symbol_venue"),
    CheckConstraint("price_increment > 0", name="positive_price_increment"),
    CheckConstraint("quantity_increment > 0", name="positive_quantity_increment"),
    schema="market",
)
quotes = Table(
    "quotes",
    metadata,
    _id(),
    Column(
        "instrument_id",
        UUID_TYPE,
        ForeignKey("market.instruments.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("bid_price", PRICE),
    Column("ask_price", PRICE),
    Column("last_price", PRICE),
    Column("bid_quantity", QUANTITY),
    Column("ask_quantity", QUANTITY),
    Column("source", String(80), nullable=False),
    Column("observed_at", UTC_TIMESTAMP, nullable=False),
    Column("received_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    CheckConstraint("bid_price IS NULL OR bid_price >= 0", name="bid_nonnegative"),
    CheckConstraint("ask_price IS NULL OR ask_price >= 0", name="ask_nonnegative"),
    CheckConstraint("last_price IS NULL OR last_price >= 0", name="last_nonnegative"),
    schema="market",
)
signals = Table(
    "signals",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "instrument_id",
        UUID_TYPE,
        ForeignKey("market.instruments.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("signal_type", String(40), nullable=False),
    Column("strength", Numeric(10, 6), nullable=False),
    Column("payload", JSON_TYPE, nullable=False, server_default="{}"),
    Column("generated_at", UTC_TIMESTAMP, nullable=False),
    Column("expires_at", UTC_TIMESTAMP),
    CheckConstraint("strength >= -1 AND strength <= 1", name="strength_range"),
    schema="market",
)
market_feed_health_events = Table(
    "market_feed_health_events",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("feed_name", String(100), nullable=False),
    Column("status", String(24), nullable=False),
    Column("last_message_at", UTC_TIMESTAMP),
    Column("observed_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    Column("details", JSON_TYPE, nullable=False, server_default="{}"),
    _state_check("status", ("healthy", "degraded", "down", "unknown"), "status"),
    schema="market",
)

trading_modes = Table(
    "trading_modes",
    metadata,
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("mode", String(24), nullable=False, server_default="observation"),
    Column(
        "changed_by_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("changed_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    Column("version", Integer, nullable=False, server_default="1"),
    _state_check("mode", ("observation", "paper", "small_live", "live", "emergency"), "mode"),
    CheckConstraint("version > 0", name="positive_version"),
    schema="trading",
)
mode_transitions = Table(
    "mode_transitions",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("from_mode", String(24), nullable=False),
    Column("to_mode", String(24), nullable=False),
    Column(
        "requested_by_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("reason", Text, nullable=False),
    Column("transitioned_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check(
        "from_mode", ("observation", "paper", "small_live", "live", "emergency"), "from_mode"
    ),
    _state_check("to_mode", ("observation", "paper", "small_live", "live", "emergency"), "to_mode"),
    CheckConstraint("from_mode <> to_mode", name="mode_changes"),
    CheckConstraint(
        """
        (from_mode = 'observation' AND to_mode IN ('paper', 'emergency'))
        OR (from_mode = 'paper' AND to_mode IN ('observation', 'small_live', 'emergency'))
        OR (from_mode = 'small_live' AND to_mode IN ('paper', 'live', 'emergency'))
        OR (from_mode = 'live' AND to_mode IN ('small_live', 'emergency'))
        OR (from_mode = 'emergency' AND to_mode = 'observation')
        """,
        name="allowed_transition",
    ),
    schema="trading",
)
risk_configurations = Table(
    "risk_configurations",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("max_order_notional", MONEY, nullable=False),
    Column("max_position_notional", MONEY, nullable=False),
    Column("daily_loss_limit", MONEY, nullable=False),
    Column("max_open_orders", Integer, nullable=False),
    Column("base_currency", String(3), nullable=False),
    Column("effective_from", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    Column("effective_to", UTC_TIMESTAMP),
    Column(
        "created_by_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    CheckConstraint("max_order_notional > 0", name="positive_order_limit"),
    CheckConstraint("max_position_notional > 0", name="positive_position_limit"),
    CheckConstraint("daily_loss_limit > 0", name="positive_loss_limit"),
    CheckConstraint("max_open_orders > 0", name="positive_open_orders"),
    CheckConstraint(
        "effective_to IS NULL OR effective_to > effective_from", name="effective_window"
    ),
    schema="trading",
)
risk_states = Table(
    "risk_states",
    metadata,
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "risk_configuration_id",
        UUID_TYPE,
        ForeignKey("trading.risk_configurations.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("state", String(24), nullable=False),
    Column("daily_realized_pnl", MONEY, nullable=False, server_default="0"),
    Column("open_order_count", Integer, nullable=False, server_default="0"),
    Column("reason", Text),
    Column("evaluated_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check("state", ("normal", "warning", "blocked", "emergency"), "state"),
    CheckConstraint("open_order_count >= 0", name="open_orders_nonnegative"),
    schema="trading",
)
orders = Table(
    "orders",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "instrument_id",
        UUID_TYPE,
        ForeignKey("market.instruments.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("client_id", String(100), nullable=False),
    Column("idempotency_key", String(200), nullable=False),
    Column("broker_order_id", String(160)),
    Column("side", String(8), nullable=False),
    Column("order_type", String(24), nullable=False),
    Column("status", String(24), nullable=False),
    Column("quantity", QUANTITY, nullable=False),
    Column("limit_price", PRICE),
    Column("stop_price", PRICE),
    Column("time_in_force", String(16), nullable=False, server_default="day"),
    Column("submitted_at", UTC_TIMESTAMP),
    Column("cancelled_at", UTC_TIMESTAMP),
    *_timestamps(),
    UniqueConstraint("workspace_id", "client_id", "idempotency_key", name="uq_order_idempotency"),
    _state_check("side", ("buy", "sell"), "side"),
    _state_check("order_type", ("market", "limit", "stop", "stop_limit"), "order_type"),
    _state_check(
        "status",
        ("pending", "submitted", "partially_filled", "filled", "cancelled", "rejected"),
        "status",
    ),
    CheckConstraint("quantity > 0", name="positive_quantity"),
    CheckConstraint("limit_price IS NULL OR limit_price > 0", name="positive_limit_price"),
    CheckConstraint("stop_price IS NULL OR stop_price > 0", name="positive_stop_price"),
    schema="trading",
)
executions = Table(
    "executions",
    metadata,
    _id(),
    Column(
        "order_id", UUID_TYPE, ForeignKey("trading.orders.id", ondelete="RESTRICT"), nullable=False
    ),
    Column("broker_execution_id", String(160), nullable=False),
    Column("quantity", QUANTITY, nullable=False),
    Column("price", PRICE, nullable=False),
    Column("commission", MONEY, nullable=False, server_default="0"),
    Column("executed_at", UTC_TIMESTAMP, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("order_id", "broker_execution_id", name="uq_execution_broker"),
    CheckConstraint("quantity > 0", name="positive_quantity"),
    CheckConstraint("price > 0", name="positive_price"),
    CheckConstraint("commission >= 0", name="commission_nonnegative"),
    schema="trading",
)
positions = Table(
    "positions",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "instrument_id",
        UUID_TYPE,
        ForeignKey("market.instruments.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("quantity", QUANTITY, nullable=False),
    Column("average_price", PRICE, nullable=False),
    Column("market_price", PRICE),
    Column("as_of", UTC_TIMESTAMP, nullable=False),
    *_timestamps(),
    UniqueConstraint("workspace_id", "instrument_id", name="uq_position_workspace_instrument"),
    CheckConstraint("average_price >= 0", name="average_price_nonnegative"),
    CheckConstraint("market_price IS NULL OR market_price >= 0", name="market_price_nonnegative"),
    schema="trading",
)
pnl = Table(
    "pnl",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("instrument_id", UUID_TYPE, ForeignKey("market.instruments.id", ondelete="SET NULL")),
    Column("realized", MONEY, nullable=False, server_default="0"),
    Column("unrealized", MONEY, nullable=False, server_default="0"),
    Column("currency", String(3), nullable=False),
    Column("as_of", UTC_TIMESTAMP, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    UniqueConstraint("workspace_id", "instrument_id", "as_of", name="uq_pnl_snapshot"),
    schema="trading",
)
broker_health = Table(
    "broker_health",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("broker_name", String(100), nullable=False),
    Column("status", String(24), nullable=False),
    Column("last_heartbeat_at", UTC_TIMESTAMP),
    Column("observed_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    Column("details", JSON_TYPE, nullable=False, server_default="{}"),
    _state_check("status", ("healthy", "degraded", "down", "unknown"), "status"),
    schema="trading",
)
manual_broker_exits = Table(
    "manual_broker_exits",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "instrument_id",
        UUID_TYPE,
        ForeignKey("market.instruments.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column(
        "reported_by_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("broker_reference", String(160), nullable=False),
    Column("side", String(8), nullable=False),
    Column("quantity", QUANTITY, nullable=False),
    Column("price", PRICE, nullable=False),
    Column("executed_at", UTC_TIMESTAMP, nullable=False),
    Column("reason", Text, nullable=False),
    Column("created_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check("side", ("buy", "sell"), "side"),
    CheckConstraint("quantity > 0", name="positive_quantity"),
    CheckConstraint("price > 0", name="positive_price"),
    UniqueConstraint("workspace_id", "broker_reference", name="uq_manual_exit_reference"),
    schema="trading",
)
reconciliation_states = Table(
    "reconciliation_states",
    metadata,
    _id(),
    Column(
        "workspace_id",
        UUID_TYPE,
        ForeignKey("workspace.workspaces.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "manual_broker_exit_id",
        UUID_TYPE,
        ForeignKey("trading.manual_broker_exits.id", ondelete="SET NULL"),
    ),
    Column("outcome", String(24), nullable=False),
    Column("differences", JSON_TYPE, nullable=False, server_default="{}"),
    Column("notes", Text),
    Column(
        "reconciled_by_user_id",
        UUID_TYPE,
        ForeignKey("identity.users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("reconciled_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    _state_check("outcome", ("matched", "adjusted", "unresolved", "ignored"), "outcome"),
    schema="trading",
)

audit_events = Table(
    "events",
    metadata,
    _id(),
    Column("workspace_id", UUID_TYPE, ForeignKey("workspace.workspaces.id", ondelete="SET NULL")),
    Column("actor_user_id", UUID_TYPE, ForeignKey("identity.users.id", ondelete="SET NULL")),
    Column("event_type", String(120), nullable=False),
    Column("aggregate_type", String(80), nullable=False),
    Column("aggregate_id", UUID_TYPE),
    Column("payload", JSON_TYPE, nullable=False),
    Column("occurred_at", UTC_TIMESTAMP, nullable=False, server_default=func.now()),
    schema="audit",
)

Index("ix_identity_devices_user_id", devices.c.user_id)
Index("ix_identity_sessions_user_id_expires", sessions.c.user_id, sessions.c.expires_at)
Index(
    "ix_personalization_notification_events_user_occurred",
    notification_events.c.user_id,
    notification_events.c.occurred_at,
)
Index("ix_workspace_members_user_id", workspace_members.c.user_id)
Index(
    "ix_operations_health_checks_component_observed",
    system_health_events.c.component,
    system_health_events.c.observed_at,
)
Index("ix_market_quotes_instrument_observed", quotes.c.instrument_id, quotes.c.observed_at)
Index("ix_market_signals_workspace_generated", signals.c.workspace_id, signals.c.generated_at)
Index(
    "ix_market_feed_health_workspace_observed",
    market_feed_health_events.c.workspace_id,
    market_feed_health_events.c.observed_at,
)
Index(
    "ix_trading_mode_transitions_workspace_time",
    mode_transitions.c.workspace_id,
    mode_transitions.c.transitioned_at,
)
Index(
    "ix_trading_risk_configurations_workspace_effective",
    risk_configurations.c.workspace_id,
    risk_configurations.c.effective_from,
)
Index("ix_trading_orders_workspace_status", orders.c.workspace_id, orders.c.status)
Index("ix_trading_executions_order_time", executions.c.order_id, executions.c.executed_at)
Index(
    "ix_trading_broker_health_workspace_observed",
    broker_health.c.workspace_id,
    broker_health.c.observed_at,
)
Index(
    "ix_trading_reconciliation_workspace_time",
    reconciliation_states.c.workspace_id,
    reconciliation_states.c.reconciled_at,
)
Index("ix_audit_events_workspace_occurred", audit_events.c.workspace_id, audit_events.c.occurred_at)
Index("ix_audit_events_aggregate", audit_events.c.aggregate_type, audit_events.c.aggregate_id)
