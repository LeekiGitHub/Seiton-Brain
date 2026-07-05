#!/usr/bin/env bash
# Diagnose fuer lokale Seiton-Brain-Installation (E20-1 / E16-2-Richtung).
#
# Aufruf: ./scripts/doctor.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

read_env_var() {
  local key="$1"
  if [[ ! -f .env ]]; then
    return 1
  fi
  grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | sed 's/^["'\''"]//; s/["'\''"]$//'
}

DEPLOY_MODE="${SEITON_DEPLOY_MODE:-}"
if [[ -z "$DEPLOY_MODE" ]]; then
  DEPLOY_MODE="$(read_env_var SEITON_DEPLOY_MODE 2>/dev/null || true)"
fi
DEPLOY_MODE="${DEPLOY_MODE:-consumer}"
if [[ "$DEPLOY_MODE" == "vps" ]]; then
  COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.vps.yml)
else
  COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.consumer.yml)
fi
ERRORS=0

ok() { printf '  [ok] %s\n' "$*"; }
fail() { printf '  [!!] %s\n' "$*" >&2; ERRORS=$((ERRORS + 1)); }
warn() { printf '  [??] %s\n' "$*" >&2; }

check_telegram_transport() {
  local running token info
  running="$(docker compose "${COMPOSE_FILES[@]}" ps --status running --services 2>/dev/null || true)"
  if [[ "$DEPLOY_MODE" == "vps" ]]; then
    if echo "$running" | grep -qx poller; then
      warn "Poller laeuft im VPS-Modus — stoppe ihn (Webhook-Konflikt)"
    else
      ok "Kein Poller (VPS/Webhook-Modus)"
    fi
    token="$(read_env_var TELEGRAM_BOT_TOKEN || true)"
    if [[ -n "${token:-}" && "$token" != "..." ]]; then
      if info="$(curl -sf "https://api.telegram.org/bot${token}/getWebhookInfo" 2>/dev/null)"; then
        if echo "$info" | grep -q '"url":"https'; then
          ok "Telegram-Webhook registriert"
        else
          warn "Telegram-Webhook nicht gesetzt — ./scripts/register-telegram-webhook.sh"
        fi
      else
        warn "getWebhookInfo fehlgeschlagen (Netzwerk/Token?)"
      fi
    fi
    return
  fi
  if echo "$running" | grep -qx poller; then
    ok "Telegram Poller laeuft (Long-Polling)"
  else
    warn "Telegram Poller laeuft nicht — optional: --profile polling"
  fi
}

check_docker() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    ok "Docker laeuft"
  else
    fail "Docker nicht verfuegbar oder Daemon gestoppt"
  fi
}

check_env_file() {
  if [[ -f .env ]]; then
    ok ".env vorhanden"
  else
    fail ".env fehlt — ./scripts/install.sh oder cp .env.example .env"
  fi
}

check_vault_path() {
  local path
  path="$(read_env_var OBSIDIAN_VAULT_HOST_PATH || true)"
  if [[ -z "${path:-}" ]]; then
    fail "OBSIDIAN_VAULT_HOST_PATH nicht gesetzt"
    return
  fi
  if [[ -d "$path" && -w "$path" ]]; then
    ok "Vault-Pfad beschreibbar: $path"
  else
    fail "Vault-Pfad fehlt oder ist nicht beschreibbar: $path"
  fi
}

check_compose_services() {
  if ! command -v docker >/dev/null 2>&1; then
    return
  fi
  local running
  running="$(docker compose "${COMPOSE_FILES[@]}" ps --status running --services 2>/dev/null || true)"
  for svc in api worker db redis; do
    if echo "$running" | grep -qx "$svc"; then
      ok "Service '$svc' laeuft"
    else
      fail "Service '$svc' laeuft nicht"
    fi
  done
  check_telegram_transport
}

check_http() {
  if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
    ok "API /health erreichbar"
  else
    fail "API /health nicht erreichbar (Port 8000)"
    return
  fi
  if curl -sf "http://localhost:8000/api/setup/status" >/dev/null 2>&1; then
    local complete
    complete="$(curl -sf "http://localhost:8000/api/setup/status" | grep -o '"complete":[^,}]*' | cut -d: -f2 || true)"
    if [[ "$complete" == "true" ]]; then
      ok "Setup wirkt vollstaendig"
    else
      warn "Setup unvollstaendig — http://localhost:8000/setup"
    fi
  else
    warn "Setup-API nicht erreichbar (nur localhost)"
  fi
}

main() {
  printf 'Seiton Brain Doctor (%s)\n\n' "$DEPLOY_MODE"
  check_docker
  check_env_file
  check_vault_path
  check_compose_services
  check_http
  printf '\n'
  if [[ "$ERRORS" -gt 0 ]]; then
    printf '%d harte(r) Fehler — siehe Hinweise oben.\n' "$ERRORS"
    exit 1
  fi
  printf 'Alles ok.\n'
}

main "$@"
