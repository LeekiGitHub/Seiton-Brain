#!/usr/bin/env bash
# Consumer-Installer fuer Seiton Brain (E20-1) — macOS / Linux.
#
# Voraussetzung: Docker Desktop / Docker Engine + Compose laeuft.
# Keine Secrets abfragen — Keys trägst du im Setup-Wizard ein:
#   http://localhost:8000/setup
#
# Aufruf (im Repo-Root):
#   ./scripts/install.sh
# Optional:
#   VAULT_DIR=/pfad/zum/vault ./scripts/install.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VAULT_DIR="${VAULT_DIR:-$ROOT/vault}"
COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.consumer.yml)
COMPOSE_PROFILE=(--profile polling)
SETUP_URL="http://localhost:8000/setup"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'Warnung: %s\n' "$*" >&2; }
die() { printf 'Fehler: %s\n' "$*" >&2; exit 1; }

detect_os_hint() {
  case "$(uname -s)" in
    Darwin) echo "https://docs.docker.com/desktop/setup/install/mac-install/" ;;
    Linux) echo "https://docs.docker.com/engine/install/" ;;
    *) echo "https://docs.docker.com/get-docker/" ;;
  esac
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    die "Docker ist nicht installiert. Installationshinweis: $(detect_os_hint)"
  fi
  if ! docker compose version >/dev/null 2>&1; then
    die "Docker Compose (Plugin) fehlt. Bitte Docker Desktop / Compose V2 installieren."
  fi
  if ! docker info >/dev/null 2>&1; then
    die "Docker-Daemon laeuft nicht. Starte Docker Desktop bzw. den Docker-Dienst."
  fi
}

set_env_var() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  if [[ -f .env ]] && grep -q "^${key}=" .env; then
    awk -v k="$key" -v v="$value" '
      BEGIN { done = 0 }
      $0 ~ "^" k "=" { print k "=" v; done = 1; next }
      { print }
      END { if (!done) print k "=" v }
    ' .env >"$tmp"
    mv "$tmp" .env
  else
    printf '%s=%s\n' "$key" "$value" >>.env
  fi
}

ensure_env() {
  if [[ ! -f .env ]]; then
    info "Erstelle .env aus .env.example"
    cp .env.example .env
  fi
  local abs_vault
  abs_vault="$(cd "$VAULT_DIR" && pwd)"
  set_env_var "OBSIDIAN_VAULT_HOST_PATH" "$abs_vault"
  set_env_var "OBSIDIAN_VAULT_PATH" "/vault"
}

ensure_vault() {
  mkdir -p "$VAULT_DIR"
  if [[ -d vault.example ]] && [[ -z "$(ls -A "$VAULT_DIR" 2>/dev/null || true)" ]]; then
    info "Initialisiere Vault aus vault.example/"
    cp -R vault.example/. "$VAULT_DIR/"
  fi
}

compose() {
  docker compose "${COMPOSE_FILES[@]}" "${COMPOSE_PROFILE[@]}" "$@"
}

start_stack() {
  info "Starte Seiton Brain (Consumer-Modus, Telegram Long-Polling)"
  compose up -d --build
}

run_migrations() {
  info "Fuehre Datenbank-Migrationen aus"
  compose run --rm api alembic upgrade head
}

wait_for_health() {
  info "Warte auf API-Healthcheck"
  local i
  for i in $(seq 1 45); do
    if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  warn "Healthcheck-Timeout — pruefe: docker compose logs api"
  return 1
}

open_setup() {
  if [[ "$(uname -s)" == "Darwin" ]] && command -v open >/dev/null 2>&1; then
    open "$SETUP_URL" || true
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$SETUP_URL" || true
  fi
}

print_next_steps() {
  cat <<EOF

Seiton Brain laeuft.

  Setup-Wizard:  $SETUP_URL
  Dashboard:     http://localhost:8000/dashboard
  Status pruefen: ./scripts/doctor.sh
  Updates:       ./scripts/update.sh
  Stoppen:       docker compose ${COMPOSE_FILES[*]} ${COMPOSE_PROFILE[*]} down
  Logs:          docker compose ${COMPOSE_FILES[*]} logs -f api worker

Deine API-Keys bleiben lokal in der .env — nichts wird an uns gesendet.

EOF
}

main() {
  info "Seiton Brain — Consumer-Installation"
  check_docker
  ensure_vault
  ensure_env
  start_stack
  run_migrations
  wait_for_health || true
  open_setup
  print_next_steps
}

main "$@"
