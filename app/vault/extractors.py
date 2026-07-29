"""Document-Extraktion (E18-1, E18-2, E18-3, E18-5).

Engine+Adapter-Muster fuer Multi-Format-Ingestion: Jeder ``DocumentExtractor``
liest eine bestimmte Dateigruppe (read-only) und liefert reinen Text fuer den
Vault-Index (E5-1) und spaeteres Retrieval/RAG (E17).

Aktuell Tier 1 (direkt text-basiert): Markdown, Plain-Text, PDF (Text-Layer)
sowie Office-Formate Word (.docx) und PowerPoint (.pptx).
OCR (E18-5) dockt als optionaler Adapter an (Bilder + PDF-Scans ohne Text-Layer),
wenn Tesseract/pytesseract installiert sind. Vision (E18-6) spaeter analog.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from docx import Document
from pptx import Presentation
from pypdf import PdfReader

from app.vault.ocr import IMAGE_OCR_EXTENSIONS, ocr_image, ocr_pdf, ocr_ready, pdf_ocr_ready
from app.vault.reader import _parse_frontmatter

logger = logging.getLogger(__name__)

# Marker fuer PDFs ohne extrahierbaren Text-Layer (Scans) — Aufhaenger fuer OCR (E18-5).
PDF_NO_TEXT_TYPE = "pdf_no_text"
PDF_OCR_TYPE = "pdf_ocr"
IMAGE_OCR_TYPE = "image_ocr"


@dataclass(frozen=True)
class ExtractedDocument:
    """Ergebnis einer Extraktion: reiner Text plus Metadaten."""

    title: str
    text: str
    category: str = ""
    doc_type: str = "text"


class DocumentExtractor(ABC):
    """Adapter-Interface: liest eine Datei und liefert ``ExtractedDocument``."""

    doc_type: ClassVar[str]
    extensions: ClassVar[tuple[str, ...]]

    @abstractmethod
    def extract(self, path: Path) -> ExtractedDocument:
        """Extrahiert Text/Metadaten aus ``path`` (wird nie veraendert)."""


def _strip_frontmatter(content: str) -> str:
    if not content.startswith("---"):
        return content
    parts = content.split("---", 2)
    return parts[2] if len(parts) > 2 else content


class MarkdownExtractor(DocumentExtractor):
    doc_type = "markdown"
    extensions = (".md", ".markdown")

    def extract(self, path: Path) -> ExtractedDocument:
        content = path.read_text(encoding="utf-8")
        meta = _parse_frontmatter(content)
        title = meta.get("title") or path.stem
        return ExtractedDocument(
            title=title,
            text=_strip_frontmatter(content),
            category=meta.get("category", ""),
            doc_type=self.doc_type,
        )


class PlainTextExtractor(DocumentExtractor):
    doc_type = "text"
    extensions = (".txt", ".text", ".log")

    def extract(self, path: Path) -> ExtractedDocument:
        return ExtractedDocument(
            title=path.stem,
            text=path.read_text(encoding="utf-8"),
            doc_type=self.doc_type,
        )


class PdfExtractor(DocumentExtractor):
    doc_type = "pdf"
    extensions = (".pdf",)

    def extract(self, path: Path) -> ExtractedDocument:
        title = path.stem
        text_parts: list[str] = []
        try:
            reader = PdfReader(str(path))
            meta_title = reader.metadata.title if reader.metadata else None
            if meta_title and meta_title.strip():
                title = meta_title.strip()
            for page in reader.pages:
                extracted = page.extract_text() or ""
                if extracted.strip():
                    text_parts.append(extracted.strip())
        except Exception as exc:  # noqa: BLE001 — defekte PDFs duerfen den Scan nicht abbrechen
            logger.warning("PDF-Extraktion fehlgeschlagen fuer %s: %s", path, exc)

        text = "\n\n".join(text_parts).strip()
        if text:
            return ExtractedDocument(title=title, text=text, doc_type=self.doc_type)

        # Kein Text-Layer (Scan) → optional OCR (E18-5), sonst pdf_no_text markieren.
        if pdf_ocr_ready():
            ocr_text = ocr_pdf(path)
            if ocr_text:
                return ExtractedDocument(title=title, text=ocr_text, doc_type=PDF_OCR_TYPE)

        return ExtractedDocument(title=title, text="", doc_type=PDF_NO_TEXT_TYPE)


def _doc_core_title(properties) -> str | None:
    """Titel aus Office-Core-Properties, falls gepflegt."""
    title = getattr(properties, "title", None)
    return title.strip() if title and title.strip() else None


class DocxExtractor(DocumentExtractor):
    """Word-Dokumente (.docx). Aeltere .doc-Binaerformate werden nicht unterstuetzt."""

    doc_type = "docx"
    extensions = (".docx",)

    def extract(self, path: Path) -> ExtractedDocument:
        title = path.stem
        text_parts: list[str] = []
        try:
            document = Document(str(path))
            title = _doc_core_title(document.core_properties) or title
            for paragraph in document.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            # Tabellen separat anhaengen — Zeugnisse/Rechnungen liegen oft darin.
            for table in document.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if cells:
                        text_parts.append(" | ".join(cells))
        except Exception as exc:  # noqa: BLE001 — defekte Dateien duerfen den Scan nicht abbrechen
            logger.warning("DOCX-Extraktion fehlgeschlagen fuer %s: %s", path, exc)

        return ExtractedDocument(
            title=title, text="\n\n".join(text_parts).strip(), doc_type=self.doc_type
        )


class PptxExtractor(DocumentExtractor):
    """PowerPoint-Praesentationen (.pptx): Folientext + Sprechernotizen."""

    doc_type = "pptx"
    extensions = (".pptx",)

    def extract(self, path: Path) -> ExtractedDocument:
        title = path.stem
        text_parts: list[str] = []
        try:
            presentation = Presentation(str(path))
            title = _doc_core_title(presentation.core_properties) or title
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame and shape.text_frame.text.strip():
                        text_parts.append(shape.text_frame.text.strip())
                if slide.has_notes_slide:
                    notes = slide.notes_slide.notes_text_frame
                    if notes is not None and notes.text.strip():
                        text_parts.append(notes.text.strip())
        except Exception as exc:  # noqa: BLE001 — defekte Dateien duerfen den Scan nicht abbrechen
            logger.warning("PPTX-Extraktion fehlgeschlagen fuer %s: %s", path, exc)

        return ExtractedDocument(
            title=title, text="\n\n".join(text_parts).strip(), doc_type=self.doc_type
        )


class ImageOcrExtractor(DocumentExtractor):
    """Foto-/Scan-Bilder via Tesseract — nur aktiv, wenn OCR installiert ist."""

    doc_type = IMAGE_OCR_TYPE
    extensions = tuple(sorted(IMAGE_OCR_EXTENSIONS))

    def extract(self, path: Path) -> ExtractedDocument:
        text = ocr_image(path) if ocr_ready() else ""
        return ExtractedDocument(title=path.stem, text=text, doc_type=self.doc_type)


# Reihenfolge bestimmt die Aufloesung bei mehrdeutigen Endungen (hier eindeutig).
_EXTRACTORS: tuple[DocumentExtractor, ...] = (
    MarkdownExtractor(),
    PlainTextExtractor(),
    PdfExtractor(),
    DocxExtractor(),
    PptxExtractor(),
)

_IMAGE_OCR_EXTRACTOR = ImageOcrExtractor()

# Immer-verfuegbare Endungen (ohne optionales OCR).
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    ext for extractor in _EXTRACTORS for ext in extractor.extensions
)


def get_extractor(path: Path) -> DocumentExtractor | None:
    """Liefert den passenden Extractor oder ``None`` fuer nicht unterstuetzte Typen."""
    suffix = path.suffix.lower()
    for extractor in _EXTRACTORS:
        if suffix in extractor.extensions:
            return extractor
    if suffix in IMAGE_OCR_EXTENSIONS and ocr_ready():
        return _IMAGE_OCR_EXTRACTOR
    return None


def is_supported(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return True
    return suffix in IMAGE_OCR_EXTENSIONS and ocr_ready()
