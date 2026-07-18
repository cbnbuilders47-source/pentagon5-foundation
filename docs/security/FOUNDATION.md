# Security Foundation

## Objectives

Record security invariants through the authorized Milestone 3 identity runtime.
Milestone 1 protects repository integrity, Milestone 2 adds contract/database
controls, and Milestone 3 implements bounded authentication and native-client
controls without claiming complete product security.

No prior implementation or security configuration was reused.

## Threat model baseline

Primary assets are user identity, authorization state, opaque sessions, OIDC
client credentials, service data, and build provenance. Signing identities and
update metadata remain future assets outside Milestone 3.
Likely threat actors include unauthenticated network clients, compromised user
devices, malicious dependencies, leaked credentials, and contributors abusing
CI permissions.

Initial abuse cases:

- A modified desktop calls privileged API operations.
- A malicious web payload reaches an over-broad Tauri command.
- A secret is committed or printed by CI.
- A dependency or action introduces known vulnerable behavior.
- A pull request obtains write permission or persistent checkout credentials.
- A desktop shutdown terminates a server that should remain available.
- An unsigned or unverified desktop artifact is distributed.

## Files

- `.github/workflows/security.yml` runs Gitleaks, Trivy, OSV-Scanner, dependency
  review, and SPDX SBOM generation.
- `.github/workflows/foundation.yml` enforces repository and configuration shape.
- `.github/dependabot.yml` proposes bounded dependency updates.
- `.github/CODEOWNERS` requires security-sensitive path review once its team is
  validated and branch protection is configured.
- `.pre-commit-config.yaml` detects private keys and validates tracked content.
- `uv.lock` locks contract, migration, database-driver, and validation tooling.
- `backend/` enforces strict settings, secret-file indirection, safe logging,
  request bounds, exact CORS, metrics, and optional tracing.
- `services/authentication/` implements OIDC PKCE, one-time grants, opaque
  fingerprinted sessions, devices, ticketed WebSockets, and global RBAC.
- `packages/auth-contracts/` keeps auth schemas separate from domain contracts.
- `apps/macos-desktop/src-tauri/` limits native access to Keychain and validated
  OIDC browser launch commands.
- Contract fixtures and database seeds are synthetic and development-only.

## Commands

Local baseline:

```sh
pre-commit run --all-files --show-diff-on-failure
gitleaks git --redact
trivy fs --scanners vuln,misconfig,secret --severity HIGH,CRITICAL .
osv-scanner scan --recursive .
syft dir:. -o spdx-json=foundation.spdx.json
```

Tool versions and installation must be controlled by the operator. Do not paste
tokens into command lines, checked-in configuration, or shell history.

## Tests

- Full-history secret scanning with redacted findings.
- Filesystem vulnerability, secret, and misconfiguration scanning.
- Recursive manifest and lockfile vulnerability scanning.
- Pull-request dependency delta review at moderate severity or above.
- SPDX JSON SBOM creation and short-lived artifact upload.
- Private-key detection before commit.
- Workflow permission and persisted-credential review.
- Contract rejection tests for malformed identifiers, timestamps, decimals,
  idempotency metadata, and invalid states.
- Database constraints preventing invalid financial and lifecycle state.
- Append-only audit mutation tests.
- OIDC state, nonce, PKCE, issuer, audience, expiry, replay, and one-time grant
  tests.
- Default-deny RBAC, keyed fingerprints, exact CORS, body/timeout limits,
  WebSocket tickets, safe errors/logging, and Tauri capability tests.

Object-level authorization for future domain resources, rate limiting, secure
updates, and release signing remain outside the current surface.

## Results

- Local detect-secrets and Gitleaks scans: PASS.
- Local Trivy and OSV scans: PASS with no findings.
- Hosted security workflow: NOT RUN.
- Local SPDX SBOM generation: PASS.
- Milestone 2 detect-secrets, Gitleaks, Trivy, OSV, workflow lint, and SPDX
  generation: PASS locally with no findings.
- Focused Milestone 3 runtime, auth contract, client, and Rust security suites:
  PASS.
- Milestone 3 Gitleaks, Trivy, OSV-Scanner, detect-secrets, private-key,
  npm-audit, and Tauri capability checks: PASS.
- Final full Milestone 3 acceptance: PASS.
- Signing, notarization, DMG, and updater checks: NOT AUTHORIZED.

Scanner configuration is evidence of intent, not evidence that a scan passed.

## Known issues

- CODEOWNERS identity and branch protection are not yet verified.
- GitHub action references are release tags, not immutable commit SHAs.
- Root `SECURITY.md` defines reporting and response policy; hosting contacts
  still require verification.
- Signing certificate custody, notarization, update signing, and incident
  response ownership remain undecided.
- Tauri 2 currently locks Linux-only GTK3 crates and unmaintained build crates
  that OSV reports for every target. The macOS dependency tree excludes the
  GTK3 and `proc-macro-error` crates. Time-bounded, reasoned exceptions in
  `apps/macos-desktop/src-tauri/osv-scanner.toml` expire on 2026-10-18; an
  upstream Tauri update must replace them before renewal.

## Security

Mandatory invariants:

1. FastAPI treats all desktop input as untrusted and enforces
   authentication and authorization server-side.
2. Backend services run independently of Vite/Tauri; desktop lifecycle events
   cannot stop, restart, or own the server.
3. Vite build-time variables are public unless proven otherwise. Secrets never
   enter a desktop bundle.
4. Tauri capabilities are deny-by-default, with no generic shell execution
   and no unrestricted filesystem access.
5. CI remains read-only by default. Any future write permission needs a
   job-level justification and protected event context.
6. Security checks fail on findings or tool errors. No `continue-on-error`,
   ignored exit status, or unconditional success is permitted for gates.
7. SBOMs describe the scanned revision and are not a substitute for provenance,
   signing, or vulnerability assessment.
8. The native callback contains only a short-lived one-time grant. The desktop
   stores the exchanged opaque token and device key only in macOS Keychain.
9. PostgreSQL stores keyed HMAC fingerprints, not plaintext sessions, states,
   grant codes, device keys, or WebSocket tickets. Transient payloads are
   authenticated-encrypted.

## Acceptance

- Secret, vulnerability, dependency, and SBOM jobs are defined.
- Permissions are read-only by default and elevated only for dependency review.
- Checkout credentials are not persisted.
- Focused runtime evidence and full acceptance evidence are distinguished.
- Desktop/server isolation and native-shell restrictions are explicit.
- Scanner exceptions are explicit, target-justified, and time-bounded.

Milestone 3 security scope authorizes identity and transport controls only; it
does not authorize trading behavior or release distribution.

## Next milestone

Milestone 4 is not authorized. Broker, market, strategy, order, execution, risk,
reconciliation, AI, signing, notarization, DMG, and updater work require a
separate security scope.
