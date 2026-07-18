# ADR 0003: PostgreSQL Is the Authoritative Store

- Status: Accepted
- Date: 2026-07-18

## Context

The platform needs one durable source of truth for identity, personalization,
workspaces, operational health, market observations, trading state, risk
controls, reconciliation, and audit history. Trading and financial data require
transactional integrity, exact decimal arithmetic, and enforceable
relationships.

## Decision

PostgreSQL is the authoritative persistent store. SQLAlchemy Core metadata in
`infrastructure/database/metadata.py` describes the relational model. Alembic
is the only schema migration mechanism; PostgreSQL init scripts are not used.
Each Alembic revision runs with transactional DDL.

The model is divided into bounded PostgreSQL schemas: `identity`,
`personalization`, `workspace`, `operations`, `market`, `trading`, and `audit`.
Cross-domain references are explicit foreign keys.

All instants use `timestamp with time zone`; applications must submit and
interpret them as UTC. Financial, price, and quantity values use fixed
`numeric` precision. Floating-point columns are prohibited for those values.
Risk configuration is mandatory trading policy and is separate from user
preferences. Audit events are append-only and protected by a database trigger.

No credentials, tokens, API keys, or broker secrets are persisted by this
model. Session rows store only a non-reversible token fingerprint.

## Consequences

- PostgreSQL-specific types and behavior are intentional.
- Database constraints remain authoritative when application validation is
  bypassed.
- Changes to persistent state require reviewed Alembic revisions.
- Integration tests require a PostgreSQL role able to create and drop temporary
  databases.
