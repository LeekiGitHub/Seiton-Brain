"""Document/photo capture from Telegram (E22-2).

Extracts text from uploaded files via the E18 extractors
(PDF/Office/text/Markdown, images via OCR/Vision) and prepares it for the
normal capture pipeline. The original file is **not** stored in the vault —
only the extracted content becomes a note.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.vault.extractors import get_extractor, image_extraction_ready, is_supported

logger = logging.getLogger(__name__)

# Cap extracted text in capture (LLM cost / prompt size).
MAX_EXTRACT_CHARS = 20_000

TRUNCATION_MARKER = "\n\n[… Inhalt gekürzt]"


def supported_document(file_name: str) -> bool:
    """Whether the file extension is covered by the E18 extractors."""
    return is_supported(Path(file_name.strip() or "unbenannt"))


def photo_extraction_ready() -> bool:
    """Photos need OCR (Tesseract) or Vision — both optional."""
    return image_extraction_ready()


def extract_document_text(data: bytes, file_name: str) -> str:
    """Write ``data`` to a temp file and extract text (E18).

    Returns ``""`` if no extractor matches or nothing is extractable.
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
    """Build capture text: user caption + source + content."""
    parts: list[str] = []
    cap = (caption or "").strip()
    if cap:
        parts.append(cap)
    parts.append(f"Aus Datei: {file_name}")
    parts.append(extracted)
    return "\n\n".join(parts)
