# Security Foundation

## Objectives

Establish security invariants before runtime code is authorized. Milestone 1
protects repository integrity, makes scanner failures visible, and records the
future desktop/server trust boundary. It does not claim product security.

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

Scanner configuration is evidence of intent, not evidence that a scan passed.

## Known issues

- CODEOWNERS identity and branch protection are not yet verified.
- GitHub action references are release tags, not immutable commit SHAs.
- Root `SECURITY.md` defines reporting and response policy; hosting contacts
  still require verification.
- `pyproject.toml` declares quality tooling but no runtime dependencies; there
  is no lockfile, so dependency evidence remains limited.
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

Milestone 1 security acceptance is a design gate only. Milestone 2 remains
unauthorized until maintainers approve the known issues and next controls.

## Next milestone

Before runtime work, approve identity and authorization models, API exposure,
secret storage, development certificate policy, dependency lockfiles, security
logging, and data classification. Add Vite/Tauri and FastAPI security tests only
when corresponding source exists. Separately authorize signing and notarization;
do not add DMG or release jobs preemptively.
