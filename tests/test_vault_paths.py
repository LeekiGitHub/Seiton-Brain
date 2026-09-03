"""Tests for app/vault/paths.py."""

import pytest

from app.vault.paths import resolve_vault_file


def test_resolve_vault_file(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    note = tmp_path / "Notes" / "A.md"
    note.write_text("x")
    assert resolve_vault_file("Notes/A.md") == note.resolve()


def test_resolve_vault_file_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(tmp_path))
    with pytest.raises(ValueError, match="Invalid vault path"):
        resolve_vault_file("../../../etc/passwd")


def test_resolve_vault_file_rejects_prefix_collision(tmp_path, monkeypatch):
    """startswith without separator would accept /vault-evil as child of /vault."""
    vault = tmp_path / "vault"
    evil = tmp_path / "vault-evil"
    vault.mkdir()
    evil.mkdir()
    (evil / "secret.md").write_text("x")
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(vault))
    with pytest.raises(ValueError, match="Invalid vault path"):
        resolve_vault_file("../vault-evil/secret.md")
