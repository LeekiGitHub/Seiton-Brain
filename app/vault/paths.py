"""Safe vault path resolution (no path traversal)."""

from pathlib import Path

from app.config import settings


def resolve_vault_file(vault_relative_path: str) -> Path:
    """Return the absolute path under the vault root.

    Uses ``Path.is_relative_to`` instead of ``str.startswith`` so prefix
    collisions like ``/vault`` vs. ``/vault-evil`` cannot slip through (E27-4).
    """
    vault_root = Path(settings.obsidian_vault_path).resolve()
    candidate = (vault_root / vault_relative_path).resolve()
    if not candidate.is_relative_to(vault_root):
        raise ValueError("Invalid vault path")
    return candidate
