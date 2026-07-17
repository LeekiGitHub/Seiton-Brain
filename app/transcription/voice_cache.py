"""Temporaerer Voice-Cache bis erfolgreiche Verarbeitung (E6-2)."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def _cache_dir() -> Path:
    path = Path(settings.telegram_voice_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_name(file_id: str) -> str:
    digest = hashlib.sha256(file_id.encode("utf-8")).hexdigest()[:40]
    return f"{digest}.ogg"


def voice_cache_path(file_id: str) -> Path:
    return _cache_dir() / _safe_name(file_id)


def load_voice_cache(file_id: str) -> bytes | None:
    path = voice_cache_path(file_id)
    if not path.is_file():
        return None
    try:
        data = path.read_bytes()
    except OSError as exc:
        logger.warning("Voice-Cache lesen fehlgeschlagen %s: %s", path, exc)
        return None
    if not data:
        return None
    logger.info("Voice-Cache Treffer file_id=%s… size=%s", file_id[:12], len(data))
    return data


def save_voice_cache(file_id: str, audio_bytes: bytes) -> Path:
    path = voice_cache_path(file_id)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_bytes(audio_bytes)
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    logger.debug("Voice-Cache geschrieben %s (%s bytes)", path.name, len(audio_bytes))
    return path


def delete_voice_cache(file_id: str) -> None:
    path = voice_cache_path(file_id)
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Voice-Cache löschen fehlgeschlagen %s: %s", path, exc)
