#!/usr/bin/env bash
# Startet Docker Compose und injiziert Secrets aus dem OS-Keystore (E16-5).
#
# Aufruf (Repo-Root):
#   ./scripts/seiton-up.sh
#   ./scripts/seiton-up.sh down
#
# Wenn SEITON_KEYRING=true in .env: Keys kommen von ``seiton keyring-export``
# und werden via deploy/compose.keyring.yml in die Container injiziert.
# Sonst: normales Compose (Secrets aus .env wie bisher).

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
