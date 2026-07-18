"""Executable Milestone 1 repository invariants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_milestone_evidence_has_required_sections() -> None:
    evidence = (ROOT / "docs/operations/MILESTONE_1.md").read_text()
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


def test_product_source_is_not_present() -> None:
    forbidden_manifests = (
        ROOT / "package.json",
        ROOT / "Cargo.toml",
        ROOT / "apps/macos-desktop/package.json",
        ROOT / "apps/macos-desktop/Cargo.toml",
        ROOT / "apps/admin-console/package.json",
    )
    assert not any(path.exists() for path in forbidden_manifests)


def test_boundaries_remain_documentation_only() -> None:
    boundary_roots = (ROOT / "apps", ROOT / "services", ROOT / "packages")
    readmes = [path for boundary in boundary_roots for path in boundary.glob("*/README.md")]
    assert len(readmes) == 20
    assert all("## NOT IMPLEMENTED" in path.read_text() for path in readmes)
