#!/usr/bin/env bash
# Telegram-Webhook fuer VPS-Betrieb registrieren (E20-2).
#
# Voraussetzung: .env mit TELEGRAM_BOT_TOKEN und TELEGRAM_WEBHOOK_SECRET,
# API erreichbar unter PUBLIC_URL (HTTPS, Reverse-Proxy).
#
# Aufruf:
#   PUBLIC_URL=https://brain.example.com ./scripts/register-telegram-webhook.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

die() { printf 'Fehler: %s\n' "$*" >&2; exit 1; }
info() { printf '==> %s\n' "$*"; }

read_env_var() {
  local key="$1"
  if [[ ! -f .env ]]; then
    return 1
  fi
  grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | sed 's/^["'\''"]//; s/["'\''"]$//'
}

PUBLIC_URL="${PUBLIC_URL:-}"
if [[ -z "$PUBLIC_URL" ]]; then
  die "PUBLIC_URL fehlt — z. B. PUBLIC_URL=https://brain.example.com $0"
fi
PUBLIC_URL="${PUBLIC_URL%/}"

TOKEN="$(read_env_var TELEGRAM_BOT_TOKEN || true)"
SECRET="$(read_env_var TELEGRAM_WEBHOOK_SECRET || true)"
if [[ -z "${TOKEN:-}" || "$TOKEN" == "..." ]]; then
  die "TELEGRAM_BOT_TOKEN fehlt in .env — zuerst Setup-Wizard oder .env ausfuellen"
fi
if [[ -z "${SECRET:-}" || "$SECRET" == "..." ]]; then
  die "TELEGRAM_WEBHOOK_SECRET fehlt in .env"
fi

WEBHOOK_URL="${PUBLIC_URL}/webhook"
info "Registriere Webhook: $WEBHOOK_URL"

RESPONSE="$(curl -sf -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "secret_token=${SECRET}")"

if ! echo "$RESPONSE" | grep -q '"ok":true'; then
  die "setWebhook fehlgeschlagen: $RESPONSE"
fi

info "Webhook registriert"
INFO="$(curl -sf "https://api.telegram.org/bot${TOKEN}/getWebhookInfo")"
printf '%s\n' "$INFO"

info "Fertig. Sende eine Testnachricht an deinen Bot."
