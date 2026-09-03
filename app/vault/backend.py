"""VaultBackend abstraction (E15-1, ADR 0003).

Service layer and UI talk to the Protocol; the default implementation
is filesystem Markdown under ``OBSIDIAN_VAULT_PATH``. Further backends
(Git, S3, …) plug into the same interface later.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.config import settings
from app.llm.schemas import ClassificationResult


@runtime_checkable
class VaultBackend(Protocol):
    def write_note(self, result: ClassificationResult) -> str:
        """Create a new note. Return vault-relative path (e.g. ``Ideas/X.md``)."""

    def append_to_note(self, vault_path: str, result: ClassificationResult) -> str:
        """Append an update block to an existing note. Return the same relative path."""

    def save_note_content(self, vault_path: str, content: str) -> str:
        """Atomically overwrite note content (UI editor)."""

    def delete_note(self, vault_path: str) -> bool:
        """Delete the note if present. ``True`` if deleted."""

    def note_exists(self, vault_path: str) -> bool:
        """Whether the note exists in the backend."""


def get_vault_backend() -> VaultBackend:
    """Factory analogous to ``get_llm_provider``."""
    name = settings.vault_backend.strip().lower()
    if name in ("filesystem", "fs", "obsidian"):
        from app.vault.filesystem import FilesystemVaultBackend

        return FilesystemVaultBackend()
    if name in ("git", "git-backed", "gitbacked"):
        from app.vault.git_backend import GitVaultBackend

        return GitVaultBackend()
    raise ValueError(f"Unsupported VAULT_BACKEND: {name}")
