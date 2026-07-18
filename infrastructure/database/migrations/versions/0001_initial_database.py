"""Create the initial bounded PostgreSQL schemas.

Revision ID: 0001_initial_database
Revises:
Create Date: 2026-07-18
"""

from __future__ import annotations

from alembic import op

from infrastructure.database.metadata_0001 import metadata

revision = "0001_initial_database"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = (
    "identity",
    "personalization",
    "workspace",
    "operations",
    "market",
    "trading",
    "audit",
)


def upgrade() -> None:
    bind = op.get_bind()
    for schema in SCHEMAS:
        op.execute(f'CREATE SCHEMA "{schema}"')
    metadata.create_all(bind=bind, checkfirst=False)
    op.execute(
        """
        CREATE FUNCTION audit.reject_event_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit.events is append-only';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit.events
        FOR EACH ROW EXECUTE FUNCTION audit.reject_event_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_events_reject_truncate
        BEFORE TRUNCATE ON audit.events
        FOR EACH STATEMENT EXECUTE FUNCTION audit.reject_event_mutation()
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP TRIGGER IF EXISTS audit_events_reject_truncate ON audit.events")
    op.execute("DROP TRIGGER IF EXISTS audit_events_append_only ON audit.events")
    op.execute("DROP FUNCTION IF EXISTS audit.reject_event_mutation()")
    metadata.drop_all(bind=bind, checkfirst=False)
    for schema in reversed(SCHEMAS):
        op.execute(f'DROP SCHEMA "{schema}"')
