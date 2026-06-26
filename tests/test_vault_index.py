from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.models.vault_note_index import VaultNoteIndex
from app.vault.index import (
    SearchHit,
    parse_note_file,
    retrieve_vault_notes,
    search_vault_notes,
    semantic_search_vault_notes,
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
async def test_sync_indexes_multiple_formats_skips_unsupported(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    (tmp_path / "Notes").mkdir()
    (tmp_path / "Notes" / "Hello.md").write_text(
        "---\ntitle: Hello\n---\n\nBody.", encoding="utf-8"
    )
    (tmp_path / "Notes" / "Rechnung.txt").write_text("Betrag 42", encoding="utf-8")
    (tmp_path / "Notes" / "Foto.jpg").write_bytes(b"\xff\xd8\xff binary")
    obsidian = tmp_path / ".obsidian"
    obsidian.mkdir()
    (obsidian / "workspace.md").write_text("config", encoding="utf-8")

    added_rows = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=added_rows.append)
    db.commit = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    count = await sync_vault_index_from_disk(db)

    assert count == 2  # .md + .txt; .jpg und .obsidian/* ignoriert
    doc_types = {row.doc_type for row in added_rows}
    assert doc_types == {"markdown", "text"}


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


# ─── E17-2: Semantische Suche + Embedding-Pipeline ────────────────────────


@pytest.mark.asyncio
async def test_semantic_search_disabled_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    db = AsyncMock()
    hits = await semantic_search_vault_notes(db, "fitness", limit=5)
    assert hits == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_semantic_search_empty_query_returns_empty(monkeypatch):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    db = AsyncMock()
    hits = await semantic_search_vault_notes(db, "   ", limit=5)
    assert hits == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.vault.index.ensure_vault_index", new_callable=AsyncMock)
@patch("app.vault.index.get_embedding_provider")
async def test_semantic_search_returns_hits(mock_provider, mock_ensure, monkeypatch):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=[0.1] * 1536)
    mock_provider.return_value = provider

    row = VaultNoteIndex(
        id=1,
        vault_path="Ideas/A.md",
        title="Fitness App",
        category="idea",
        folder="Ideas",
        body_snippet="track workouts and nutrition",
        mtime=MagicMock(),
    )
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))
        )
    )

    hits = await semantic_search_vault_notes(db, "exercise tracking", limit=5)

    assert len(hits) == 1
    assert hits[0].title == "Fitness App"
    assert isinstance(hits[0], SearchHit)
    provider.embed.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.vault.index.get_embedding_provider")
async def test_upsert_sets_embedding_when_enabled(
    mock_provider, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=[0.5] * 1536)
    mock_provider.return_value = provider

    notes = tmp_path / "Notes"
    notes.mkdir()
    (notes / "Hello.md").write_text(
        "---\ntitle: Hello\n---\n\nBody.", encoding="utf-8"
    )

    added: list = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=added.append)
    db.commit = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    await upsert_vault_note_index(db, "Notes/Hello.md")

    assert added and added[0].embedding == [0.5] * 1536
    provider.embed.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.vault.index.get_embedding_provider")
async def test_upsert_skips_embedding_when_disabled(
    mock_provider, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "embeddings_enabled", False)

    notes = tmp_path / "Notes"
    notes.mkdir()
    (notes / "Hello.md").write_text(
        "---\ntitle: Hello\n---\n\nBody.", encoding="utf-8"
    )

    added: list = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=added.append)
    db.commit = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    await upsert_vault_note_index(db, "Notes/Hello.md")

    assert added and added[0].embedding is None
    mock_provider.assert_not_called()


# ─── E17-5: retrieve_vault_notes (Keyword + semantisch) ───────────────────


@pytest.mark.asyncio
@patch("app.vault.index.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.vault.index.search_vault_notes", new_callable=AsyncMock)
async def test_retrieve_prefers_semantic_when_enabled(
    mock_keyword, mock_semantic, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    sem_hit = SearchHit(
        title="Semantic", vault_path="Notes/S.md", snippet="s",
        category="note", folder="Notes",
    )
    mock_semantic.return_value = [sem_hit]
    db = AsyncMock()

    hits = await retrieve_vault_notes(db, "frage", 5, semantic=True)

    assert hits == [sem_hit]
    mock_semantic.assert_awaited_once()
    mock_keyword.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.vault.index.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.vault.index.search_vault_notes", new_callable=AsyncMock)
async def test_retrieve_falls_back_to_keyword(mock_keyword, mock_semantic, monkeypatch):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    mock_semantic.return_value = []
    kw_hit = SearchHit(
        title="Keyword", vault_path="Notes/K.md", snippet="k",
        category="note", folder="Notes",
    )
    mock_keyword.return_value = [kw_hit]
    db = AsyncMock()

    hits = await retrieve_vault_notes(db, "frage", 5, semantic=True)

    assert hits == [kw_hit]
    mock_semantic.assert_awaited_once()
    mock_keyword.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.vault.index.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.vault.index.search_vault_notes", new_callable=AsyncMock)
async def test_retrieve_keyword_only_when_semantic_false(
    mock_keyword, mock_semantic, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    mock_keyword.return_value = []
    db = AsyncMock()

    await retrieve_vault_notes(db, "frage", 5, semantic=False)

    mock_semantic.assert_not_awaited()
    mock_keyword.assert_awaited_once()
