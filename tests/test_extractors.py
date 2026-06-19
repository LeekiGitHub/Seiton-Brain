from pathlib import Path

from app.vault.extractors import (
    SUPPORTED_EXTENSIONS,
    MarkdownExtractor,
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
    assert get_extractor(tmp_path / "scan.pdf") is None
    assert get_extractor(tmp_path / "photo.jpg") is None


def test_is_supported_and_extensions():
    assert is_supported(Path("a.md"))
    assert is_supported(Path("a.txt"))
    assert not is_supported(Path("a.pdf"))
    assert ".md" in SUPPORTED_EXTENSIONS
    assert ".txt" in SUPPORTED_EXTENSIONS
    assert ".pdf" not in SUPPORTED_EXTENSIONS
