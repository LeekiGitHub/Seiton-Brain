from datetime import date

import pytest

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.writer import (
    _next_available_path,
    _related_section,
    _sanitize_filename,
    _tags_frontmatter_line,
    append_to_note,
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


def test_tags_frontmatter_line_empty():
    assert _tags_frontmatter_line([]) == ""


def test_tags_frontmatter_line_inline_list():
    line = _tags_frontmatter_line(["idea", "side-project"])
    assert line == "tags: [idea, side-project]\n"


def test_write_note_includes_tags_in_frontmatter(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    result = ClassificationResult(
        category="idea",
        title="Tagged Note",
        summary="Body.",
        tags=["idea", "fitness"],
    )
    path = write_note(result)
    content = path.read_text(encoding="utf-8")
    assert "tags: [idea, fitness]" in content


def test_write_note_omits_tags_line_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    result = ClassificationResult(
        category="note", title="Untagged", summary="Body.",
    )
    path = write_note(result)
    content = path.read_text(encoding="utf-8")
    assert "tags:" not in content


def test_write_note(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
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
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
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


def test_append_to_note_adds_update_section(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(
        category="idea",
        title="Fitness App",
        summary="Initial idea.",
    )
    original = write_note(base)
    relative = str(original.relative_to(tmp_path))

    update = ClassificationResult(
        category="idea",
        title="Workout log feature",
        summary="Add daily workout logging.",
        action="append",
        target_title="Fitness App",
    )
    result_path = append_to_note(relative, update)

    assert result_path == original
    content = original.read_text(encoding="utf-8")
    assert "Initial idea." in content
    assert f"## Update {date.today().isoformat()}" in content
    assert "Add daily workout logging." in content


def test_append_to_note_includes_related_section(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(
        category="note", title="Project X", summary="Start."
    )
    path = write_note(base)
    relative = str(path.relative_to(tmp_path))

    update = ClassificationResult(
        category="note",
        title="More on X",
        summary="Linking related work.",
        related=["Other Note"],
        action="append",
        target_title="Project X",
    )
    append_to_note(relative, update)
    content = path.read_text(encoding="utf-8")
    assert "[[Other Note]]" in content


def test_append_to_note_raises_if_file_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    update = ClassificationResult(
        category="note",
        title="X",
        summary="Y",
        action="append",
        target_title="Nope",
    )
    with pytest.raises(FileNotFoundError):
        append_to_note("Notes/does-not-exist.md", update)
