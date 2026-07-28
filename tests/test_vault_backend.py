"""Tests fuer VaultBackend Protocol + Factory (E15-1/E15-3)."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.backend import VaultBackend, get_vault_backend
from app.vault.filesystem import FilesystemVaultBackend
from app.vault.git_backend import GitVaultBackend


def test_get_vault_backend_filesystem(monkeypatch):
    monkeypatch.setattr(settings, "vault_backend", "filesystem")
    backend = get_vault_backend()
    assert isinstance(backend, FilesystemVaultBackend)
    assert isinstance(backend, VaultBackend)


def test_get_vault_backend_aliases(monkeypatch):
    for name in ("fs", "Obsidian", "FILESYSTEM"):
        monkeypatch.setattr(settings, "vault_backend", name)
        assert isinstance(get_vault_backend(), FilesystemVaultBackend)


def test_get_vault_backend_git_aliases(monkeypatch):
    for name in ("git", "git-backed", "GitBacked"):
        monkeypatch.setattr(settings, "vault_backend", name)
        assert isinstance(get_vault_backend(), GitVaultBackend)


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


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def _init_repo(path: Path) -> None:
    _git("init", "-b", "main", cwd=path)


def test_git_backend_commits_write_append_and_delete(monkeypatch):
    repo = Path(tempfile.mkdtemp(prefix="git-vault-", dir=Path.cwd()))
    try:
        monkeypatch.setattr(settings, "obsidian_vault_path", str(repo))
        monkeypatch.setattr(settings, "vault_backend", "git")
        monkeypatch.setattr(settings, "vault_git_push", False)
        monkeypatch.setattr(settings, "vault_git_author_name", "Seiton Test")
        monkeypatch.setattr(settings, "vault_git_author_email", "test@example.invalid")
        _init_repo(repo)

        backend = get_vault_backend()
        rel = backend.write_note(
            ClassificationResult(category="idea", title="Git Note", summary="first")
        )
        log1 = _git("log", "--oneline", "-1", cwd=repo).stdout
        assert "seiton(vault): add" in log1
        assert backend.note_exists(rel)

        backend.append_to_note(
            rel,
            ClassificationResult(category="idea", title="Git Note", summary="second"),
        )
        log2 = _git("log", "--oneline", "-1", cwd=repo).stdout
        assert "seiton(vault): update" in log2

        assert backend.delete_note(rel) is True
        log3 = _git("log", "--oneline", "-1", cwd=repo).stdout
        assert "seiton(vault): delete" in log3
    finally:
        shutil.rmtree(repo)


def test_git_backend_pushes_when_enabled(monkeypatch):
    root = Path(tempfile.mkdtemp(prefix="git-vault-push-", dir=Path.cwd()))
    try:
        remote = root / "remote.git"
        remote.mkdir()
        _git("init", "--bare", cwd=remote)

        repo = root / "vault"
        repo.mkdir()
        _init_repo(repo)
        _git("remote", "add", "origin", str(remote), cwd=repo)

        monkeypatch.setattr(settings, "obsidian_vault_path", str(repo))
        monkeypatch.setattr(settings, "vault_backend", "git")
        monkeypatch.setattr(settings, "vault_git_push", True)
        monkeypatch.setattr(settings, "vault_git_remote", "origin")
        monkeypatch.setattr(settings, "vault_git_branch", "main")
        monkeypatch.setattr(settings, "vault_git_author_name", "Seiton Test")
        monkeypatch.setattr(settings, "vault_git_author_email", "test@example.invalid")

        backend = get_vault_backend()
        backend.write_note(
            ClassificationResult(category="note", title="Push Note", summary="hello")
        )

        ls_remote = subprocess.run(
            ["git", "ls-remote", str(remote), "refs/heads/main"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        assert ls_remote, "Expected refs/heads/main to exist on remote after push"

        remote_sha = ls_remote.split()[0]
        remote_subject = subprocess.run(
            ["git", "--git-dir", str(remote), "show", "-s", "--format=%s", remote_sha],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        assert "seiton(vault): add" in remote_subject
    finally:
        shutil.rmtree(root)


def test_git_backend_requires_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "vault_backend", "git")
    backend = get_vault_backend()
    with pytest.raises(RuntimeError, match="not a git repository"):
        backend.write_note(
            ClassificationResult(category="note", title="X", summary="y")
        )
