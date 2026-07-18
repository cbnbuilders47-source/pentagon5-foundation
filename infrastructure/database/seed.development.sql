BEGIN;

DO $$
BEGIN
    IF current_setting('app.environment', true) IS DISTINCT FROM 'development' THEN
        RAISE EXCEPTION
            'development seed refused: set app.environment=development for this session';
    END IF;
END;
$$;

INSERT INTO identity.users (id, email, display_name)
VALUES ('018f0000-0000-7000-8000-000000000001', 'developer@example.test', 'Development User')
ON CONFLICT (id) DO NOTHING;

INSERT INTO identity.roles (id, name, description)
VALUES ('018f0000-0000-7000-8000-000000000002', 'developer', 'Development-only operator role')
ON CONFLICT (id) DO NOTHING;

INSERT INTO identity.permissions (id, code, description)
VALUES ('018f0000-0000-7000-8000-000000000003', 'workspace.manage', 'Manage a workspace')
ON CONFLICT (id) DO NOTHING;

INSERT INTO identity.permissions (id, code, description)
VALUES (
    '018f0000-0000-7000-8000-000000000004',
    'system.health.read',
    'Read system health over authenticated transports'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO identity.user_roles (user_id, role_id)
VALUES (
    '018f0000-0000-7000-8000-000000000001',
    '018f0000-0000-7000-8000-000000000002'
)
ON CONFLICT DO NOTHING;

INSERT INTO identity.role_permissions (role_id, permission_id)
VALUES (
    '018f0000-0000-7000-8000-000000000002',
    '018f0000-0000-7000-8000-000000000003'
)
ON CONFLICT DO NOTHING;

INSERT INTO identity.role_permissions (role_id, permission_id)
VALUES (
    '018f0000-0000-7000-8000-000000000002',
    '018f0000-0000-7000-8000-000000000004'
)
ON CONFLICT DO NOTHING;

INSERT INTO personalization.themes (id, name, definition, is_system)
VALUES (
    '018f0000-0000-7000-8000-000000000010',
    'Development Dark',
    '{"palette": "dark"}'::jsonb,
    true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO personalization.background_assets (id, name, asset_uri, is_system)
VALUES (
    '018f0000-0000-7000-8000-000000000011',
    'Development Grid',
    'mock://background/grid',
    true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO personalization.sound_assets (id, name, asset_uri, is_system)
VALUES (
    '018f0000-0000-7000-8000-000000000012',
    'Development Chime',
    'mock://sound/chime',
    true
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO personalization.user_preferences (
    user_id, theme_id, background_id, sound_id, locale, timezone
)
VALUES (
    '018f0000-0000-7000-8000-000000000001',
    '018f0000-0000-7000-8000-000000000010',
    '018f0000-0000-7000-8000-000000000011',
    '018f0000-0000-7000-8000-000000000012',
    'en-US',
    'UTC'
)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO personalization.sound_preferences (
    id, user_id, event_type, sound_asset_id, enabled, volume
)
VALUES (
    '018f0000-0000-7000-8000-000000000013',
    '018f0000-0000-7000-8000-000000000001',
    'order.status',
    '018f0000-0000-7000-8000-000000000012',
    true,
    0.750
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO workspace.workspaces (id, name, owner_user_id)
VALUES (
    '018f0000-0000-7000-8000-000000000020',
    'Development Workspace',
    '018f0000-0000-7000-8000-000000000001'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO workspace.workspace_members (workspace_id, user_id, member_role)
VALUES (
    '018f0000-0000-7000-8000-000000000020',
    '018f0000-0000-7000-8000-000000000001',
    'owner'
)
ON CONFLICT DO NOTHING;

INSERT INTO market.instruments (
    id, symbol, venue, asset_class, currency, price_increment, quantity_increment
)
VALUES (
    '018f0000-0000-7000-8000-000000000030',
    'MOCK',
    'SIM',
    'equity',
    'USD',
    0.01,
    1
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO trading.trading_modes (workspace_id, mode, changed_by_user_id)
VALUES (
    '018f0000-0000-7000-8000-000000000020',
    'observation',
    '018f0000-0000-7000-8000-000000000001'
)
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO trading.risk_configurations (
    id,
    workspace_id,
    max_order_notional,
    max_position_notional,
    daily_loss_limit,
    max_open_orders,
    base_currency,
    created_by_user_id
)
VALUES (
    '018f0000-0000-7000-8000-000000000040',
    '018f0000-0000-7000-8000-000000000020',
    1000.00000000,
    5000.00000000,
    250.00000000,
    5,
    'USD',
    '018f0000-0000-7000-8000-000000000001'
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO trading.risk_states (
    workspace_id, risk_configuration_id, state
)
VALUES (
    '018f0000-0000-7000-8000-000000000020',
    '018f0000-0000-7000-8000-000000000040',
    'normal'
)
ON CONFLICT (workspace_id) DO NOTHING;

INSERT INTO operations.server_connections (
    id, workspace_id, connection_type, endpoint_label, status, details
)
VALUES (
    '018f0000-0000-7000-8000-000000000050',
    '018f0000-0000-7000-8000-000000000020',
    'market_data',
    'mock-feed',
    'connected',
    '{"mock": true}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
