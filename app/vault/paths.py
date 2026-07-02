"""Sichere Vault-Pfad-Aufloesung (kein Path-Traversal)."""

from pathlib import Path

from app.config import settings


def resolve_vault_file(vault_relative_path: str) -> Path:
    """Liefert den absoluten Pfad unterhalb des Vault-Roots."""
    vault_root = Path(settings.obsidian_vault_path).resolve()
    candidate = (vault_root / vault_relative_path).resolve()
    if not str(candidate).startswith(str(vault_root)):
        raise ValueError("Invalid vault path")
    return candidate
