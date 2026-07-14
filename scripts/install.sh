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

# shellcheck source=scripts/lib/init.sh
source "$ROOT/scripts/lib/init.sh"

VAULT_DIR="${VAULT_DIR:-$ROOT/vault}"
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

ensure_env() {
  if [[ ! -f .env ]]; then
    info "Erstelle .env aus .env.example"
    ensure_env_from_example
  fi
  configure_vault_env "$VAULT_DIR"
}

ensure_vault() {
  if [[ -d "$VAULT_DIR" ]] && [[ -n "$(ls -A "$VAULT_DIR" 2>/dev/null || true)" ]]; then
    return 0
  fi
  info "Vault anlegen: $VAULT_DIR"
  ensure_vault_dir "$VAULT_DIR"
  if [[ -d vault.example ]]; then
    info "Initialisiere Vault aus vault.example/"
  fi
}

COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.consumer.yml)

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
