"""Tests fuer One-Click-Backup + gefuehrten Restore (E25-1)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.services import backup as backup_service
from app.services.backup import BackupEntry, BackupOutcome, restore_commands

client = TestClient(app)


def test_create_backup_sync_writes_manifest_and_vault(tmp_path: Path, monkeypatch):
    vault = tmp_path / "vault"
    (vault / "Ideas").mkdir(parents=True)
    (vault / "Ideas" / "note.md").write_text("# Idee\n", encoding="utf-8")

    monkeypatch.setattr(
        backup_service, "backups_dir", lambda: tmp_path / "backups"
    )
    monkeypatch.setattr(backup_service.settings, "obsidian_vault_path", str(vault))
    monkeypatch.setattr(backup_service.shutil, "which", lambda _: "/usr/bin/pg_dump")

    completed = MagicMock(returncode=0, stderr=b"")
    with patch(
        "app.services.backup.subprocess.run", return_value=completed
    ) as mock_run:
        outcome = backup_service.create_backup_sync()

    assert mock_run.call_args.args[0][0] == "pg_dump"
    assert "PGPASSWORD" in mock_run.call_args.kwargs["env"]
    dest = tmp_path / "backups" / outcome.name
    assert (dest / "manifest.txt").is_file()
    assert (dest / "vault.tar.gz").is_file()
    assert "postgres.sql" in outcome.files
    assert not outcome.warnings


def test_create_backup_sync_cleans_up_on_failure(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        backup_service, "backups_dir", lambda: tmp_path / "backups"
    )
    monkeypatch.setattr(backup_service.shutil, "which", lambda _: None)

    with pytest.raises(RuntimeError, match="pg_dump"):
        backup_service.create_backup_sync()

    leftover = list((tmp_path / "backups").iterdir())
    assert leftover == []


def test_restore_commands_reference_backup():
    cmds = restore_commands("seiton-20260811-190000")
    assert any("psql" in c and "seiton-20260811-190000" in c for c in cmds)
    assert any("tar -xzf" in c for c in cmds)


@patch("app.ui.router.create_backup_sync")
def test_backup_api_creates(mock_create):
    mock_create.return_value = BackupOutcome(
        name="seiton-20260811-190000",
        directory="/tmp/backups/seiton-20260811-190000",
        files={"postgres.sql": 1024, "manifest.txt": 100},
        warnings=["Vault-Archiv übersprungen (OBSIDIAN_VAULT_PATH kein Verzeichnis)."],
    )

    response = client.post("/api/ui/backup")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "seiton-20260811-190000"
    assert data["files"]["postgres.sql"] == 1024
    assert len(data["warnings"]) == 1


@patch("app.ui.router.create_backup_sync")
def test_backup_api_reports_error(mock_create):
    mock_create.side_effect = RuntimeError("pg_dump nicht gefunden")

    response = client.post("/api/ui/backup")

    assert response.status_code == 500
    assert "pg_dump" in response.json()["detail"]


@patch("app.ui.router.list_backup_details")
def test_backup_list_api(mock_list):
    mock_list.return_value = [
        BackupEntry(
            name="seiton-20260811-190000",
            created_at=datetime(2026, 8, 11, 19, 0, 0),
            files={"postgres.sql": 2048},
        )
    ]

    response = client.get("/api/ui/backups")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "seiton-20260811-190000"
    assert any("psql" in c for c in data["items"][0]["restore"])


def test_settings_page_has_backup_button():
    response = client.get("/settings")
    assert response.status_code == 200
    assert 'id="btn-backup"' in response.text
