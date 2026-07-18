# macOS Desktop

Minimal Milestone 3 Tauri 2 shell for macOS. It displays the configured backend
endpoint and status, launches OIDC in the system browser, accepts only
`pentagon5://auth/callback` callbacks, stores the resulting opaque token in the
macOS login Keychain, restores the authenticated user, and maintains a
ticket-based reconnecting WebSocket.

The default backend is `http://127.0.0.1:8000`; set `VITE_BACKEND_URL` at build
time for another endpoint. The backend is always externally managed. This app
does not start, stop, or supervise it.

Security boundaries:

- The webview has only core window/event and deep-link read permissions.
- There is no shell, filesystem, generic opener, updater, or storage plugin.
- Rust exposes only token load/store/delete, stable device-key creation, and a
  validated OIDC browser launch.
- Tokens are held in memory while active and in Keychain at rest, never
  `localStorage`.
- Browser launch accepts HTTPS (or loopback HTTP) authorization-code URLs with
  client ID, state, PKCE S256, and an HTTPS/loopback backend callback.
- The desktop callback contains only a one-time grant code; the exchanged
  session token is never placed in a URL.

```sh
npm install
npm run typecheck
npm test
npm run build
npm run rust:fmt
npm run rust:clippy
npm run rust:test
npm run tauri dev
```

Deep links on macOS must be tested with an installed `.app` bundle. The bundle
target is `.app` only; signing, notarization, DMG, updater, and release
distribution are intentionally absent.
