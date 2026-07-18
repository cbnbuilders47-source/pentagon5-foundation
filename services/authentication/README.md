# Authentication

Provider-neutral OIDC Authorization Code + PKCE service. The service validates
issuer discovery, ID-token signatures, audience, nonce, expiry, and verified
email before provisioning an identity. It never accepts a local login bypass.

Local sessions and WebSocket tickets are opaque random values; PostgreSQL stores
only keyed HMAC-SHA256 fingerprints. OIDC flow verifiers and nonces are
authenticated-encrypted while transiently stored. Global roles and permissions
are read from PostgreSQL for every resolved session.

After the HTTPS provider callback, the browser is redirected to the exact
configured custom desktop URI with only a random, short-lived one-time code.
`POST /v1/auth/oidc/exchange` consumes that code and returns the opaque session
token once. The encrypted login-grant payload is never placed in a URL. Browser
cookies are disabled by default and require explicit `P5_WEB_COOKIE_MODE=true`.

Run with `uvicorn pentagon5_auth.app:create_app --factory`. Configuration uses
strict `P5_` environment variables. Secrets support mutually exclusive
`P5_OIDC_CLIENT_SECRET_FILE`, `P5_SESSION_HMAC_KEY_FILE`, and
`P5_DATABASE_URL_FILE` forms. Production issuer and callback URLs must be HTTPS.

REST routes are under `/v1/auth`; liveness and readiness are under
`/v1/system/health`. Ticketed WebSockets accept only `system.health` and
`session.events`.
