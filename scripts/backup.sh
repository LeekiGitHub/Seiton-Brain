#!/usr/bin/env bash
# Lokales Backup: Postgres-Dump + Vault-Snapshot (tar.gz).
#
# Voraussetzung: Docker Compose-Stack laeuft (`docker compose up -d`),
# insbesondere der `db`-Service.
#
# Aufruf:
#   ./scripts/backup.sh              # -> backups/seiton-YYYYMMDD-HHMMSS/
#   ./scripts/backup.sh /pfad/zu/dir # eigenes Zielverzeichnis
#
# Inhalt pro Backup-Ordner:
#   postgres.sql   — pg_dump der seitonbrain-Datenbank
#   vault.tar.gz   — Archiv von OBSIDIAN_VAULT_HOST_PATH (falls gesetzt)
#   manifest.txt   — Metadaten zum Restore

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

read_vault_host_path() {
    if [[ -n "${OBSIDIAN_VAULT_HOST_PATH:-}" ]]; then
        echo "$OBSIDIAN_VAULT_HOST_PATH"
        return
    fi
    if [[ ! -f .env ]]; then
        return
    fi
    local line
    line="$(grep -E '^OBSIDIAN_VAULT_HOST_PATH=' .env | tail -1 || true)"
    if [[ -z "$line" ]]; then
        return
    fi
    local value="${line#OBSIDIAN_VAULT_HOST_PATH=}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    echo "$value"
}

BACKUP_PARENT="${1:-$ROOT/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_PARENT/seiton-$TIMESTAMP"
mkdir -p "$DEST"

if ! docker compose ps --status running --services 2>/dev/null | grep -qx db; then
    echo "Fehler: Service 'db' laeuft nicht. Starte zuerst: docker compose up -d" >&2
    exit 1
fi

echo "==> Postgres-Dump nach $DEST/postgres.sql"
docker compose exec -T db pg_dump -U user -d seitonbrain --no-owner --no-acl \
    >"$DEST/postgres.sql"

VAULT_PATH="$(read_vault_host_path || true)"
VAULT_ARCHIVE="(skipped)"
if [[ -z "${VAULT_PATH:-}" ]]; then
    echo "==> Vault-Snapshot uebersprungen (OBSIDIAN_VAULT_HOST_PATH nicht gesetzt)"
else
    if [[ ! -d "$VAULT_PATH" ]]; then
        echo "Fehler: Vault-Pfad existiert nicht: $VAULT_PATH" >&2
        exit 1
    fi
    VAULT_ARCHIVE="vault.tar.gz"
    echo "==> Vault-Archiv von $VAULT_PATH"
    tar -czf "$DEST/vault.tar.gz" -C "$(dirname "$VAULT_PATH")" "$(basename "$VAULT_PATH")"
fi

{
    echo "created_at=$TIMESTAMP"
    echo "postgres=postgres.sql"
    echo "vault=$VAULT_ARCHIVE"
    echo "vault_source=${VAULT_PATH:-}"
    echo "repo_root=$ROOT"
} >"$DEST/manifest.txt"

echo ""
echo "Backup fertig: $DEST"
echo "  - postgres.sql ($(du -h "$DEST/postgres.sql" | cut -f1))"
if [[ -f "$DEST/vault.tar.gz" ]]; then
    echo "  - vault.tar.gz ($(du -h "$DEST/vault.tar.gz" | cut -f1))"
fi
echo "  - manifest.txt"
