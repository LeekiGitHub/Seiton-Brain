"""Optionale Vision-Beschreibung fuer Bilder (E18-6).

Nutzt die OpenAI Chat-API mit Bild-Input (sync), damit der synchrone
DocumentExtractor-Pfad den Index befuellen kann. Standardmaessig aus
(Kosten) — analog zu Embeddings.
"""

from __future__ import annotations

import base64
import json
import logging
import mimetypes
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError

from app.config import settings
from app.llm.parser import MAX_PARSE_ATTEMPTS
from app.llm.prompts import load_prompt
from app.llm.schemas import VisionImageResult
from app.llm.tags import normalize_tags

logger = logging.getLogger(__name__)

MAX_VISION_TAGS = 8

_MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def vision_ready() -> bool:
    """True, wenn Vision konfiguriert und ein OpenAI-API-Key gesetzt ist."""
    return bool(settings.seiton_vision_enabled) and bool(settings.openai_api_key)


def _vision_model() -> str:
    model = (settings.seiton_vision_model or "").strip()
    return model or settings.openai_model


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _MIME_BY_SUFFIX:
        return _MIME_BY_SUFFIX[suffix]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def format_vision_text(result: VisionImageResult) -> str:
    """Beschreibung + Tags als durchsuchbarer Index-Text."""
    parts = [result.description.strip()]
    tags = normalize_tags(result.tags, max_tags=MAX_VISION_TAGS)
    if tags:
        parts.append("Tags: " + ", ".join(tags))
    return "\n\n".join(p for p in parts if p)


def parse_vision_json(content: str) -> VisionImageResult:
    data = json.loads(content)
    return VisionImageResult.model_validate(data)


def describe_image(path: Path, *, client: OpenAI | None = None) -> VisionImageResult | None:
    """Bild → Beschreibung/Tags. ``None`` bei Fehler oder wenn Vision aus ist."""
    if not vision_ready():
        return None

    try:
        raw = path.read_bytes()
    except OSError as exc:
        logger.warning("Vision: Bild nicht lesbar %s: %s", path, exc)
        return None

    if not raw:
        return None

    b64 = base64.b64encode(raw).decode("ascii")
    mime = _mime_type(path)
    prompt, _ = load_prompt("vision")
    data_url = f"data:{mime};base64,{b64}"

    openai_client = client or OpenAI(api_key=settings.openai_api_key)
    last_error: Exception | None = None

    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        try:
            response = openai_client.chat.completions.create(
                model=_vision_model(),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            result = parse_vision_json(content)
            result.tags = normalize_tags(result.tags, max_tags=MAX_VISION_TAGS)
            if not result.description.strip():
                logger.warning("Vision: leere Beschreibung fuer %s", path)
                return None
            return result
        except (json.JSONDecodeError, ValidationError, Exception) as exc:  # noqa: BLE001
            last_error = exc
            logger.warning(
                "Vision parse/API failed (attempt %d/%d) fuer %s: %s",
                attempt,
                MAX_PARSE_ATTEMPTS,
                path,
                exc,
            )

    logger.warning(
        "Vision fehlgeschlagen fuer %s nach %d Versuchen: %s",
        path,
        MAX_PARSE_ATTEMPTS,
        last_error,
    )
    return None
