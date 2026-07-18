"""Konfigurierbare Kategorie→Ordner-Zuordnung (E4-3).

Liest optional ``vault_config.yaml`` (Vault-Root oder ``SEITON_VAULT_CONFIG``).
Ohne Datei gelten die Defaults (wie bisher hardcoded).
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_CATEGORY_FOLDERS: dict[str, str] = {
    "school": "School",
    "work": "Work",
    "private": "Private",
    "idea": "Ideas",
    "travel": "Travel",
    "note": "Notes",
}

DEFAULT_FOLDER = "Notes"

# Abwärtskompatibel: viele Tests/Imports erwarten diesen Namen.
CATEGORY_FOLDERS = DEFAULT_CATEGORY_FOLDERS


def clear_category_cache() -> None:
    """Cache leeren (Tests / nach Config-Änderung)."""
    get_category_folders.cache_clear()
    resolve_vault_config_path.cache_clear()


@lru_cache(maxsize=1)
def resolve_vault_config_path() -> Path | None:
    explicit = settings.seiton_vault_config.strip()
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    candidate = Path(settings.obsidian_vault_path) / "vault_config.yaml"
    return candidate if candidate.is_file() else None


def _parse_vault_config_yaml(text: str) -> tuple[dict[str, str], str]:
    """Minimales YAML-Subset fuer categories + default_folder — ohne PyYAML."""
    folders: dict[str, str] = {}
    default_folder = DEFAULT_FOLDER
    in_categories = False

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^categories:\s*$", line):
            in_categories = True
            continue
        if re.match(r"^default_folder:\s*", line):
            in_categories = False
            _, _, value = line.partition(":")
            value = value.strip().strip("\"'")
            if value:
                default_folder = value
            continue
        if in_categories:
            # Ende des Blocks bei neuer Top-Level-Key ohne Indent
            if re.match(r"^[A-Za-z_][\w-]*:\s*", line) and not line.startswith(
                (" ", "\t")
            ):
                in_categories = False
                continue
            match = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.+?)\s*$", line)
            if not match:
                continue
            key = match.group(1).strip().lower()
            folder = match.group(2).strip().strip("\"'")
            if key and folder:
                folders[key] = folder

    return folders, default_folder


@lru_cache(maxsize=1)
def get_category_folders() -> dict[str, str]:
    path = resolve_vault_config_path()
    if path is None:
        return dict(DEFAULT_CATEGORY_FOLDERS)

    try:
        text = path.read_text(encoding="utf-8")
        folders, _default = _parse_vault_config_yaml(text)
    except OSError as exc:
        logger.warning("vault_config.yaml nicht lesbar (%s): %s", path, exc)
        return dict(DEFAULT_CATEGORY_FOLDERS)

    if not folders:
        logger.warning("vault_config.yaml ohne categories — Defaults")
        return dict(DEFAULT_CATEGORY_FOLDERS)

    logger.info("Kategorien aus %s geladen (%d Einträge)", path, len(folders))
    return folders


def get_default_folder() -> str:
    path = resolve_vault_config_path()
    if path is None:
        return DEFAULT_FOLDER
    try:
        text = path.read_text(encoding="utf-8")
        folders, default_folder = _parse_vault_config_yaml(text)
    except OSError:
        return DEFAULT_FOLDER
    if "note" in folders:
        return folders["note"]
    return default_folder or DEFAULT_FOLDER


def folder_for_category(category: str) -> str:
    folders = get_category_folders()
    return folders.get(category.lower(), get_default_folder())


def format_category_list_for_prompt() -> str:
    return ", ".join(get_category_folders().keys())


def format_category_guide_for_prompt() -> str:
    lines = [
        f"- {key}: mapped to folder `{folder}`"
        for key, folder in get_category_folders().items()
    ]
    return "\n".join(lines)
