# Database Entity Map

## Objectives

Define the authoritative PostgreSQL entities through authorized Milestone 3.
Migration `0002` adds identity-runtime persistence without authorizing trading
or other product runtimes.

## Files

`infrastructure/database/metadata.py` is the current model.
`metadata_0001.py` is the immutable initial-migration snapshot, and
`migrations/versions/0001_initial_database.py` applies it transactionally.
`metadata_0002.py` is the immutable additive identity snapshot, and
`migrations/versions/0002_identity_authentication.py` applies it.

## Commands

Use `make database-test`, `make database-migrate`, `make database-seed`, and
`make database-downgrade` from the repository root.

## Tests

Integration tests create isolated temporary databases and verify upgrade,
downgrade, repeat migration, constraints, precision, UTC behavior, development
seeding, append-only audit records, and the additive `0002` lifecycle.

## Results

The entity map contains seven bounded schemas:

- `identity`: `users`, `roles`, `permissions`, `user_roles`,
  `role_permissions`, `devices`, `sessions`, `oidc_identities`, `oidc_flows`,
  `login_grants`, `websocket_tickets`, and `session_events`.
- `personalization`: `themes`, `background_assets`, `sound_assets`,
  `user_preferences`, `sound_preferences`, `notification_preferences`,
  `notification_events`, and `dashboard_layouts`.
- `workspace`: `workspaces` and `workspace_members`.
- `operations`: `server_connections` and `system_health_events`.
- `market`: `instruments`, `quotes`, `signals`, and
  `market_feed_health_events`.
- `trading`: `trading_modes`, `mode_transitions`, `risk_configurations`,
  `risk_states`, `orders`, `executions`, `positions`, `pnl`,
  `broker_health`, `manual_broker_exits`, and `reconciliation_states`.
- `audit`: append-only `events`.

Migration `0002` stores only provider identity links, authenticated-encrypted
transient OIDC and grant payloads, HMAC fingerprints, expiry metadata,
channel-bound tickets, and session events. Foreign keys enforce bounded
relationships; structural trading tables remain authorization-neutral and do
not imply an implemented trading runtime.

## Known issues

Future service-specific database roles, grants, retention policies,
partitioning, and production backup policy require later authorization.

## Security

No password, API key, broker credential, plaintext session token, grant code,
OIDC state, ticket, or signing secret is stored. Session and transient lookup
rows retain keyed HMAC fingerprints; transient payloads are
authenticated-encrypted. Audit events reject update, delete, and truncate
operations.

## Acceptance

All financial values use fixed-precision `numeric`; identifiers use UUID
storage with application-generated UUIDv7 contracts; timestamps use
`timestamptz`. Focused migration and identity tests passed during
implementation; final full Milestone 3 acceptance remains pending.

## Next milestone

Milestone 4 is not authorized. This map does not authorize broker, market,
strategy, order, execution, risk, reconciliation, or AI runtimes.
