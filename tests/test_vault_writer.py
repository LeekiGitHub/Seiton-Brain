from datetime import date

import pytest

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.writer import (
    _atomic_write,
    _next_available_path,
    _parse_frontmatter,
    _related_section,
    _render_frontmatter,
    _sanitize_filename,
    _tags_frontmatter_line,
    append_to_note,
    delete_note,
    save_note_content,
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


def test_parse_frontmatter_inline_tags():
    text = "---\ntitle: Foo\ntags: [a, b]\n---\nBody\n"
    fm, body = _parse_frontmatter(text)
    assert fm == {"title": "Foo", "tags": ["a", "b"]}
    assert body == "Body\n"


def test_parse_frontmatter_block_tags():
    text = "---\ntitle: Foo\ntags:\n- a\n- b\n---\nBody\n"
    fm, body = _parse_frontmatter(text)
    assert fm is not None
    assert fm["tags"] == ["a", "b"]
    assert body == "Body\n"


def test_parse_frontmatter_no_frontmatter():
    fm, body = _parse_frontmatter("Just a body\n")
    assert fm is None
    assert body == "Just a body\n"


def test_parse_frontmatter_unterminated():
    fm, body = _parse_frontmatter("---\ntitle: Foo\nno closing fence\n")
    assert fm is None


def test_render_frontmatter_preserves_canonical_order():
    rendered = _render_frontmatter(
        {
            "tags": ["x"],
            "title": "T",
            "extra": "keep",
            "created": "2026-01-01",
        }
    )
    assert rendered == (
        "---\n"
        "title: T\n"
        "created: 2026-01-01\n"
        "tags: [x]\n"
        "extra: keep\n"
        "---\n"
    )


def test_render_frontmatter_skips_empty_tag_list():
    rendered = _render_frontmatter({"title": "T", "tags": []})
    assert "tags:" not in rendered


def test_append_to_note_sets_updated_date(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(
        category="idea", title="Fitness App", summary="Start.", tags=["idea"]
    )
    path = write_note(base)
    relative = str(path.relative_to(tmp_path))

    update = ClassificationResult(
        category="idea",
        title="More",
        summary="Add feature.",
        action="append",
        target_title="Fitness App",
    )
    append_to_note(relative, update)

    content = path.read_text(encoding="utf-8")
    assert f"updated: {date.today().isoformat()}" in content
    assert content.count("---") >= 2, "frontmatter fences must remain"


def test_append_to_note_merges_tags_without_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(
        category="idea",
        title="Project X",
        summary="Start.",
        tags=["idea", "fitness"],
    )
    path = write_note(base)
    relative = str(path.relative_to(tmp_path))

    update = ClassificationResult(
        category="idea",
        title="More on X",
        summary="More.",
        tags=["fitness", "training"],
        action="append",
        target_title="Project X",
    )
    append_to_note(relative, update)

    content = path.read_text(encoding="utf-8")
    assert "tags: [idea, fitness, training]" in content
    assert content.count("fitness") == 1, "fitness must not be duplicated in tags"


def test_append_to_note_adds_tags_when_original_had_none(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(category="note", title="Untagged", summary="Body.")
    path = write_note(base)
    relative = str(path.relative_to(tmp_path))

    update = ClassificationResult(
        category="note",
        title="Add tags now",
        summary="Update.",
        tags=["new"],
        action="append",
        target_title="Untagged",
    )
    append_to_note(relative, update)

    content = path.read_text(encoding="utf-8")
    assert "tags: [new]" in content


def test_append_to_note_keeps_body_intact(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    base = ClassificationResult(
        category="idea", title="Body Test", summary="Original body.", tags=["x"]
    )
    path = write_note(base)
    relative = str(path.relative_to(tmp_path))

    update = ClassificationResult(
        category="idea",
        title="More",
        summary="Update text.",
        action="append",
        target_title="Body Test",
    )
    append_to_note(relative, update)

    content = path.read_text(encoding="utf-8")
    assert "Original body." in content
    assert "Update text." in content
    assert f"## Update {date.today().isoformat()}" in content


def test_atomic_write_creates_file_with_content(tmp_path):
    target = tmp_path / "sub" / "note.md"
    _atomic_write(target, "hello\nworld\n")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "hello\nworld\n"


def test_atomic_write_overwrites_existing_file(tmp_path):
    target = tmp_path / "note.md"
    target.write_text("OLD")
    _atomic_write(target, "NEW")
    assert target.read_text(encoding="utf-8") == "NEW"


def test_atomic_write_leaves_no_tempfiles_on_success(tmp_path):
    target = tmp_path / "note.md"
    _atomic_write(target, "x")
    leftovers = [
        p for p in tmp_path.iterdir() if p.name.startswith(".") and p.name.endswith(".tmp")
    ]
    assert leftovers == []


def test_atomic_write_preserves_original_on_replace_failure(
    tmp_path, monkeypatch
):
    """Wenn os.replace failt, muss die Zieldatei unveraendert bleiben
    und kein Tempfile zurueckbleiben."""
    target = tmp_path / "note.md"
    target.write_text("ORIGINAL CONTENT")

    import app.vault.filesystem as fs_mod

    def boom(*_a, **_kw):
        raise OSError("simulated disk full at replace")

    monkeypatch.setattr(fs_mod.os, "replace", boom)

    with pytest.raises(OSError, match="simulated disk full"):
        _atomic_write(target, "NEW CONTENT")

    # Original ist intakt
    assert target.read_text(encoding="utf-8") == "ORIGINAL CONTENT"
    # Tempfile wurde aufgeraeumt
    tmpfiles = [
        p for p in tmp_path.iterdir()
        if p.name.startswith(".note.md.") and p.name.endswith(".tmp")
    ]
    assert tmpfiles == [], f"Tempfile-Leak: {tmpfiles}"


def test_atomic_write_cleans_up_tempfile_on_write_failure(tmp_path, monkeypatch):
    """Wenn das Schreiben in den Tempfile failt (z.B. Disk-Full mitten drin),
    darf kein halber Tempfile zurueckbleiben und das Ziel nicht entstehen."""
    target = tmp_path / "note.md"

    import app.vault.filesystem as fs_mod
    original_fdopen = fs_mod.os.fdopen

    def evil_fdopen(*args, **kwargs):
        fh = original_fdopen(*args, **kwargs)

        def broken_write(_text):
            raise OSError("simulated disk full mid-write")

        fh.write = broken_write  # type: ignore[method-assign]
        return fh

    monkeypatch.setattr(fs_mod.os, "fdopen", evil_fdopen)

    with pytest.raises(OSError, match="mid-write"):
        _atomic_write(target, "anything")

    assert not target.exists()
    leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


def test_write_note_is_atomic_under_replace_failure(tmp_path, monkeypatch):
    """End-to-end: write_note darf bei Replace-Fehler keine halbe Datei
    am Ziel hinterlassen."""
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))

    import app.vault.filesystem as fs_mod

    def boom(*_a, **_kw):
        raise OSError("disk full")

    monkeypatch.setattr(fs_mod.os, "replace", boom)

    result = ClassificationResult(category="note", title="Crashy", summary="x")
    with pytest.raises(OSError):
        write_note(result)

    target = tmp_path / "Notes" / "Crashy.md"
    assert not target.exists()


def test_delete_note_removes_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    target = tmp_path / "Notes" / "Foo.md"
    target.write_text("x")
    assert delete_note("Notes/Foo.md") is True
    assert not target.exists()


def test_delete_note_returns_false_for_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    assert delete_note("Notes/does-not-exist.md") is False


def test_delete_note_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    assert delete_note("../../../etc/passwd") is False


def test_save_note_content_overwrites_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    target = tmp_path / "Notes" / "Edit.md"
    target.write_text("old")
    save_note_content("Notes/Edit.md", "new body")
    assert target.read_text(encoding="utf-8") == "new body"


def test_save_note_content_raises_for_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        save_note_content("Notes/missing.md", "x")


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


def test_append_to_note_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    update = ClassificationResult(
        category="note",
        title="X",
        summary="Y",
        action="append",
        target_title="Nope",
    )
    with pytest.raises(ValueError, match="Invalid vault path"):
        append_to_note("../../../etc/passwd", update)


def test_sanitize_frontmatter_scalar_strips_newlines_and_delimiter():
    from app.vault.filesystem import _sanitize_frontmatter_scalar

    assert "\n" not in _sanitize_frontmatter_scalar("a\nb\rc")
    assert "---" not in _sanitize_frontmatter_scalar("before --- after")
    quoted = _sanitize_frontmatter_scalar("Title: with colon")
    assert quoted.startswith("'") and quoted.endswith("'")


def test_write_note_sanitizes_hostile_title(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    result = ClassificationResult(
        category="note",
        title="Evil\n---\nscript: true",
        summary="Body.",
        tags=["ok", "bad,tag", "x]y"],
    )
    path = write_note(result)
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    fm_end = content.find("\n---\n", 4)
    assert fm_end != -1
    fm_block = content[4:fm_end]
    assert "\n---\n" not in fm_block
    # Titel ist gequoted — „script: true" ist Text, keine YAML-Key-Injection
    assert "title: 'Evil — script: true'" in fm_block
    assert not any(
        line.startswith("script:") for line in fm_block.splitlines()
    )
    assert "tags: [ok, badtag, xy]" in fm_block


def test_file_lock_serializes_create_path_allocation(tmp_path, monkeypatch):
    """E28-2: parallele write_note mit gleichem Titel → unterschiedliche Dateien."""
    import threading

    from app.vault.filesystem import FilesystemVaultBackend

    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    backend = FilesystemVaultBackend()
    results: list[str] = []
    errors: list[BaseException] = []

    def worker():
        try:
            rel = backend.write_note(
                ClassificationResult(
                    category="note",
                    title="Same Title",
                    summary="Body.",
                )
            )
            results.append(rel)
        except BaseException as exc:  # noqa: BLE001 — Test sammelt alle Fehler
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(results) == 8
    assert len(set(results)) == 8
    notes_dir = tmp_path / "Notes"
    assert len(list(notes_dir.glob("Same Title*.md"))) == 8


def test_file_lock_serializes_append(tmp_path, monkeypatch):
    """E28-2: parallele Appends verlieren keine Update-Blöcke."""
    import threading

    from app.vault.filesystem import FilesystemVaultBackend

    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    backend = FilesystemVaultBackend()
    rel = backend.write_note(
        ClassificationResult(category="note", title="Shared", summary="Start.")
    )
    errors: list[BaseException] = []

    def worker(i: int):
        try:
            backend.append_to_note(
                rel,
                ClassificationResult(
                    category="note",
                    title="Shared",
                    summary=f"Update {i}",
                    action="append",
                    target_title="Shared",
                ),
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    content = (tmp_path / rel).read_text(encoding="utf-8")
    for i in range(10):
        assert f"Update {i}" in content
    assert content.count("## Update") == 10
