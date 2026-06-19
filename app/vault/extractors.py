"""Document-Extraktion (E18-1).

Engine+Adapter-Muster fuer Multi-Format-Ingestion: Jeder ``DocumentExtractor``
liest eine bestimmte Dateigruppe (read-only) und liefert reinen Text fuer den
Vault-Index (E5-1) und spaeteres Retrieval/RAG (E17).

Aktuell Tier 1 (direkt text-basiert): Markdown und Plain-Text. PDF (E18-2),
Office (E18-3), OCR (E18-5) und Vision (E18-6) docken hier als weitere
Extractoren an, ohne den Index-Code zu aendern.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from app.vault.reader import _parse_frontmatter


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


# Reihenfolge bestimmt die Aufloesung bei mehrdeutigen Endungen (hier eindeutig).
_EXTRACTORS: tuple[DocumentExtractor, ...] = (
    MarkdownExtractor(),
    PlainTextExtractor(),
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
