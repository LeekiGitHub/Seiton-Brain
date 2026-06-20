"""Document-Extraktion (E18-1, E18-2).

Engine+Adapter-Muster fuer Multi-Format-Ingestion: Jeder ``DocumentExtractor``
liest eine bestimmte Dateigruppe (read-only) und liefert reinen Text fuer den
Vault-Index (E5-1) und spaeteres Retrieval/RAG (E17).

Aktuell Tier 1 (direkt text-basiert): Markdown, Plain-Text und PDF (Text-Layer).
Office (E18-3), OCR (E18-5) und Vision (E18-6) docken hier als weitere
Extractoren an, ohne den Index-Code zu aendern.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from pypdf import PdfReader

from app.vault.reader import _parse_frontmatter

logger = logging.getLogger(__name__)

# Marker fuer PDFs ohne extrahierbaren Text-Layer (Scans) — Aufhaenger fuer OCR (E18-5).
PDF_NO_TEXT_TYPE = "pdf_no_text"


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
        # Kein Text-Layer (Scan) → fuer OCR (E18-5) markieren statt leer indexieren.
        doc_type = self.doc_type if text else PDF_NO_TEXT_TYPE
        return ExtractedDocument(title=title, text=text, doc_type=doc_type)


# Reihenfolge bestimmt die Aufloesung bei mehrdeutigen Endungen (hier eindeutig).
_EXTRACTORS: tuple[DocumentExtractor, ...] = (
    MarkdownExtractor(),
    PlainTextExtractor(),
    PdfExtractor(),
)

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    ext for extractor in _EXTRACTORS for ext in extractor.extensions
)


def get_extractor(path: Path) -> DocumentExtractor | None:
    """Liefert den passenden Extractor oder ``None`` fuer nicht unterstuetzte Typen."""
    suffix = path.suffix.lower()
    for extractor in _EXTRACTORS:
        if suffix in extractor.extensions:
            return extractor
    return None


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS
