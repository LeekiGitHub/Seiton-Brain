from app.vault.reader import (
    VaultNote,
    _parse_frontmatter,
    format_notes_for_prompt,
    known_titles,
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
