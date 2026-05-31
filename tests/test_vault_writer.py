from app.llm.schemas import ClassificationResult
from app.vault.writer import (
    _next_available_path,
    _related_section,
    _sanitize_filename,
    write_note,
)


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


def test_next_available_path_no_collision(tmp_path):
    assert _next_available_path(tmp_path, "Foo") == tmp_path / "Foo.md"


def test_next_available_path_one_collision(tmp_path):
    (tmp_path / "Foo.md").write_text("x")
    assert _next_available_path(tmp_path, "Foo") == tmp_path / "Foo (2).md"


def test_next_available_path_many_collisions(tmp_path):
    (tmp_path / "Foo.md").write_text("x")
    (tmp_path / "Foo (2).md").write_text("x")
    (tmp_path / "Foo (3).md").write_text("x")
    assert _next_available_path(tmp_path, "Foo") == tmp_path / "Foo (4).md"


def test_write_note_does_not_overwrite_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    base = ClassificationResult(
        category="idea",
        title="Fitness App",
        summary="First version.",
    )
    update = ClassificationResult(
        category="idea",
        title="Fitness App",
        summary="A second, different note with the same title.",
    )

    first = write_note(base)
    second = write_note(update)

    assert first.name == "Fitness App.md"
    assert second.name == "Fitness App (2).md"
    assert first.read_text(encoding="utf-8") != second.read_text(encoding="utf-8")
    assert "First version." in first.read_text(encoding="utf-8")
    assert "A second, different note" in second.read_text(encoding="utf-8")
