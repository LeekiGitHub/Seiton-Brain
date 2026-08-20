"""Sichere Vault-Pfad-Aufloesung (kein Path-Traversal)."""

from pathlib import Path

from app.config import settings


def resolve_vault_file(vault_relative_path: str) -> Path:
    """Liefert den absoluten Pfad unterhalb des Vault-Roots.

    Nutzt ``Path.is_relative_to`` statt ``str.startswith``, damit Prefix-
    Kollisionen wie ``/vault`` vs. ``/vault-evil`` nicht durchgehen (E27-4).
    """
    vault_root = Path(settings.obsidian_vault_path).resolve()
    candidate = (vault_root / vault_relative_path).resolve()
    if not candidate.is_relative_to(vault_root):
        raise ValueError("Invalid vault path")
    return candidate
