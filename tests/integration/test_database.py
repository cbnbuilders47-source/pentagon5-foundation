"""PostgreSQL integration coverage for the database workstream."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from itertools import count
from pathlib import Path
from typing import Any

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from psycopg import sql
from sqlalchemy.engine import make_url

test_database_url = os.environ.get("TEST_DATABASE_URL")
if not test_database_url:
    pytest.skip(
        "TEST_DATABASE_URL is absent; PostgreSQL integration tests require it",
        allow_module_level=True,
    )
TEST_DATABASE_URL: str = test_database_url

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "infrastructure" / "database" / "alembic.ini"
SEED_SQL = ROOT / "infrastructure" / "database" / "seed.development.sql"
SCHEMAS = {
    "identity",
    "personalization",
    "workspace",
    "operations",
    "market",
    "trading",
    "audit",
}
EXPECTED_TABLES = {
    "audit.events",
    "identity.devices",
    "identity.login_grants",
    "identity.oidc_flows",
    "identity.oidc_identities",
    "identity.permissions",
    "identity.role_permissions",
    "identity.roles",
    "identity.session_events",
    "identity.sessions",
    "identity.user_roles",
    "identity.users",
    "identity.websocket_tickets",
    "market.instruments",
    "market.market_feed_health_events",
    "market.quotes",
    "market.signals",
    "operations.server_connections",
    "operations.system_health_events",
    "personalization.background_assets",
    "personalization.dashboard_layouts",
    "personalization.notification_events",
    "personalization.notification_preferences",
    "personalization.sound_assets",
    "personalization.sound_preferences",
    "personalization.themes",
    "personalization.user_preferences",
    "trading.broker_health",
    "trading.executions",
    "trading.manual_broker_exits",
    "trading.mode_transitions",
    "trading.orders",
    "trading.pnl",
    "trading.positions",
    "trading.reconciliation_states",
    "trading.risk_configurations",
    "trading.risk_states",
    "trading.trading_modes",
    "workspace.workspace_members",
    "workspace.workspaces",
}

USER_ID = uuid.UUID("018f1000-0000-7000-8000-000000000001")
WORKSPACE_ID = uuid.UUID("018f1000-0000-7000-8000-000000000002")
INSTRUMENT_ID = uuid.UUID("018f1000-0000-7000-8000-000000000003")
UUID_SEQUENCE = count(100)


def _uuid7() -> uuid.UUID:
    return uuid.UUID(f"018f1000-0000-7000-8000-{next(UUID_SEQUENCE):012x}")


def _psycopg_url(url: str, database: str | None = None) -> str:
    parsed = make_url(url)
    psycopg_url = parsed.set(
        database=database or parsed.database or "postgres",
        drivername="postgresql",
    )
    return psycopg_url.render_as_string(hide_password=False)


def _migration_url(url: str, database: str) -> str:
    parsed = make_url(url).set(database=database, drivername="postgresql+psycopg")
    return parsed.render_as_string(hide_password=False)


def _alembic(url: str) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    config.attributes["database_url"] = url
    return config


@contextmanager
def temporary_database(*, migrated: bool = True) -> Iterator[tuple[str, str]]:
    database = f"p5_test_{uuid.uuid4().hex}"
    admin_url = _psycopg_url(TEST_DATABASE_URL)
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))

    database_url = _migration_url(TEST_DATABASE_URL, database)
    try:
        if migrated:
            command.upgrade(_alembic(database_url), "head")
        yield database, database_url
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (database,),
            )
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database)))


def _connect(database: str, *, autocommit: bool = False) -> psycopg.Connection[Any]:
    return psycopg.connect(
        _psycopg_url(TEST_DATABASE_URL, database),
        autocommit=autocommit,
    )


def _required_value(row: tuple[Any, ...] | None) -> Any:
    assert row is not None
    return row[0]


def _insert_prerequisites(connection: psycopg.Connection[Any]) -> None:
    connection.execute(
        "INSERT INTO identity.users (id, email, display_name) VALUES (%s, %s, %s)",
        (USER_ID, "integration@example.test", "Integration User"),
    )
    connection.execute(
        """
        INSERT INTO workspace.workspaces (id, name, owner_user_id)
        VALUES (%s, %s, %s)
        """,
        (WORKSPACE_ID, "Integration Workspace", USER_ID),
    )
    connection.execute(
        """
        INSERT INTO market.instruments (
            id, symbol, venue, asset_class, currency,
            price_increment, quantity_increment
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (INSTRUMENT_ID, "TEST", "SIM", "equity", "USD", Decimal("0.01"), Decimal("0.001")),
    )
    connection.commit()


