"""VaultBackend-Abstraktion (E15-1, ADR 0003).

Service-Layer und UI sprechen das Protocol an; die Default-Implementierung
ist Filesystem-Markdown unter ``OBSIDIAN_VAULT_PATH``. Weitere Backends
(Git, S3, …) docken spaeter an dieselbe Schnittstelle an.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.config import settings
from app.llm.schemas import ClassificationResult


@runtime_checkable
class VaultBackend(Protocol):
    def write_note(self, result: ClassificationResult) -> str:
        """Neue Notiz anlegen. Liefert vault-relativen Pfad (z. B. ``Ideas/X.md``)."""

    def append_to_note(self, vault_path: str, result: ClassificationResult) -> str:
        """Update-Block an bestehende Notiz anhaengen. Liefert denselben Relativpfad."""

    def save_note_content(self, vault_path: str, content: str) -> str:
        """Notizinhalt atomar ueberschreiben (UI-Editor)."""

    def delete_note(self, vault_path: str) -> bool:
        """Loescht die Notiz falls vorhanden. ``True`` bei Loeschung."""

    def note_exists(self, vault_path: str) -> bool:
        """Ob die Notiz im Backend vorhanden ist."""


def get_vault_backend() -> VaultBackend:
    """Factory analog zu ``get_llm_provider``."""
    name = settings.vault_backend.strip().lower()
    if name in ("filesystem", "fs", "obsidian"):
        from app.vault.filesystem import FilesystemVaultBackend

        return FilesystemVaultBackend()
    if name in ("git", "git-backed", "gitbacked"):
        from app.vault.git_backend import GitVaultBackend

        return GitVaultBackend()
    raise ValueError(f"Unsupported VAULT_BACKEND: {name}")
