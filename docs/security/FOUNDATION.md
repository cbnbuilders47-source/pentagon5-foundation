# Security Foundation

## Objectives

Establish security invariants before runtime code is authorized. Milestone 1
protects repository integrity; Milestone 2 adds structural contract and
database controls. Neither milestone claims product security.

No prior implementation or security configuration was reused.

## Threat model baseline

Primary assets are future user identity, authorization state, service data,
API credentials, signing identities, update metadata, and build provenance.
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

Future runtime security tests must cover authentication, object-level
authorization, rate limiting, input validation, CORS, CSRF where applicable,
Tauri capability allowlists, secure update verification, and audit logging.

## Results

- Local detect-secrets and Gitleaks scans: PASS.
- Local Trivy and OSV scans: PASS with no findings.
- Hosted security workflow: NOT RUN.
- Local SPDX SBOM generation: PASS.
- Runtime threat and macOS signing/notarization tests: NOT APPLICABLE to
  Milestone 1; no product runtime or artifact exists.
- Milestone 2 detect-secrets, Gitleaks, Trivy, OSV, workflow lint, and SPDX
  generation: PASS locally with no findings.

Scanner configuration is evidence of intent, not evidence that a scan passed.

## Known issues

- CODEOWNERS identity and branch protection are not yet verified.
- GitHub action references are release tags, not immutable commit SHAs.
- Root `SECURITY.md` defines reporting and response policy; hosting contacts
  still require verification.
- Contract and database tooling is locked, but future service dependencies do
  not yet exist.
- Signing certificate custody, notarization, update signing, and incident
  response ownership remain undecided.
- Vulnerability exceptions have no approved process; suppressions are therefore
  forbidden in Milestone 1.

## Security

Mandatory invariants:

1. The FastAPI server will treat all desktop input as untrusted and enforce
   authentication and authorization server-side.
2. The server will run independently of Vite/Tauri; desktop lifecycle events
   cannot stop, restart, or own the server.
3. Vite build-time variables are public unless proven otherwise. Secrets never
   enter a desktop bundle.
4. Tauri capabilities will be deny-by-default, with no generic shell execution
   and no unrestricted filesystem access.
5. CI remains read-only by default. Any future write permission needs a
   job-level justification and protected event context.
6. Security checks fail on findings or tool errors. No `continue-on-error`,
   ignored exit status, or unconditional success is permitted for gates.
7. SBOMs describe the scanned revision and are not a substitute for provenance,
   signing, or vulnerability assessment.

## Acceptance

- Secret, vulnerability, dependency, and SBOM jobs are defined.
- Permissions are read-only by default and elevated only for dependency review.
- Checkout credentials are not persisted.
- Runtime and artifact claims remain NOT RUN or BLOCKED.
- Desktop/server isolation and future native-shell restrictions are explicit.
- No secret, exception, or vulnerability suppression is introduced.

Milestone 2 security acceptance remains structural; it does not authorize a
network service, authentication implementation, or trading behavior.

## Next milestone

Milestone 3 remains unauthorized. Before runtime work, separately approve API
exposure, secret storage, authentication behavior, and runtime data
classification. Add Vite/Tauri and FastAPI security tests only when their scope
and source are authorized.
