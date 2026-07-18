#!/usr/bin/env bash
set -Eeuo pipefail

export PATH="/opt/homebrew/opt/node/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$project_root"

failed=0

require_command() {
  local command_name="$1"
  if command -v "$command_name" >/dev/null 2>&1; then
    printf 'ok: %s\n' "$command_name"
  else
    printf 'missing: %s\n' "$command_name" >&2
    failed=1
  fi
}

require_command docker
require_command make
require_command curl
require_command node
require_command npm
require_command rustc
require_command cargo
require_command rustup
require_command uv

if [[ "$(uname -s)" == "Darwin" ]]; then
  require_command xcodebuild
  require_command xcrun
else
  printf 'notice: full Xcode validation is available only on macOS\n'
fi

if command -v node >/dev/null 2>&1; then
  node_major="$(node -p 'process.versions.node.split(".")[0]')"
  if (( node_major < 24 )); then
    printf 'unsupported: Node.js 24 or newer is required; found %s\n' "$(node --version)" >&2
    failed=1
  fi
fi

if command -v uv >/dev/null 2>&1; then
  if ! uv run --python 3.12 --no-project python -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
    printf 'unsupported: uv-managed Python 3.12 is required\n' >&2
    failed=1
  else
    printf 'ok: uv-managed Python 3.12\n'
  fi
fi

if [[ "$(uname -s)" == "Darwin" ]] && command -v xcodebuild >/dev/null 2>&1; then
  if ! xcodebuild -version >/dev/null 2>&1; then
    printf 'unavailable: full Xcode is required; Command Line Tools alone are insufficient\n' >&2
    failed=1
  fi
fi

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    printf 'ok: docker compose\n'
  else
    printf 'missing: Docker Compose v2 plugin\n' >&2
    failed=1
  fi

  if docker info >/dev/null 2>&1; then
    printf 'ok: Docker daemon\n'
  else
    printf 'unavailable: Docker daemon is not running or is not accessible\n' >&2
    failed=1
  fi
fi

if (( failed != 0 )); then
  printf 'doctor: prerequisites are not satisfied\n' >&2
  exit 1
fi

if ! docker compose config --quiet; then
  printf 'doctor: docker-compose.yml is invalid\n' >&2
  exit 1
fi

printf 'doctor: local infrastructure prerequisites are ready\n'
