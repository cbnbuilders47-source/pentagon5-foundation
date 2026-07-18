"""Executable repository and milestone-scope invariants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_milestone_evidence_has_required_sections() -> None:
    headings = (
        "Objectives",
        "Files",
        "Commands",
        "Tests",
        "Results",
        "Known issues",
        "Security",
        "Acceptance",
        "Next milestone",
    )
    for milestone in ("MILESTONE_1.md", "MILESTONE_2.md", "MILESTONE_3.md"):
        evidence = (ROOT / "docs/operations" / milestone).read_text()
        assert all(f"## {heading}\n" in evidence for heading in headings)


def test_compose_ports_are_loopback_only() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()
    published_ports = [
        line.strip()
        for line in compose.splitlines()
        if line.strip().startswith('- "127.0.0.1:')
        or (line.strip().startswith('- "') and ":" in line)
    ]
    assert published_ports
    assert all(line.startswith('- "127.0.0.1:') for line in published_ports)


def test_product_manifests_stay_out_of_unimplemented_roots() -> None:
    forbidden_manifests = (
        ROOT / "package.json",
        ROOT / "Cargo.toml",
        ROOT / "apps/admin-console/package.json",
    )
    assert not any(path.exists() for path in forbidden_manifests)


def test_unimplemented_boundaries_remain_documentation_only() -> None:
    boundary_roots = (ROOT / "apps", ROOT / "services", ROOT / "packages")
    readmes = [path for boundary in boundary_roots for path in boundary.glob("*/README.md")]
    implemented = {
        ROOT / "apps/macos-desktop/README.md",
        ROOT / "packages/api-client/README.md",
        ROOT / "packages/auth-contracts/README.md",
        ROOT / "services/authentication/README.md",
        ROOT / "services/api-gateway/README.md",
    }
    assert len(readmes) == 21
    assert all(
        "## NOT IMPLEMENTED" in path.read_text() for path in readmes if path not in implemented
    )
    assert (ROOT / "packages/shared-types/schemas/v1/domain.schema.json").is_file()
    assert (ROOT / "packages/event-contracts/schemas/v1/message.schema.json").is_file()
    assert (ROOT / "packages/auth-contracts/schemas/v1/auth.schema.json").is_file()


def test_excluded_runtime_boundaries_have_no_source() -> None:
    excluded = (
        "apps/admin-console",
        "services/audit-service",
        "services/instrument-master",
        "services/market-data",
        "services/notification-service",
        "services/order-router",
        "services/reconciliation",
        "services/reporting",
        "services/risk-engine",
        "services/signal-allocator",
        "services/strategy-engine",
        "packages/theme-system",
        "packages/ui-components",
    )
    for relative in excluded:
        files = {
            path.relative_to(ROOT / relative).as_posix()
            for path in (ROOT / relative).rglob("*")
            if path.is_file()
        }
        assert files == {"README.md"}, relative


def test_milestone_2_contracts_and_migration_are_immutable() -> None:
    immutable = (
        "packages/shared-types/schemas/v1/common.schema.json",
        "packages/shared-types/schemas/v1/domain.schema.json",
        "packages/event-contracts/schemas/v1/message.schema.json",
        "infrastructure/database/metadata_0001.py",
        "infrastructure/database/migrations/versions/0001_initial_database.py",
    )
    assert all((ROOT / relative).is_file() for relative in immutable)
