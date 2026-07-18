# API Client

Milestone 3's narrow TypeScript client for desktop system, authentication, and
WebSocket bootstrap operations. It strictly validates accepted health,
WebSocket, and error envelopes plus the raw authentication responses. The
WebSocket client creates UUIDv7 subscribe envelopes and validates every incoming
frame before delivering it.

The client deliberately has no trading, broker, market-data, strategy, order,
risk, execution, or AI operations. Callers own opaque-token persistence; the
client only accepts a token for authenticated requests.

```sh
npm install
npm run typecheck
npm test
npm run build
```

Expected backend routes:

- `GET /v1/system/health/ready`
- `POST /v1/auth/oidc/start`
- `POST /v1/auth/oidc/exchange`
- `GET /v1/auth/session`
- `POST /v1/auth/logout`
- `POST /v1/auth/ws-tickets`
- `WS /v1/ws/{channel}`