def test_empty_upgrade_creates_bounded_schemas_and_tables() -> None:
    with temporary_database(migrated=False) as (database, database_url):
        command.upgrade(_alembic(database_url), "head")
        with _connect(database) as connection:
            schemas = {
                row[0]
                for row in connection.execute("SELECT schema_name FROM information_schema.schemata")
            }
            assert SCHEMAS <= schemas
            tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT table_schema || '.' || table_name
                    FROM information_schema.tables
                    WHERE table_schema = ANY(%s)
                    """,
                    (list(SCHEMAS),),
                )
            }
            assert tables == EXPECTED_TABLES


def test_domain_tables_exclude_secret_and_credential_columns() -> None:
    with temporary_database() as (database, _):
        with _connect(database) as connection:
            forbidden = list(
                connection.execute(
                    """
                    SELECT table_schema, table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = ANY(%s)
                      AND column_name ~ %s
                    """,
                    (
                        list(SCHEMAS),
                        "password|secret|credential|api_key|private_key|access_token|refresh_token",
                    ),
                )
            )
            assert forbidden == []


def test_downgrade_removes_all_bounded_schemas() -> None:
    with temporary_database() as (database, database_url):
        command.downgrade(_alembic(database_url), "base")
        with _connect(database) as connection:
            remaining = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = ANY(%s)
                    """,
                    (list(SCHEMAS),),
                )
            }
            assert remaining == set()


def test_migrations_are_repeatable() -> None:
    with temporary_database(migrated=False) as (database, database_url):
        config = _alembic(database_url)
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        with _connect(database) as connection:
            assert (
                _required_value(
                    connection.execute("SELECT count(*) FROM alembic_version").fetchone()
                )
                == 1
            )


def test_constraints_idempotency_and_invalid_states() -> None:
    with temporary_database() as (database, _):
        with _connect(database) as connection:
            _insert_prerequisites(connection)
            order_values = (
                _uuid7(),
                WORKSPACE_ID,
                INSTRUMENT_ID,
                "client-a",
                "retry-key",
                "buy",
                "market",
                "pending",
                Decimal("1.000000000000"),
            )
            connection.execute(
                """
                INSERT INTO trading.orders (
                    id, workspace_id, instrument_id, client_id,
                    idempotency_key, side, order_type, status, quantity
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                order_values,
            )
            connection.commit()

            with pytest.raises(psycopg.errors.UniqueViolation):
                connection.execute(
                    """
                    INSERT INTO trading.orders (
                        id, workspace_id, instrument_id, client_id,
                        idempotency_key, side, order_type, status, quantity
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (_uuid7(), *order_values[1:]),
                )
            connection.rollback()

            with pytest.raises(psycopg.errors.CheckViolation):
                connection.execute(
                    """
                    INSERT INTO trading.trading_modes (
                        workspace_id, mode, changed_by_user_id
                    ) VALUES (%s, 'reckless', %s)
                    """,
                    (WORKSPACE_ID, USER_ID),
                )
            connection.rollback()

            with pytest.raises(psycopg.errors.CheckViolation):
                connection.execute(
                    """
                    INSERT INTO trading.mode_transitions (
                        id, workspace_id, from_mode, to_mode,
                        requested_by_user_id, reason
                    )
                    VALUES (%s, %s, 'observation', 'live', %s, 'unsafe jump')
                    """,
                    (_uuid7(), WORKSPACE_ID, USER_ID),
                )
            connection.rollback()

            with pytest.raises(psycopg.errors.CheckViolation):
                connection.execute(
                    """
                    INSERT INTO trading.risk_configurations (
                        id, workspace_id, max_order_notional,
                        max_position_notional, daily_loss_limit,
                        max_open_orders, base_currency, created_by_user_id
                    )
                    VALUES (%s, %s, -1, 100, 10, 1, 'USD', %s)
                    """,
                    (_uuid7(), WORKSPACE_ID, USER_ID),
                )
            connection.rollback()


def test_decimal_precision_and_no_floating_financial_columns() -> None:
    with temporary_database() as (database, _):
        with _connect(database) as connection:
            _insert_prerequisites(connection)
            order_id = _uuid7()
            quantity = Decimal("1234.123456789012")
            price = Decimal("98765.123456789012")
            connection.execute(
                """
                INSERT INTO trading.orders (
                    id, workspace_id, instrument_id, client_id,
                    idempotency_key, side, order_type, status,
                    quantity, limit_price
                )
                VALUES (%s, %s, %s, 'precision-client', 'precision-key',
                        'buy', 'limit', 'pending', %s, %s)
                """,
                (order_id, WORKSPACE_ID, INSTRUMENT_ID, quantity, price),
            )
            connection.commit()
            stored = connection.execute(
                "SELECT quantity, limit_price FROM trading.orders WHERE id = %s",
                (order_id,),
            ).fetchone()
            assert stored == (quantity, price)
            floating = connection.execute(
                """
                SELECT table_schema, table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = ANY(%s)
                  AND data_type IN ('real', 'double precision')
                """,
                (list(SCHEMAS),),
            ).fetchall()
            assert floating == []


def test_timestamptz_values_are_read_in_utc() -> None:
    with temporary_database() as (database, _):
        with _connect(database) as connection:
            _insert_prerequisites(connection)
            connection.execute("SET TIME ZONE 'UTC'")
            supplied = datetime(
                2026, 7, 18, 23, 45, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))
            )
            quote_id = _uuid7()
            connection.execute(
                """
                INSERT INTO market.quotes (
                    id, instrument_id, last_price, source, observed_at
                ) VALUES (%s, %s, 10.25, 'integration', %s)
                """,
                (quote_id, INSTRUMENT_ID, supplied),
            )
            connection.commit()
            stored = _required_value(
                connection.execute(
                    "SELECT observed_at FROM market.quotes WHERE id = %s",
                    (quote_id,),
                ).fetchone()
            )
            assert stored.utcoffset() == timedelta(0)
            assert stored == supplied.astimezone(UTC)


