# Database Entity Map

## Objectives

Define the authoritative Milestone 2 PostgreSQL entities, ownership schemas,
and permitted relationships without authorizing a service implementation.

## Files

`infrastructure/database/metadata.py` is the current model.
`metadata_0001.py` is the immutable initial-migration snapshot, and
`migrations/versions/0001_initial_database.py` applies it transactionally.

## Commands

Use `make database-test`, `make database-migrate`, `make database-seed`, and
`make database-downgrade` from the repository root.

## Tests

Integration tests create isolated temporary databases and verify upgrade,
downgrade, repeat migration, constraints, precision, UTC behavior, development
seeding, and append-only audit records.

## Results

The entity map contains seven bounded schemas:

- `identity`: `users`, `roles`, `permissions`, `user_roles`,
  `role_permissions`, `devices`, and `sessions`.
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

Foreign keys enforce identity, workspace, instrument, order, position, risk,
and reconciliation relationships. Cross-schema references are structural
integrity controls, not permission for future services to write another
boundary's tables.

## Known issues

Future service-specific database roles, grants, retention policies,
partitioning, and production backup policy require later authorization.

## Security

No password, API key, broker credential, session token, or signing secret is
stored. Session rows retain only a non-reversible token fingerprint. Audit
events reject update, delete, and truncate operations.

## Acceptance

All financial values use fixed-precision `numeric`; identifiers use UUID
storage with application-generated UUIDv7 contracts; timestamps use
`timestamptz`; trading modes explicitly include observation, paper,
small-live, live, and emergency.

## Next milestone

Milestone 3 remains unauthorized. This map does not authorize authentication,
service repositories, broker access, market feeds, strategies, or order
placement.
