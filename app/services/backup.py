"""Backup-Service fuer die Web-UI (E25-1).

One-Click-Backup: Postgres-Dump (``pg_dump`` gegen ``DATABASE_URL``) +
Vault-Archiv (tar.gz) — gleiche Artefakte wie ``scripts/backup.sh``, aber vom
API-Prozess aus (funktioniert lokal und im Container, dort braucht das Image
``postgresql-client`` und einen ``backups/``-Mount).

Restore bleibt bewusst **gefuehrt** (Befehle pro Backup, keine destruktive
One-Click-Aktion waehrend die App laeuft).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine.url import make_url

from app.config import settings
from app.setup.env_file import resolve_env_path

logger = logging.getLogger(__name__)

_PG_DUMP_TIMEOUT_SEC = 300


def backups_dir() -> Path:
    """Backup-Verzeichnis: ``backups/`` neben der ``.env`` (wie scripts/backup.sh)."""
    return resolve_env_path(settings.seiton_env_file).parent / "backups"


@dataclass(frozen=True)
class BackupOutcome:
    name: str
    directory: str
    files: dict[str, int]
    warnings: list[str] = field(default_factory=list)


def _dump_postgres(dest: Path) -> int:
    """Schreibt ``postgres.sql`` via ``pg_dump``. Liefert Dateigroesse in Bytes."""
    if shutil.which("pg_dump") is None:
        raise RuntimeError(
            "pg_dump nicht gefunden — Image ohne postgresql-client? "
            "Alternative: ./scripts/backup.sh auf dem Host."
        )
    url = make_url(settings.database_url)
    cmd = [
        "pg_dump",
        "--no-owner",
        "--no-acl",
        "-h",
        url.host or "localhost",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "user",
        "-d",
        url.database or "seitonbrain",
    ]
    outfile = dest / "postgres.sql"
    env = {"PGPASSWORD": url.password or ""}
    with outfile.open("wb") as fh:
        result = subprocess.run(
            cmd,
            stdout=fh,
            stderr=subprocess.PIPE,
            env=env,
            timeout=_PG_DUMP_TIMEOUT_SEC,
            check=False,
        )
    if result.returncode != 0:
        err = (result.stderr or b"").decode("utf-8", errors="replace").strip()[:500]
        raise RuntimeError(f"pg_dump exit {result.returncode}: {err}")
    return outfile.stat().st_size


def _archive_vault(dest: Path) -> int | None:
    """Packt den Vault als ``vault.tar.gz``. ``None`` wenn kein Vault-Pfad."""
    vault = Path(settings.obsidian_vault_path)
    if not vault.is_dir():
        return None
    archive = dest / "vault.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(vault, arcname=vault.name or "vault")
    return archive.stat().st_size


def create_backup_sync() -> BackupOutcome:
    """Erstellt ein Backup-Verzeichnis ``seiton-YYYYMMDD-HHMMSS`` (sync)."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    parent = backups_dir()
    dest = parent / f"seiton-{timestamp}"
    try:
        dest.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise RuntimeError(
            f"Backup-Verzeichnis nicht beschreibbar: {parent} ({exc}). "
            "Im Docker-Betrieb muss ./backups gemountet und beschreibbar sein."
        ) from exc

    files: dict[str, int] = {}
    warnings: list[str] = []
    try:
        files["postgres.sql"] = _dump_postgres(dest)
        vault_size = _archive_vault(dest)
        if vault_size is None:
            warnings.append(
                "Vault-Archiv übersprungen (OBSIDIAN_VAULT_PATH kein Verzeichnis)."
            )
        else:
            files["vault.tar.gz"] = vault_size

        manifest = dest / "manifest.txt"
        manifest.write_text(
            "\n".join(
                [
                    f"created_at={timestamp}",
                    "postgres=postgres.sql",
                    f"vault={'vault.tar.gz' if vault_size is not None else '(skipped)'}",
                    f"vault_source={settings.obsidian_vault_path}",
                    "source=ui",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        files["manifest.txt"] = manifest.stat().st_size
    except Exception:
        # Halbes Backup ist gefaehrlicher als keins (Restore-Verwechslung).
        shutil.rmtree(dest, ignore_errors=True)
        raise

    logger.info("Backup erstellt: %s (%s)", dest.name, ", ".join(files))
    return BackupOutcome(
        name=dest.name,
        directory=str(dest),
        files=files,
        warnings=warnings,
    )


@dataclass(frozen=True)
class BackupEntry:
    name: str
    created_at: datetime
    files: dict[str, int]


def list_backup_details(limit: int = 10) -> list[BackupEntry]:
    parent = backups_dir()
    if not parent.is_dir():
        return []
    entries: list[BackupEntry] = []
    for path in sorted(parent.iterdir(), reverse=True):
        if not path.is_dir():
            continue
        files = {
            f.name: f.stat().st_size
            for f in sorted(path.iterdir())
            if f.is_file()
        }
        entries.append(
            BackupEntry(
                name=path.name,
                created_at=datetime.fromtimestamp(path.stat().st_mtime),
                files=files,
            )
        )
        if len(entries) >= limit:
            break
    return entries


def restore_commands(name: str) -> list[str]:
    """Gefuehrte Restore-Befehle fuer ein Backup (Host-Perspektive)."""
    return [
        "docker compose stop api worker poller",
        f"docker compose exec -T db psql -U user -d seitonbrain < backups/{name}/postgres.sql",
        f'tar -xzf backups/{name}/vault.tar.gz -C "$(dirname "$OBSIDIAN_VAULT_HOST_PATH")"',
        "docker compose up -d",
    ]
