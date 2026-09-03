#!/usr/bin/env bash
# Start Docker Compose and inject secrets from the OS keystore (E16-5).
#
# Usage (repo root):
#   ./scripts/seiton-up.sh
#   ./scripts/seiton-up.sh down
#
# If SEITON_KEYRING=true in .env: keys come from ``seiton keyring-export``
# and are injected via deploy/compose.keyring.yml.
# Otherwise: normal Compose (secrets from .env as before).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/deploy.sh
source "$ROOT/scripts/lib/deploy.sh"

DEPLOY_MODE="$(resolve_deploy_mode)"
load_compose_config "$DEPLOY_MODE"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  printf 'Fehler: python3 nicht gefunden\n' >&2
  exit 1
fi

KEYRING_FLAG="$(read_env_var SEITON_KEYRING 2>/dev/null || true)"
KEYRING_FLAG="$(printf '%s' "$KEYRING_FLAG" | tr '[:upper:]' '[:lower:]')"

if [[ "$KEYRING_FLAG" == "true" || "$KEYRING_FLAG" == "1" || "$KEYRING_FLAG" == "yes" ]]; then
  # shellcheck disable=SC1090
  eval "$("$PY" -m app.cli keyring-export --shell)"
  COMPOSE_FILES+=(-f deploy/compose.keyring.yml)
  printf '==> Secrets aus OS-Keystore geladen (SEITON_KEYRING=true)\n'
fi

ARGS=("$@")
if [[ ${#ARGS[@]} -eq 0 ]]; then
  ARGS=(up -d)
fi

compose_cmd "${ARGS[@]}"
