"""PostgreSQL persistence for authentication and global RBAC."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from pentagon5_runtime.uuid7 import uuid7
from sqlalchemy import Connection, Engine, RowMapping, text

from pentagon5_auth.models import Device, Flow, Identity, Principal


class AuthRepository(Protocol):
    """Storage boundary used by the authentication domain service."""

    def put_flow(
        self, fingerprint: str, encrypted_payload: str, redirect_uri: str, expires_at: datetime
    ) -> None: ...

    def consume_flow(self, fingerprint: str, now: datetime) -> Flow | None: ...

    def put_login_grant(
        self, fingerprint: str, encrypted_payload: str, expires_at: datetime
    ) -> None: ...

    def consume_login_grant(self, fingerprint: str, now: datetime) -> str | None: ...

    def provision_identity(self, identity: Identity) -> uuid.UUID: ...

    def register_device(
        self, user_id: uuid.UUID, device_fingerprint: str, platform: str, now: datetime
    ) -> uuid.UUID: ...

    def create_session(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        token_fingerprint: str,
        expires_at: datetime,
    ) -> uuid.UUID: ...

    def resolve_session(self, token_fingerprint: str, now: datetime) -> Principal | None: ...

    def revoke_session(self, session_id: uuid.UUID, now: datetime) -> None: ...

    def list_devices(self, user_id: uuid.UUID) -> Sequence[Device]: ...

    def revoke_device(self, user_id: uuid.UUID, device_id: uuid.UUID, now: datetime) -> bool: ...

    def put_ws_ticket(
        self,
        ticket_fingerprint: str,
        session_id: uuid.UUID,
        channel: str,
        expires_at: datetime,
    ) -> None: ...

    def consume_ws_ticket(
        self, ticket_fingerprint: str, channel: str, now: datetime
    ) -> uuid.UUID | None: ...


class PostgresAuthRepository:
    """Transactional SQLAlchemy Core implementation."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def put_flow(
        self, fingerprint: str, encrypted_payload: str, redirect_uri: str, expires_at: datetime
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.oidc_flows
                        (id, state_fingerprint, encrypted_payload, redirect_uri, expires_at)
                    VALUES (:id, :fingerprint, :payload, :redirect_uri, :expires_at)
                    """
                ),
                {
                    "id": uuid7(),
                    "fingerprint": fingerprint,
                    "payload": encrypted_payload,
                    "redirect_uri": redirect_uri,
                    "expires_at": expires_at,
                },
            )

    def consume_flow(self, fingerprint: str, now: datetime) -> Flow | None:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    DELETE FROM identity.oidc_flows
                    WHERE state_fingerprint = :fingerprint AND expires_at > :now
                    RETURNING encrypted_payload, redirect_uri
                    """
                    ),
                    {"fingerprint": fingerprint, "now": now},
                )
                .mappings()
                .one_or_none()
            )
        return (
            None if row is None else Flow(str(row["encrypted_payload"]), str(row["redirect_uri"]))
        )

    def put_login_grant(
        self, fingerprint: str, encrypted_payload: str, expires_at: datetime
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.login_grants
                        (id, code_fingerprint, encrypted_payload, expires_at)
                    VALUES (:id, :fingerprint, :payload, :expires_at)
                    """
                ),
                {
                    "id": uuid7(),
                    "fingerprint": fingerprint,
                    "payload": encrypted_payload,
                    "expires_at": expires_at,
                },
            )

    def consume_login_grant(self, fingerprint: str, now: datetime) -> str | None:
        with self._engine.begin() as connection:
            value = connection.execute(
                text(
                    """
                    DELETE FROM identity.login_grants
                    WHERE code_fingerprint = :fingerprint AND expires_at > :now
                    RETURNING encrypted_payload
                    """
                ),
                {"fingerprint": fingerprint, "now": now},
            ).scalar_one_or_none()
        return None if value is None else str(value)

    def provision_identity(self, identity: Identity) -> uuid.UUID:
        with self._engine.begin() as connection:
            existing = connection.execute(
                text(
                    """
                    SELECT user_id FROM identity.oidc_identities
                    WHERE issuer = :issuer AND subject = :subject
                    """
                ),
                {"issuer": identity.issuer, "subject": identity.subject},
            ).scalar_one_or_none()
            if existing is None:
                user_id = uuid7()
                connection.execute(
                    text(
                        """
                        INSERT INTO identity.users (id, email, display_name)
                        VALUES (:id, :email, :display_name)
                        """
                    ),
                    {
                        "id": user_id,
                        "email": identity.email,
                        "display_name": identity.display_name,
                    },
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO identity.oidc_identities
                            (id, user_id, issuer, subject)
                        VALUES (:id, :user_id, :issuer, :subject)
                        """
                    ),
                    {
                        "id": uuid7(),
                        "user_id": user_id,
                        "issuer": identity.issuer,
                        "subject": identity.subject,
                    },
                )
            else:
                user_id = uuid.UUID(str(existing))
                connection.execute(
                    text(
                        """
                        UPDATE identity.users
                        SET email = :email, display_name = :display_name, updated_at = now()
                        WHERE id = :id AND status = 'active'
                        """
                    ),
                    {
                        "id": user_id,
                        "email": identity.email,
                        "display_name": identity.display_name,
                    },
                )
        return user_id

    def register_device(
        self, user_id: uuid.UUID, device_fingerprint: str, platform: str, now: datetime
    ) -> uuid.UUID:
        with self._engine.begin() as connection:
            device_id = connection.execute(
                text(
                    """
                    INSERT INTO identity.devices
                        (id, user_id, device_key, platform, last_seen_at)
                    VALUES (:id, :user_id, :device_key, :platform, :now)
                    ON CONFLICT (user_id, device_key) DO UPDATE
                    SET platform = EXCLUDED.platform, last_seen_at = EXCLUDED.last_seen_at,
                        revoked_at = NULL, updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "id": uuid7(),
                    "user_id": user_id,
                    "device_key": device_fingerprint,
                    "platform": platform,
                    "now": now,
                },
            ).scalar_one()
        return uuid.UUID(str(device_id))

    def create_session(
        self,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        token_fingerprint: str,
        expires_at: datetime,
    ) -> uuid.UUID:
        session_id = uuid7()
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.sessions
                        (id, user_id, device_id, token_fingerprint, expires_at)
                    VALUES (:id, :user_id, :device_id, :fingerprint, :expires_at)
                    """
                ),
                {
                    "id": session_id,
                    "user_id": user_id,
                    "device_id": device_id,
                    "fingerprint": token_fingerprint,
                    "expires_at": expires_at,
                },
            )
            self._event(connection, session_id, user_id, "session.created", {})
        return session_id

    def resolve_session(self, token_fingerprint: str, now: datetime) -> Principal | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT s.id session_id, s.user_id, s.device_id, s.expires_at,
                           u.email, u.display_name
                    FROM identity.sessions s
                    JOIN identity.users u ON u.id = s.user_id
                    LEFT JOIN identity.devices d ON d.id = s.device_id
                    WHERE s.token_fingerprint = :fingerprint
                      AND s.revoked_at IS NULL AND s.expires_at > :now
                      AND u.status = 'active'
                      AND (d.id IS NULL OR d.revoked_at IS NULL)
                    """
                    ),
                    {"fingerprint": token_fingerprint, "now": now},
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            roles = tuple(
                connection.execute(
                    text(
                        """
                        SELECT r.name FROM identity.roles r
                        JOIN identity.user_roles ur ON ur.role_id = r.id
                        WHERE ur.user_id = :user_id ORDER BY r.name
                        """
                    ),
                    {"user_id": row["user_id"]},
                ).scalars()
            )
            permissions = frozenset(
                connection.execute(
                    text(
                        """
                        SELECT DISTINCT p.code FROM identity.permissions p
                        JOIN identity.role_permissions rp ON rp.permission_id = p.id
                        JOIN identity.user_roles ur ON ur.role_id = rp.role_id
                        WHERE ur.user_id = :user_id
                        """
                    ),
                    {"user_id": row["user_id"]},
                ).scalars()
            )
        return self._principal(row, roles, permissions)

    def revoke_session(self, session_id: uuid.UUID, now: datetime) -> None:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE identity.sessions SET revoked_at = :now
                    WHERE id = :id AND revoked_at IS NULL RETURNING user_id
                    """
                ),
                {"id": session_id, "now": now},
            ).one_or_none()
            if row is not None:
                self._event(connection, session_id, uuid.UUID(str(row[0])), "session.revoked", {})

    def list_devices(self, user_id: uuid.UUID) -> Sequence[Device]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, platform, last_seen_at, revoked_at
                    FROM identity.devices WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    """
                ),
                {"user_id": user_id},
            ).mappings()
            return [
                Device(
                    uuid.UUID(str(row["id"])),
                    str(row["platform"]),
                    row["last_seen_at"],
                    row["revoked_at"],
                )
                for row in rows
            ]

    def revoke_device(self, user_id: uuid.UUID, device_id: uuid.UUID, now: datetime) -> bool:
        with self._engine.begin() as connection:
            changed = connection.execute(
                text(
                    """
                    UPDATE identity.devices SET revoked_at = :now, updated_at = :now
                    WHERE id = :device_id AND user_id = :user_id AND revoked_at IS NULL
                    RETURNING id
                    """
                ),
                {"now": now, "device_id": device_id, "user_id": user_id},
            ).one_or_none()
            if changed is not None:
                connection.execute(
                    text(
                        """
                        UPDATE identity.sessions SET revoked_at = :now
                        WHERE device_id = :device_id AND revoked_at IS NULL
                        """
                    ),
                    {"now": now, "device_id": device_id},
                )
        return changed is not None

    def put_ws_ticket(
        self,
        ticket_fingerprint: str,
        session_id: uuid.UUID,
        channel: str,
        expires_at: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.websocket_tickets
                        (id, ticket_fingerprint, session_id, channel, expires_at)
                    VALUES (:id, :fingerprint, :session_id, :channel, :expires_at)
                    """
                ),
                {
                    "id": uuid7(),
                    "fingerprint": ticket_fingerprint,
                    "session_id": session_id,
                    "channel": channel,
                    "expires_at": expires_at,
                },
            )

    def consume_ws_ticket(
        self, ticket_fingerprint: str, channel: str, now: datetime
    ) -> uuid.UUID | None:
        with self._engine.begin() as connection:
            session_id = connection.execute(
                text(
                    """
                    DELETE FROM identity.websocket_tickets wt
                    USING identity.sessions s
                    WHERE wt.session_id = s.id
                      AND wt.ticket_fingerprint = :fingerprint
                      AND wt.channel = :channel
                      AND wt.expires_at > :now
                      AND s.revoked_at IS NULL AND s.expires_at > :now
                    RETURNING wt.session_id
                    """
                ),
                {"fingerprint": ticket_fingerprint, "channel": channel, "now": now},
            ).scalar_one_or_none()
        return None if session_id is None else uuid.UUID(str(session_id))

    @staticmethod
    def _principal(
        row: RowMapping, roles: tuple[str, ...], permissions: frozenset[str]
    ) -> Principal:
        return Principal(
            user_id=uuid.UUID(str(row["user_id"])),
            session_id=uuid.UUID(str(row["session_id"])),
            device_id=None if row["device_id"] is None else uuid.UUID(str(row["device_id"])),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            roles=roles,
            permissions=permissions,
            expires_at=row["expires_at"],
        )

    @staticmethod
    def _event(
        connection: Connection,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO identity.session_events
                    (id, session_id, user_id, event_type, payload)
                VALUES (:id, :session_id, :user_id, :event_type, CAST(:payload AS jsonb))
                """
            ),
            {
                "id": uuid7(),
                "session_id": session_id,
                "user_id": user_id,
                "event_type": event_type,
                "payload": json.dumps(payload, separators=(",", ":")),
            },
        )
