#!/usr/bin/env bash
# Auto-Update fuer Seiton Brain (E20-4).
#
# Holt Git-Aenderungen, baut Container neu, fuehrt Migrationen aus.
# Erkennt Consumer- vs. VPS-Modus (SEITON_DEPLOY_MODE in .env).
#
# Aufruf (im Repo-Root):
#   ./scripts/update.sh              # Backup + Update
#   ./scripts/update.sh --check      # nur pruefen, ob Updates verfuegbar
#   ./scripts/update.sh --no-backup  # ohne vorheriges Backup
#
# Optional per Cron/systemd — siehe deploy/seiton-update.{service,timer}

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck source=scripts/lib/deploy.sh
source "$ROOT/scripts/lib/deploy.sh"

SKIP_BACKUP=0
CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-backup) SKIP_BACKUP=1 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      printf 'Fehler: Unbekannte Option %s\n' "$1" >&2
      exit 1
      ;;
  esac
  shift
done

info() { printf '==> %s\n' "$*"; }
warn() { printf 'Warnung: %s\n' "$*" >&2; }
die() { printf 'Fehler: %s\n' "$*" >&2; exit 1; }

DEPLOY_MODE="$(resolve_deploy_mode)"
load_compose_config "$DEPLOY_MODE"

current_branch() {
  git symbolic-ref -q --short HEAD || echo "main"
}

upstream_ref() {
  local branch upstream
  branch="$(current_branch)"
  upstream="$(git rev-parse --abbrev-ref "@{upstream}" 2>/dev/null || true)"
  if [[ -n "$upstream" ]]; then
    printf '%s' "$upstream"
  else
    printf 'origin/%s' "$branch"
  fi
}

check_git_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    die "Kein Git-Repository — Update nur bei Git-Checkout moeglich"
  fi
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    die "Docker nicht verfuegbar"
  fi
}

fetch_updates() {
  if git remote | grep -q .; then
    git fetch --prune origin 2>/dev/null || git fetch --prune 2>/dev/null || true
  fi
}

commits_behind() {
  local ref
  ref="$(upstream_ref)"
  git rev-list --count "HEAD..${ref}" 2>/dev/null || echo "0"
}

print_version_info() {
  local sha
  sha="$(git rev-parse --short HEAD)"
  info "Aktuelle Version: $(current_branch) @ ${sha}"
}

run_check() {
  check_git_repo
  fetch_updates
  local behind ref
  behind="$(commits_behind)"
  ref="$(upstream_ref)"
  if [[ "$behind" == "0" ]]; then
    info "Keine Updates verfuegbar (${ref})"
    print_version_info
    return 0
  fi
  info "${behind} Commit(s) hinter ${ref} — ./scripts/update.sh ausfuehren"
  git log --oneline "HEAD..${ref}" | head -10
  return 1
}

wait_for_health() {
  info "Warte auf API-Healthcheck"
  local i
  for i in $(seq 1 45); do
    if curl -sf "http://127.0.0.1:8000/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  warn "Healthcheck-Timeout — pruefe Logs: compose_cmd logs api"
  return 1
}

run_update() {
  check_git_repo
  check_docker
  fetch_updates

  local behind
  behind="$(commits_behind)"
  if [[ "$behind" == "0" ]]; then
    info "Bereits aktuell — nichts zu tun"
    print_version_info
    return 0
  fi

  info "Update: ${behind} Commit(s) werden eingespielt (${DEPLOY_MODE}-Modus)"

  if [[ "$SKIP_BACKUP" -eq 0 ]]; then
    if [[ -x "$ROOT/scripts/backup.sh" ]]; then
      info "Erstelle Backup vor dem Update"
      "$ROOT/scripts/backup.sh" || warn "Backup fehlgeschlagen — Update wird trotzdem fortgesetzt"
    fi
  fi

  if ! git diff --quiet || ! git diff --cached --quiet; then
    die "Lokale Aenderungen im Repo — bitte committen oder stashen vor dem Update"
  fi

  info "git pull --ff-only"
  git pull --ff-only

  info "Container neu bauen und starten"
  compose_cmd up -d --build

  info "Datenbank-Migrationen"
  compose_cmd run --rm api alembic upgrade head

  wait_for_health || true
  print_version_info

  if [[ -x "$ROOT/scripts/doctor.sh" ]]; then
    info "Kurz-Diagnose"
    "$ROOT/scripts/doctor.sh" || warn "Doctor meldet Probleme — Logs pruefen"
  fi

  info "Update abgeschlossen"
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  run_check
else
  run_update
fi
