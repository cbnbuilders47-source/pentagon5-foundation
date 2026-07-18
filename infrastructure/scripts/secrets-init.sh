#!/usr/bin/env bash
set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
secrets_dir="$project_root/.secrets"

umask 077
mkdir -p "$secrets_dir"
chmod 700 "$secrets_dir"

create_hex_secret() {
  local name="$1"
  local path="$secrets_dir/$name"

  if [[ -e "$path" || -L "$path" ]]; then
    if [[ -L "$path" || ! -f "$path" ]]; then
      printf 'secrets-init: refusing unsafe path: %s\n' "$path" >&2
      exit 1
    fi
    chmod 600 "$path"
    printf 'secrets-init: preserved %s\n' "$name"
    return
  fi

  openssl rand -hex 32 >"$path"
  chmod 600 "$path"
  printf 'secrets-init: created %s\n' "$name"
}

create_base64_secret() {
  local name="$1"
  local path="$secrets_dir/$name"

  if [[ -e "$path" || -L "$path" ]]; then
    if [[ -L "$path" || ! -f "$path" ]]; then
      printf 'secrets-init: refusing unsafe path: %s\n' "$path" >&2
      exit 1
    fi
    chmod 600 "$path"
    printf 'secrets-init: preserved %s\n' "$name"
    return
  fi

  openssl rand -base64 48 | tr -d '\n' >"$path"
  printf '\n' >>"$path"
  chmod 600 "$path"
  printf 'secrets-init: created %s\n' "$name"
}

create_hex_secret postgres_password
create_base64_secret session_hmac_key
create_hex_secret oidc_client_secret

printf 'secrets-init: private development secrets are ready\n'
