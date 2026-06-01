from app.config import settings
from app.vault.reader import (
    VaultNote,
    _parse_frontmatter,
    format_notes_for_prompt,
    known_titles,
    list_existing_notes,
)


def test_parse_frontmatter():
    content = """---
title: My Note
category: idea
---

# Body
"""
    meta = _parse_frontmatter(content)
    assert meta["title"] == "My Note"
    assert meta["category"] == "idea"


def test_parse_frontmatter_missing():
    assert _parse_frontmatter("no frontmatter") == {}


def test_list_existing_notes(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    ideas_dir = tmp_path / "Ideas"
    ideas_dir.mkdir()
    (ideas_dir / "Startup Idea.md").write_text(
        """---
title: Startup Idea
category: idea
---

# Startup Idea

A note about startups.
""",
        encoding="utf-8",
    )

    notes = list_existing_notes()
    assert len(notes) == 1
    assert notes[0].title == "Startup Idea"
    assert notes[0].category == "idea"
    assert notes[0].folder == "Ideas"
    assert "startups" in notes[0].snippet.lower()


def test_format_notes_for_prompt_empty():
    assert format_notes_for_prompt([]) == "(no existing notes yet)"


def test_format_notes_for_prompt():
    notes = [
        VaultNote(title="A", category="idea", folder="Ideas", snippet="snippet a"),
    ]
    formatted = format_notes_for_prompt(notes)
    assert "[idea] A: snippet a" in formatted


def test_known_titles():
    notes = [VaultNote(title="My Note", category="", folder="", snippet="")]
    titles = known_titles(notes)
    assert titles["my note"] == "My Note"
