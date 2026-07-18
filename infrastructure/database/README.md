# Database Infrastructure

PostgreSQL is the authoritative store. SQLAlchemy Core metadata defines seven
bounded schemas and Alembic owns their lifecycle. Do not use PostgreSQL init
scripts as a migration mechanism.

## Layout

- `metadata.py`: authoritative SQLAlchemy Core tables, constraints, and indexes.
- `metadata_0001.py`: immutable metadata snapshot consumed by migration 0001.
- `metadata_0002.py`: immutable identity/authentication additions for migration 0002.
- `alembic.ini`: Alembic configuration.
- `migrations/`: transactional migration environment and revisions.
- `seed.development.sql`: deterministic, idempotent mock data for development.

## Migrations

Provide a psycopg SQLAlchemy URL through `DATABASE_URL`:

```sh
DATABASE_URL=postgresql+psycopg://postgres@localhost/pentagon5 \
  alembic -c infrastructure/database/alembic.ini upgrade head
```

Downgrade the initial migration with:

```sh
DATABASE_URL=postgresql+psycopg://postgres@localhost/pentagon5 \
  alembic -c infrastructure/database/alembic.ini downgrade base
```

Alembic is configured for transactional PostgreSQL DDL. The initial revision
creates and removes all bounded schemas, tables, indexes, constraints, and the
append-only audit trigger. Existing migration snapshots are immutable; every
later schema change requires a new revision and a new reviewed snapshot.

Revision 0002 adds OIDC subject bindings, encrypted transient authorization
flows, encrypted single-use native login grants, one-time WebSocket ticket
fingerprints, and session events. Existing
session/device/RBAC tables are reused; no plaintext session value or provider
credential is persisted.

## Development seed

The seed contains only structural and mock data. It has deterministic UUIDs and
uses conflict handling so repeated execution has no effect. It refuses to run
unless the database session is explicitly marked as development:

```sh
PGOPTIONS='-c app.environment=development' \
  psql "$PSQL_DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f infrastructure/database/seed.development.sql
```

`PSQL_DATABASE_URL` is a native `postgresql://` URI (without SQLAlchemy's
`+psycopg` driver suffix). The parent development commands must set the gate.
Never set it in production. The seed does not contain credentials, API keys,
tokens, or broker secrets.

## Data rules

- IDs are application-generated UUIDv7 values; PostgreSQL has no ID defaults.
- All timestamps are `timestamp with time zone` and are handled as UTC.
- Monetary values, prices, and quantities use fixed-precision `numeric`; no
  floating-point financial storage is allowed.
- Risk configuration and runtime risk state are trading controls, not user
  preferences.
- `audit.events` accepts inserts but rejects updates and deletes.

## Integration tests

Set `TEST_DATABASE_URL` to an existing PostgreSQL database. The role must have
`CREATE DATABASE` and termination/drop privileges. Tests create uniquely named
temporary databases, run migrations against them, and always attempt cleanup.
If `TEST_DATABASE_URL` is absent, the database integration module is skipped
with an explicit reason.
