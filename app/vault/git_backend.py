"""Git-backed VaultBackend (E15-3)."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.filesystem import FilesystemVaultBackend

logger = logging.getLogger(__name__)


class GitVaultBackend:
    """Filesystem backend plus a Git commit per change.

    Still writes Markdown files locally, then stages only the affected
    file and creates a commit. Optionally can push straight to a remote.
    """

    def __init__(self) -> None:
        self.filesystem = FilesystemVaultBackend()
        self.vault_root = Path(settings.obsidian_vault_path)

    def write_note(self, result: ClassificationResult) -> str:
        rel = self.filesystem.write_note(result)
        self._commit_path(rel, f"seiton(vault): add {rel}")
        return rel

    def append_to_note(self, vault_path: str, result: ClassificationResult) -> str:
        rel = self.filesystem.append_to_note(vault_path, result)
        self._commit_path(rel, f"seiton(vault): update {rel}")
        return rel

    def save_note_content(self, vault_path: str, content: str) -> str:
        rel = self.filesystem.save_note_content(vault_path, content)
        self._commit_path(rel, f"seiton(vault): edit {rel}")
        return rel

    def delete_note(self, vault_path: str) -> bool:
        deleted = self.filesystem.delete_note(vault_path)
        if deleted:
            self._commit_path(vault_path, f"seiton(vault): delete {vault_path}")
        return deleted

    def note_exists(self, vault_path: str) -> bool:
        return self.filesystem.note_exists(vault_path)

    def _git_env(self) -> dict[str, str]:
        env = os.environ.copy()
        name = settings.vault_git_author_name.strip()
        email = settings.vault_git_author_email.strip()
        if name:
            env['GIT_AUTHOR_NAME'] = name
            env['GIT_COMMITTER_NAME'] = name
        if email:
            env['GIT_AUTHOR_EMAIL'] = email
            env['GIT_COMMITTER_EMAIL'] = email
        return env

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ['git', *args],
                cwd=self.vault_root,
                env=self._git_env(),
                check=check,
                text=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError('git executable not found') from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or '').strip()
            stdout = (exc.stdout or '').strip()
            details = stderr or stdout or 'git command failed'
            raise RuntimeError(details) from exc

    def _ensure_repo(self) -> None:
        if not (self.vault_root / '.git').exists():
            raise RuntimeError(
                f'Vault path is not a git repository: {self.vault_root}'
            )

    def _commit_path(self, rel_path: str, message: str) -> None:
        self._ensure_repo()
        self._run_git('add', '-A', '--', rel_path)
        staged = self._run_git('diff', '--cached', '--quiet', '--', rel_path, check=False)
        if staged.returncode == 0:
            logger.info('No git changes for vault path %s', rel_path)
            return
        self._run_git('commit', '-m', message)
        if settings.vault_git_push:
            remote = settings.vault_git_remote.strip()
            if not remote:
                raise RuntimeError('VAULT_GIT_PUSH=true requires VAULT_GIT_REMOTE')
            branch = settings.vault_git_branch.strip()
            if branch:
                self._run_git('push', remote, f'HEAD:{branch}')
            else:
                self._run_git('push', remote, 'HEAD')
