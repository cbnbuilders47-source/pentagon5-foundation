"""Add OIDC identities, transient flows, session events, and WebSocket tickets.

Revision ID: 0002_identity_authentication
Revises: 0001_initial_database
Create Date: 2026-07-18
"""

from __future__ import annotations

from alembic import op

from infrastructure.database.metadata_0002 import ADDITION_TABLES

revision = "0002_identity_authentication"
down_revision = "0001_initial_database"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    for table in ADDITION_TABLES:
        table.create(bind=bind, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(ADDITION_TABLES):
        table.drop(bind=bind, checkfirst=False)
