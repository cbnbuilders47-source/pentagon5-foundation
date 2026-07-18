"""Static security boundaries that must remain true after Milestone 3."""

from __future__ import annotations

import json
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_tauri_capabilities_exclude_shell_and_filesystem() -> None:
    capability = json.loads(
        (ROOT / "apps/macos-desktop/src-tauri/capabilities/default.json").read_text(
            encoding="utf-8"
        )
    )
    permissions = tuple(str(value).lower() for value in capability["permissions"])
    assert not any("shell" in value or value.startswith("fs:") for value in permissions)


def test_desktop_does_not_persist_tokens_in_browser_storage() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "apps/macos-desktop/src").rglob("*")
        if path.suffix in {".ts", ".tsx"}
    )
    assert "localStorage" not in source
    assert "sessionStorage" not in source


def test_private_runtime_material_is_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".secrets/" in ignore
    assert ".env" in ignore


def test_authentication_container_has_no_published_port() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    authentication = compose.split("  authentication:\n", 1)[1].split("  api-gateway:\n", 1)[0]
    assert "\n    ports:" not in authentication


def test_osv_exceptions_are_reasoned_and_time_bounded() -> None:
    config = tomllib.loads(
        (ROOT / "apps/macos-desktop/src-tauri/osv-scanner.toml").read_text(encoding="utf-8")
    )
    exceptions = config["IgnoredVulns"]
    assert exceptions
    assert all(entry["reason"].strip() for entry in exceptions)
    assert all(date.today() <= entry["ignoreUntil"] <= date(2026, 10, 18) for entry in exceptions)
