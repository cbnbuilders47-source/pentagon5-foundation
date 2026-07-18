#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$project_root"

for command_name in docker curl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'stack-health: missing required command: %s\n' "$command_name" >&2
    exit 1
  fi
done

if ! docker compose version >/dev/null 2>&1; then
  printf 'stack-health: Docker Compose v2 plugin is unavailable\n' >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  printf 'stack-health: Docker daemon is not running or is not accessible\n' >&2
  exit 1
fi

services=(postgres redis minio otel-collector prometheus grafana authentication api-gateway)

for service in "${services[@]}"; do
  container_id="$(docker compose ps --quiet "$service")"
  if [[ -z "$container_id" ]]; then
    printf 'stack-health: %s has no container\n' "$service" >&2
    exit 1
  fi

  state="$(docker inspect --format '{{.State.Status}}' "$container_id")"
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id")"

  if [[ "$state" != "running" || "$health" != "healthy" ]]; then
    printf 'stack-health: %s is state=%s health=%s\n' "$service" "$state" "$health" >&2
    exit 1
  fi
  printf 'healthy: %s\n' "$service"
done

check_http() {
  local service="$1"
  local container_port="$2"
  local path="$3"
  local address

  if ! address="$(docker compose port "$service" "$container_port")" || [[ -z "$address" ]]; then
    printf 'stack-health: cannot resolve host port for %s\n' "$service" >&2
    exit 1
  fi

  if ! curl --fail --silent --show-error --max-time 5 "http://${address}${path}" >/dev/null; then
    printf 'stack-health: HTTP health check failed for %s\n' "$service" >&2
    exit 1
  fi
  printf 'reachable: %s\n' "$service"
}

check_http minio 9000 /minio/health/live
check_http otel-collector 13133 /
check_http prometheus 9090 /-/healthy
check_http grafana 3000 /api/health
check_http api-gateway 8000 /v1/system/health/ready

if ! docker compose exec -T authentication python -c \
  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/v1/system/health/ready', timeout=5)"; then
  printf 'stack-health: internal authentication readiness check failed\n' >&2
  exit 1
fi
printf 'reachable: authentication (internal only)\n'

printf 'stack-health: dependencies and independent backend processes are healthy\n'
