from pathlib import Path
from unittest.mock import MagicMock, patch

from pypdf import PdfWriter

from app.vault.extractors import (
    PDF_NO_TEXT_TYPE,
    SUPPORTED_EXTENSIONS,
    MarkdownExtractor,
    PdfExtractor,
    PlainTextExtractor,
    get_extractor,
    is_supported,
)


def test_markdown_extractor_parses_frontmatter(tmp_path: Path):
    note = tmp_path / "Idea.md"
    note.write_text(
        "---\ntitle: Fitness App\ncategory: idea\n---\n\n# Heading\n\nTrack workouts.",
        encoding="utf-8",
    )
    doc = MarkdownExtractor().extract(note)
    assert doc.title == "Fitness App"
    assert doc.category == "idea"
    assert doc.doc_type == "markdown"
    assert "Track workouts." in doc.text
    assert "title: Fitness App" not in doc.text  # frontmatter entfernt


def test_markdown_extractor_falls_back_to_stem(tmp_path: Path):
    note = tmp_path / "No Frontmatter.md"
    note.write_text("Just body text.", encoding="utf-8")
    doc = MarkdownExtractor().extract(note)
    assert doc.title == "No Frontmatter"
    assert doc.category == ""
    assert doc.text == "Just body text."


def test_plaintext_extractor(tmp_path: Path):
    note = tmp_path / "Rechnung 2026.txt"
    note.write_text("Betrag: 42 EUR", encoding="utf-8")
    doc = PlainTextExtractor().extract(note)
    assert doc.title == "Rechnung 2026"
    assert doc.text == "Betrag: 42 EUR"
    assert doc.doc_type == "text"
    assert doc.category == ""


def test_get_extractor_resolves_by_suffix(tmp_path: Path):
    assert isinstance(get_extractor(tmp_path / "a.md"), MarkdownExtractor)
    assert isinstance(get_extractor(tmp_path / "a.MARKDOWN"), MarkdownExtractor)
    assert isinstance(get_extractor(tmp_path / "a.txt"), PlainTextExtractor)
    assert isinstance(get_extractor(tmp_path / "scan.pdf"), PdfExtractor)
    assert isinstance(get_extractor(tmp_path / "doc.PDF"), PdfExtractor)
    assert get_extractor(tmp_path / "photo.jpg") is None


def test_is_supported_and_extensions():
    assert is_supported(Path("a.md"))
    assert is_supported(Path("a.txt"))
    assert is_supported(Path("a.pdf"))
    assert not is_supported(Path("a.jpg"))
    assert ".md" in SUPPORTED_EXTENSIONS
    assert ".txt" in SUPPORTED_EXTENSIONS
    assert ".pdf" in SUPPORTED_EXTENSIONS
    assert ".jpg" not in SUPPORTED_EXTENSIONS


def _fake_pdf_reader(pages_text: list[str], title: str | None = None) -> MagicMock:
    reader = MagicMock()
    reader.metadata = MagicMock(title=title)
    reader.pages = [MagicMock(extract_text=MagicMock(return_value=t)) for t in pages_text]
    return reader


def test_pdf_extractor_with_text_layer(tmp_path: Path):
    pdf = tmp_path / "Bewerbung.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with patch(
        "app.vault.extractors.PdfReader",
        return_value=_fake_pdf_reader(["Seite eins.", "Seite zwei."], title="Anschreiben"),
    ):
        doc = PdfExtractor().extract(pdf)
    assert doc.title == "Anschreiben"  # aus PDF-Metadaten
    assert doc.doc_type == "pdf"
    assert "Seite eins." in doc.text
    assert "Seite zwei." in doc.text


def test_pdf_extractor_title_falls_back_to_stem(tmp_path: Path):
    pdf = tmp_path / "Zeugnis 2024.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with patch(
        "app.vault.extractors.PdfReader",
        return_value=_fake_pdf_reader(["Inhalt"], title=None),
    ):
        doc = PdfExtractor().extract(pdf)
    assert doc.title == "Zeugnis 2024"


def test_pdf_extractor_no_text_layer_marks_for_ocr(tmp_path: Path):
    """Echter Scan ohne Text-Layer (leere Seite) → pdf_no_text."""
    pdf = tmp_path / "Scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with pdf.open("wb") as fh:
        writer.write(fh)

    doc = PdfExtractor().extract(pdf)
    assert doc.doc_type == PDF_NO_TEXT_TYPE
    assert doc.text == ""
    assert doc.title == "Scan"


def test_pdf_extractor_corrupt_file_does_not_raise(tmp_path: Path):
    pdf = tmp_path / "kaputt.pdf"
    pdf.write_bytes(b"not really a pdf")
    doc = PdfExtractor().extract(pdf)
    assert doc.doc_type == PDF_NO_TEXT_TYPE
    assert doc.text == ""
