"""Dokument-/Foto-Capture aus Telegram (E22-2).

Extrahiert Text aus hochgeladenen Dateien über die E18-Extractors
(PDF/Office/Text/Markdown, Bilder via OCR/Vision) und bereitet ihn für die
normale Capture-Pipeline auf. Die Originaldatei wird **nicht** im Vault
abgelegt — nur der extrahierte Inhalt wird zur Notiz.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.vault.extractors import get_extractor, image_extraction_ready, is_supported

logger = logging.getLogger(__name__)

# Obergrenze fuer den extrahierten Text im Capture (LLM-Kosten/Prompt-Groesse).
MAX_EXTRACT_CHARS = 20_000

TRUNCATION_MARKER = "\n\n[… Inhalt gekürzt]"


def supported_document(file_name: str) -> bool:
    """Ob die Datei-Endung von den E18-Extractors abgedeckt ist."""
    return is_supported(Path(file_name.strip() or "unbenannt"))


def photo_extraction_ready() -> bool:
    """Fotos brauchen OCR (Tesseract) oder Vision — beides optional."""
    return image_extraction_ready()


def extract_document_text(data: bytes, file_name: str) -> str:
    """Schreibt ``data`` in eine Temp-Datei und extrahiert Text (E18).

    Liefert ``""`` wenn kein Extractor passt oder nichts extrahierbar ist.
    """
    suffix = Path(file_name).suffix.lower() or ".bin"
    with tempfile.TemporaryDirectory(prefix="seiton-doc-") as tmp:
        path = Path(tmp) / f"upload{suffix}"
        path.write_bytes(data)
        extractor = get_extractor(path)
        if extractor is None:
            logger.info("Kein Extractor fuer %s", file_name)
            return ""
        text = extractor.extract(path).text.strip()
    if len(text) > MAX_EXTRACT_CHARS:
        text = text[:MAX_EXTRACT_CHARS].rstrip() + TRUNCATION_MARKER
    return text


def compose_capture_text(
    extracted: str, *, file_name: str, caption: str | None
) -> str:
    """Baut den Capture-Text: Caption des Users + Quelle + Inhalt."""
    parts: list[str] = []
    cap = (caption or "").strip()
    if cap:
        parts.append(cap)
    parts.append(f"Aus Datei: {file_name}")
    parts.append(extracted)
    return "\n\n".join(parts)
