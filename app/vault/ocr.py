"""Optional OCR helper (E18-5) via Tesseract.

Soft imports: without ``pytesseract`` / Pillow / (for PDFs) ``pypdfium2`` and
without an installed Tesseract binary, OCR stays disabled — index and text
extractors continue unchanged.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Image formats for the image OCR adapter.
IMAGE_OCR_EXTENSIONS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}
)


@lru_cache(maxsize=1)
def is_ocr_available() -> bool:
    """True if Python deps and the Tesseract binary are usable."""
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401

        pytesseract.get_tesseract_version()
        return True
    except Exception as exc:  # noqa: BLE001 — optional path
        logger.debug("OCR nicht verfuegbar: %s", exc)
        return False


def is_pdf_ocr_available() -> bool:
    """PDF OCR additionally needs pypdfium2 to render pages."""
    if not is_ocr_available():
        return False
    try:
        import pypdfium2  # noqa: F401

        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("PDF-OCR (pypdfium2) nicht verfuegbar: %s", exc)
        return False


def ocr_ready() -> bool:
    """Config + soft deps: may OCR be used actively?"""
    from app.config import settings

    return bool(settings.seiton_ocr_enabled) and is_ocr_available()


def pdf_ocr_ready() -> bool:
    from app.config import settings

    return bool(settings.seiton_ocr_enabled) and is_pdf_ocr_available()


def _ocr_lang() -> str:
    from app.config import settings

    lang = (settings.seiton_ocr_lang or "deu+eng").strip()
    return lang or "deu+eng"


def ocr_image(path: Path) -> str:
    """OCR on an image file. Empty on error / when disabled."""
    if not ocr_ready():
        return ""
    try:
        import pytesseract
        from PIL import Image

        with Image.open(path) as image:
            # RGB forces Tesseract-compatible input (e.g. RGBA/P mode).
            rgb = image.convert("RGB")
            text = pytesseract.image_to_string(rgb, lang=_ocr_lang())
        return (text or "").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR fehlgeschlagen fuer Bild %s: %s", path, exc)
        return ""


def ocr_pdf(path: Path, *, scale: float = 2.0) -> str:
    """OCR all pages of a PDF (scan without text layer)."""
    if not pdf_ocr_ready():
        return ""
    try:
        import pypdfium2
        import pytesseract

        pdf = pypdfium2.PdfDocument(str(path))
        parts: list[str] = []
        try:
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    bitmap = page.render(scale=scale)
                    pil_image = bitmap.to_pil()
                    text = pytesseract.image_to_string(
                        pil_image.convert("RGB"), lang=_ocr_lang()
                    )
                    if text and text.strip():
                        parts.append(text.strip())
                finally:
                    page.close()
        finally:
            pdf.close()
        return "\n\n".join(parts).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR fehlgeschlagen fuer PDF %s: %s", path, exc)
        return ""


def clear_ocr_availability_cache() -> None:
    """Test helper: clear ``is_ocr_available`` cache."""
    is_ocr_available.cache_clear()
