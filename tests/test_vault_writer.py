from app.llm.schemas import ClassificationResult
from app.vault.writer import _related_section, _sanitize_filename, write_note


def test_sanitize_filename():
    assert _sanitize_filename('Bad/name:here?') == "Badnamehere"


def test_related_section_empty():
    assert _related_section([]) == ""


def test_related_section_with_links():
    section = _related_section(["Note A", "Note B"])
    assert "[[Note A]]" in section
    assert "[[Note B]]" in section
    assert "## Related" in section


def test_write_note(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    result = ClassificationResult(
        category="idea",
        title="Fitness App",
        summary="An app for tracking workouts.",
        related=["Existing Note"],
    )

    filepath = write_note(result)
    assert filepath.exists()
    assert filepath.parent.name == "Ideas"
    content = filepath.read_text(encoding="utf-8")
    assert "title: Fitness App" in content
    assert "category: idea" in content
    assert "An app for tracking workouts." in content
    assert "[[Existing Note]]" in content
