"""Tests fuer VaultBackend Protocol + Factory (E15-1)."""

import pytest

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.backend import VaultBackend, get_vault_backend
from app.vault.filesystem import FilesystemVaultBackend


def test_get_vault_backend_filesystem(monkeypatch):
    monkeypatch.setattr(settings, "vault_backend", "filesystem")
    backend = get_vault_backend()
    assert isinstance(backend, FilesystemVaultBackend)
    assert isinstance(backend, VaultBackend)


def test_get_vault_backend_aliases(monkeypatch):
    for name in ("fs", "Obsidian", "FILESYSTEM"):
        monkeypatch.setattr(settings, "vault_backend", name)
        assert isinstance(get_vault_backend(), FilesystemVaultBackend)


def test_get_vault_backend_unsupported(monkeypatch):
    monkeypatch.setattr(settings, "vault_backend", "s3")
    with pytest.raises(ValueError, match="Unsupported VAULT_BACKEND"):
        get_vault_backend()


def test_filesystem_backend_write_and_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "vault_backend", "filesystem")
    backend = get_vault_backend()
    result = ClassificationResult(
        category="idea",
        title="Protocol Note",
        summary="via backend",
        tags=["e15"],
    )
    rel = backend.write_note(result)
    assert rel.endswith("Protocol Note.md")
    assert backend.note_exists(rel)
    assert (tmp_path / rel).is_file()
    assert "via backend" in (tmp_path / rel).read_text(encoding="utf-8")


def test_filesystem_backend_append_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    backend = FilesystemVaultBackend()
    created = backend.write_note(
        ClassificationResult(category="note", title="N", summary="base")
    )
    backend.append_to_note(
        created,
        ClassificationResult(category="note", title="N", summary="more"),
    )
    text = (tmp_path / created).read_text(encoding="utf-8")
    assert "## Update" in text
    assert "more" in text
    assert backend.delete_note(created) is True
    assert backend.note_exists(created) is False
