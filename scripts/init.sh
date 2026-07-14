#!/usr/bin/env bash
# Seiton Brain Init (E16-1) — Vault + .env vorbereiten, ohne Secrets abfragen.
#
# Idempotent: mehrfach ausfuehrbar. Keys trägst du in .env oder im Setup-Wizard ein.
#
# Aufruf (im Repo-Root):
#   ./scripts/init.sh
# Optional:
#   VAULT_DIR=/pfad/zum/vault ./scripts/init.sh
#
# Danach:
#   ./scripts/install.sh          # Consumer: Docker starten + Wizard
#   docker compose up -d          # Entwicklung
#   ./scripts/doctor.sh           # Diagnose

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/init.sh
source "$ROOT/scripts/lib/init.sh"

VAULT_DIR="${VAULT_DIR:-$ROOT/vault}"

info() { printf '==> %s\n' "$*"; }
ok() { printf '  [ok] %s\n' "$*"; }

main() {
  info "Seiton Brain — Init (ohne Secrets)"

  if [[ ! -f .env ]]; then
    ensure_env_from_example
    ok ".env aus .env.example erstellt"
  else
    ok ".env vorhanden"
  fi

  if [[ -d "$VAULT_DIR" ]] && [[ -n "$(ls -A "$VAULT_DIR" 2>/dev/null || true)" ]]; then
    ok "Vault: $VAULT_DIR"
  else
    info "Vault anlegen: $VAULT_DIR"
    ensure_vault_dir "$VAULT_DIR"
    if [[ -d vault.example ]]; then
      ok "Vault aus vault.example/ initialisiert"
    else
      ok "Leerer Vault-Ordner angelegt"
    fi
  fi

  configure_vault_env "$VAULT_DIR"
  ok "OBSIDIAN_VAULT_HOST_PATH in .env gesetzt"

  info "Docker-Status"
  print_docker_status

  cat <<EOF

Naechste Schritte:

  1. Keys eintragen (eine Option):
     - Setup-Wizard nach Start: http://localhost:8000/setup
     - oder .env manuell bearbeiten (OPENAI_API_KEY, optional Telegram)

  2. Stack starten:
     Heim-Box:     ./scripts/install.sh
     Entwicklung:  docker compose up -d
     VPS:          ./scripts/deploy-vps.sh

  3. Diagnose:    ./scripts/doctor.sh

Doku: docs/setup.md · docs/vault.md · docs/self-hosting.md

EOF
}

main "$@"
