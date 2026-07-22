"""Prompt-Dateien versioniert laden (E4-4)."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def normalize_prompt_version(version: str | None) -> str:
    raw = (version or "").strip().lower()
    if not raw:
        return "v1"
    if raw.startswith("v") and raw[1:].isdigit():
        return raw
    if raw.isdigit():
        return f"v{raw}"
    return raw


def resolve_prompt_path(name: str, version: str | None = None) -> Path:
    """Loest ``prompts/{name}.{version}.txt``, Fallback ``prompts/{name}.txt``.

    Beispiele: name=\"classify\", version=\"v1\" → ``classify.v1.txt``.
    """
    ver = normalize_prompt_version(version if version is not None else settings.seiton_prompt_version)
    versioned = PROMPTS_DIR / f"{name}.{ver}.txt"
    if versioned.is_file():
        return versioned
    legacy = PROMPTS_DIR / f"{name}.txt"
    if legacy.is_file():
        logger.warning(
            "Prompt %s.%s.txt fehlt — Fallback auf %s",
            name,
            ver,
            legacy.name,
        )
        return legacy
    raise FileNotFoundError(
        f"Prompt nicht gefunden: {versioned.name} oder {legacy.name} in {PROMPTS_DIR}"
    )


def load_prompt(name: str, version: str | None = None) -> tuple[str, str]:
    """Liefert ``(inhalt, verwendete_version)``."""
    ver = normalize_prompt_version(version if version is not None else settings.seiton_prompt_version)
    path = resolve_prompt_path(name, ver)
    text = path.read_text(encoding="utf-8")
    # Wenn nur Legacy-Datei existiert, trotzdem die angeforderte Version speichern
    # (Audit: was konfiguriert war). Dateiname kann abweichen.
    return text, ver
