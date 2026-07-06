#!/usr/bin/env bash
# VPS-Deployment fuer Seiton Brain (E20-2) — Linux-Server (IONOS, Hetzner, …).
#
# Telegram per Webhook (oeffentliche HTTPS-URL), kein Long-Polling.
# API lauscht nur auf 127.0.0.1:8000 — Reverse-Proxy (Caddy) davor.
#
# Aufruf (im Repo-Root auf dem VPS):
#   ./scripts/deploy-vps.sh
# Optional:
#   VAULT_DIR=/var/lib/seiton-brain/vault ./scripts/deploy-vps.sh
#
# Danach: TLS + Webhook — siehe docs/vps-deployment.md

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VAULT_DIR="${VAULT_DIR:-$ROOT/vault}"
COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.vps.yml)

info() { printf '==> %s\n' "$*"; }
warn() { printf 'Warnung: %s\n' "$*" >&2; }
die() { printf 'Fehler: %s\n' "$*" >&2; exit 1; }

require_linux() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    die "deploy-vps.sh ist nur fuer Linux-VPS gedacht. Fuer Heim-Box: ./scripts/install.sh"
  fi
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    die "Docker fehlt. https://docs.docker.com/engine/install/"
  fi
  if ! docker compose version >/dev/null 2>&1; then
    die "Docker Compose (Plugin) fehlt."
  fi
  if ! docker info >/dev/null 2>&1; then
    die "Docker-Daemon laeuft nicht — z. B. systemctl start docker"
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
  abs_vault="$(mkdir -p "$VAULT_DIR" && cd "$VAULT_DIR" && pwd)"
  set_env_var "OBSIDIAN_VAULT_HOST_PATH" "$abs_vault"
  set_env_var "OBSIDIAN_VAULT_PATH" "/vault"
  set_env_var "SEITON_DEPLOY_MODE" "vps"
  set_env_var "LOG_JSON" "true"
}

ensure_vault() {
  mkdir -p "$VAULT_DIR"
  if [[ -d vault.example ]] && [[ -z "$(ls -A "$VAULT_DIR" 2>/dev/null || true)" ]]; then
    info "Initialisiere Vault aus vault.example/"
    cp -R vault.example/. "$VAULT_DIR/"
  fi
}

compose() {
  docker compose "${COMPOSE_FILES[@]}" "$@"
}

start_stack() {
  info "Starte Seiton Brain (VPS-Modus, Webhook — kein Poller)"
  compose up -d --build
}

run_migrations() {
  info "Fuehre Datenbank-Migrationen aus"
  compose run --rm api alembic upgrade head
}

wait_for_health() {
  info "Warte auf API-Healthcheck (localhost:8000)"
  local i
  for i in $(seq 1 45); do
    if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  warn "Healthcheck-Timeout — pruefe: docker compose logs api"
  return 1
}

print_next_steps() {
  cat <<EOF

Seiton Brain laeuft auf diesem VPS (API nur localhost:8000).

Naechste Schritte:

  1) Setup-Wizard (SSH-Tunnel von deinem Rechner):
       ssh -L 8000:127.0.0.1:8000 user@$(hostname -f 2>/dev/null || echo DEIN-VPS)
       → http://localhost:8000/setup

  2) Reverse-Proxy + TLS (Caddy-Beispiel):
       deploy/Caddyfile.example → /etc/caddy/Caddyfile anpassen

  3) Telegram-Webhook registrieren:
       PUBLIC_URL=https://deine-domain.tld ./scripts/register-telegram-webhook.sh

  4) Status:
       SEITON_DEPLOY_MODE=vps ./scripts/doctor.sh

  5) Updates:
       ./scripts/update.sh

Doku: docs/vps-deployment.md

EOF
}

main() {
  info "Seiton Brain — VPS-Deployment (E20-2)"
  require_linux
  check_docker
  ensure_vault
  ensure_env
  start_stack
  run_migrations
  wait_for_health || true
  print_next_steps
}

main "$@"
