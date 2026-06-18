from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.models.vault_note_index import VaultNoteIndex
from app.vault.index import (
    SearchHit,
    parse_note_file,
    search_vault_notes,
    sync_vault_index_from_disk,
    upsert_vault_note_index,
)


def test_parse_note_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    ideas = tmp_path / "Ideas"
    ideas.mkdir()
    note = ideas / "Fitness App.md"
    note.write_text(
        """---
title: Fitness App
category: idea
---

# Fitness App

Track workouts and nutrition.
""",
        encoding="utf-8",
    )
    parsed = parse_note_file(note)
    assert parsed.title == "Fitness App"
    assert parsed.category == "idea"
    assert "workouts" in parsed.snippet.lower()


@pytest.mark.asyncio
async def test_sync_vault_index_from_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    (tmp_path / "Notes" / "Hello.md").write_text(
        "---\ntitle: Hello\ncategory: note\n---\n\nBody text.",
        encoding="utf-8",
    )

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    count = await sync_vault_index_from_disk(db)
    assert count == 1
    assert db.add.called
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_upsert_removes_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    db = AsyncMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock()

    await upsert_vault_note_index(db, "Notes/Missing.md")

    assert db.execute.await_count >= 1
    db.commit.assert_awaited()


@pytest.mark.asyncio
@patch("app.vault.index.ensure_vault_index", new_callable=AsyncMock)
async def test_search_vault_notes_title_before_body(mock_ensure):
    row_title = VaultNoteIndex(
        id=1,
        vault_path="Ideas/A.md",
        title="Fitness App",
        category="idea",
        folder="Ideas",
        body_snippet="other",
        mtime=MagicMock(),
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row_title]))))
    )

    hits = await search_vault_notes(db, "fitness", limit=5)

    assert len(hits) == 1
    assert hits[0].title == "Fitness App"
    assert isinstance(hits[0], SearchHit)


@pytest.mark.asyncio
@patch("app.vault.index.ensure_vault_index", new_callable=AsyncMock)
async def test_search_empty_query_returns_empty(mock_ensure):
    db = AsyncMock()
    hits = await search_vault_notes(db, "   ", limit=5)
    assert hits == []
    db.execute.assert_not_awaited()
