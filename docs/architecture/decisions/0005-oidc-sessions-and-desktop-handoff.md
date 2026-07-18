# ADR 0005: OIDC Sessions and Desktop Handoff

- Status: accepted
- Date: 2026-07-18

## Context

The macOS application is an untrusted public client. It cannot safely contain an
OIDC client secret, and a system-browser login cannot share cookies reliably with
the Tauri webview. Session material must survive backend restarts without being
stored in plaintext by PostgreSQL or browser storage.

## Decision

PENTAGON5 uses provider-neutral OIDC Authorization Code flow with PKCE, state,
nonce, exact issuer and audience validation, and an allowlisted provider redirect
URI. The provider callback creates an opaque server session and redirects to the
registered `pentagon5://auth/callback` URI with only a short-lived, single-use
login grant. The desktop exchanges that grant once and stores the returned opaque
session token in macOS Keychain.

PostgreSQL stores HMAC-SHA-256 fingerprints of session tokens and one-time codes.
Transient OIDC and login-grant payloads are authenticated-encrypted. Global roles
and permissions are resolved from the accepted identity tables and authorization
denies by default.

## Consequences

- No password database or desktop client secret is introduced.
- Session tokens never appear in URLs, logs, local storage, or database plaintext.
- A deployment must provide an OIDC issuer, client registration, redirect URI,
  and secret through runtime configuration.
- Automated tests use controlled in-process OIDC fixtures; no production bypass
  exists.
