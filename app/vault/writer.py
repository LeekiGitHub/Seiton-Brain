"""Vault-Schreib-API — duenne Wrapper um ``VaultBackend`` (E15-1).

Bestehende Imports (`from app.vault.writer import write_note`, …) bleiben
gueltig. Implementierung: ``app.vault.filesystem.FilesystemVaultBackend``.
"""

from pathlib import Path

from app.llm.schemas import ClassificationResult
from app.vault.backend import get_vault_backend
from app.vault.categories import CATEGORY_FOLDERS, get_category_folders
from app.vault.filesystem import (
    _atomic_write,
    _next_available_path,
    _parse_frontmatter,
    _related_section,
    _render_frontmatter,
    _sanitize_filename,
    _tags_frontmatter_line,
)
from app.vault.paths import resolve_vault_file

__all__ = [
    "CATEGORY_FOLDERS",
    "get_category_folders",
    "write_note",
    "append_to_note",
    "save_note_content",
    "delete_note",
    # fuer Tests / interne Nutzung (historisch aus writer exportiert)
    "_atomic_write",
    "_next_available_path",
    "_parse_frontmatter",
    "_related_section",
    "_render_frontmatter",
    "_sanitize_filename",
    "_tags_frontmatter_line",
]


def write_note(result: ClassificationResult) -> Path:
    rel = get_vault_backend().write_note(result)
    return resolve_vault_file(rel)


def append_to_note(vault_relative_path: str, result: ClassificationResult) -> Path:
    rel = get_vault_backend().append_to_note(vault_relative_path, result)
    return resolve_vault_file(rel)


def save_note_content(vault_relative_path: str, content: str) -> Path:
    rel = get_vault_backend().save_note_content(vault_relative_path, content)
    return resolve_vault_file(rel)


def delete_note(vault_relative_path: str) -> bool:
    return get_vault_backend().delete_note(vault_relative_path)