def test_development_seed_is_gated_and_idempotent() -> None:
    seed = SEED_SQL.read_text(encoding="utf-8")
    with temporary_database() as (database, _):
        with _connect(database, autocommit=True) as connection:
            with pytest.raises(psycopg.errors.RaiseException):
                connection.execute(seed)
            connection.execute("ROLLBACK")

            connection.execute("SET app.environment = 'development'")
            connection.execute(seed)
            connection.execute(seed)
            count = _required_value(
                connection.execute(
                    """
                    SELECT count(*) FROM identity.users
                    WHERE id = '018f0000-0000-7000-8000-000000000001'
                    """
                ).fetchone()
            )
            assert count == 1
            health_permission = _required_value(
                connection.execute(
                    """
                    SELECT count(*) FROM identity.permissions
                    WHERE code = 'system.health.read'
                    """
                ).fetchone()
            )
            assert health_permission == 1
            sound_preferences = _required_value(
                connection.execute(
                    """
                    SELECT count(*) FROM personalization.sound_preferences
                    WHERE id = '018f0000-0000-7000-8000-000000000013'
                    """
                ).fetchone()
            )
            assert sound_preferences == 1


def test_audit_events_are_append_only() -> None:
    with temporary_database() as (database, _):
        with _connect(database) as connection:
            _insert_prerequisites(connection)
            event_id = _uuid7()
            connection.execute(
                """
                INSERT INTO audit.events (
                    id, workspace_id, actor_user_id, event_type,
                    aggregate_type, aggregate_id, payload
                )
                VALUES (%s, %s, %s, 'order.requested', 'order', %s, '{}')
                """,
                (event_id, WORKSPACE_ID, USER_ID, _uuid7()),
            )
            connection.commit()

            with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
                connection.execute(
                    "UPDATE audit.events SET event_type = 'changed' WHERE id = %s",
                    (event_id,),
                )
            connection.rollback()

            with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
                connection.execute("DELETE FROM audit.events WHERE id = %s", (event_id,))
            connection.rollback()

            with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
                connection.execute("TRUNCATE audit.events")
            connection.rollback()
            assert (
                _required_value(
                    connection.execute(
                        "SELECT count(*) FROM audit.events WHERE id = %s",
                        (event_id,),
                    ).fetchone()
                )
                == 1
            )
