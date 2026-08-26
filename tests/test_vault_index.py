from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.models.vault_chunk import VaultChunk
from app.models.vault_note_index import VaultNoteIndex
from app.vault.chunking import chunk_text
from app.vault.index import (
    SearchHit,
    parse_note_file,
    retrieve_vault_notes,
    search_vault_notes,
    semantic_search_vault_notes,
    sync_vault_index_from_disk,
    sync_vault_index_incremental,
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


def test_chunk_text_short_stays_one():
    assert chunk_text("hello world", chunk_size=100, overlap=10) == ["hello world"]


def test_chunk_text_splits_with_overlap():
    text = ("alpha " * 40) + ("beta " * 40)  # ~400 chars of words
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) >= 2
    assert all(chunks)


def test_chunk_text_empty():
    assert chunk_text("   ") == []


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
    db.flush = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    count = await sync_vault_index_from_disk(db)
    assert count == 1
    assert db.add.called
    db.commit.assert_awaited()


@pytest.mark.asyncio
async def test_incremental_sync_skips_unchanged_mtime(tmp_path, monkeypatch):
    """E28-1: unveränderte mtime → kein Re-Index / kein _replace_chunks."""
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    notes = tmp_path / "Notes"
    notes.mkdir()
    note = notes / "Hello.md"
    note.write_text("---\ntitle: Hello\n---\n\nBody.", encoding="utf-8")
    mtime = datetime.fromtimestamp(note.stat().st_mtime, tz=UTC)

    existing = VaultNoteIndex(
        vault_path="Notes/Hello.md",
        title="Hello",
        category="",
        folder="Notes",
        doc_type="markdown",
        body_snippet="Body.",
        mtime=mtime,
    )

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()

    # 1) select existing for mtime check → existing
    # 2) delete orphans → rowcount 0
    select_result = MagicMock()
    select_result.scalar_one_or_none.return_value = existing
    delete_result = MagicMock(rowcount=0)

    db.execute = AsyncMock(side_effect=[select_result, delete_result])

    with patch("app.vault.index._replace_chunks", new_callable=AsyncMock) as mock_chunks:
        result = await sync_vault_index_incremental(db)

    assert result.mode == "incremental"
    assert result.indexed == 0
    assert result.skipped == 1
    mock_chunks.assert_not_awaited()
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_incremental_sync_indexes_when_mtime_newer(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    notes = tmp_path / "Notes"
    notes.mkdir()
    note = notes / "Hello.md"
    note.write_text("---\ntitle: Hello\n---\n\nBody v1.", encoding="utf-8")

    old_mtime = datetime.fromtimestamp(note.stat().st_mtime - 10, tz=UTC)
    existing = VaultNoteIndex(
        vault_path="Notes/Hello.md",
        title="Hello",
        category="",
        folder="Notes",
        doc_type="markdown",
        body_snippet="old",
        mtime=old_mtime,
    )

    note.write_text("---\ntitle: Hello\n---\n\nBody v2 changed.", encoding="utf-8")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()

    # mtime check → existing; apply_index select → existing; delete → 0
    mtime_check = MagicMock(scalar_one_or_none=MagicMock(return_value=existing))
    apply_select = MagicMock(scalar_one_or_none=MagicMock(return_value=existing))
    delete_result = MagicMock(rowcount=0)
    db.execute = AsyncMock(side_effect=[mtime_check, apply_select, delete_result])

    with patch(
        "app.vault.index._replace_chunks", new_callable=AsyncMock, return_value=(1, False)
    ):
        result = await sync_vault_index_incremental(db)

    assert result.indexed == 1
    assert result.skipped == 0
    assert existing.body_snippet  # updated via apply
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
    db.flush = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    count = await sync_vault_index_from_disk(db)

    assert count == 2  # .md + .txt; .jpg und .obsidian/* ignoriert
    doc_types = {row.doc_type for row in added_rows if isinstance(row, VaultNoteIndex)}
    assert doc_types == {"markdown", "text"}
    assert any(isinstance(row, VaultChunk) for row in added_rows)


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


# ─── E17-2 / E18-4: Semantische Suche + Chunk-Embeddings ───────────────────


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

    note = VaultNoteIndex(
        id=1,
        vault_path="Ideas/A.md",
        title="Fitness App",
        category="idea",
        folder="Ideas",
        body_snippet="track workouts and nutrition",
        mtime=MagicMock(),
    )
    chunk = VaultChunk(
        id=10,
        note_id=1,
        chunk_index=0,
        content="track workouts and nutrition deeply",
        embedding=[0.1] * 1536,
    )
    chunk.note = note
    db = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[chunk])))
        )
    )

    hits = await semantic_search_vault_notes(db, "exercise tracking", limit=5)

    assert len(hits) == 1
    assert hits[0].title == "Fitness App"
    assert "workouts" in hits[0].snippet
    assert isinstance(hits[0], SearchHit)
    provider.embed.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.webhooks.outbound.emit_note_indexed_event", new_callable=AsyncMock)
@patch("app.vault.index.get_embedding_provider")
async def test_upsert_sets_chunk_embedding_when_enabled(
    mock_provider, mock_emit, tmp_path, monkeypatch
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
    db.flush = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    await upsert_vault_note_index(db, "Notes/Hello.md")

    notes_added = [r for r in added if isinstance(r, VaultNoteIndex)]
    chunks_added = [r for r in added if isinstance(r, VaultChunk)]
    assert notes_added
    assert chunks_added
    assert chunks_added[0].embedding == [0.5] * 1536
    provider.embed.assert_awaited_once()
    mock_emit.assert_awaited_once_with(
        vault_path="Notes/Hello.md",
        title="Hello",
        category="",
        folder="Notes",
        doc_type="markdown",
    )


@pytest.mark.asyncio
@patch("app.webhooks.outbound.emit_note_indexed_event", new_callable=AsyncMock)
@patch("app.vault.index.get_embedding_provider")
async def test_upsert_skips_embedding_when_disabled(
    mock_provider, mock_emit, tmp_path, monkeypatch
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
    db.flush = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    await upsert_vault_note_index(db, "Notes/Hello.md")

    chunks_added = [r for r in added if isinstance(r, VaultChunk)]
    assert chunks_added
    assert chunks_added[0].embedding is None
    mock_provider.assert_not_called()
    mock_emit.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.webhooks.outbound.emit_note_indexed_event", new_callable=AsyncMock)
@patch("app.vault.index.get_embedding_provider")
async def test_upsert_creates_multiple_chunks_for_long_doc(
    mock_provider, mock_emit, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    monkeypatch.setattr(settings, "seiton_chunk_size", 80)
    monkeypatch.setattr(settings, "seiton_chunk_overlap", 10)

    notes = tmp_path / "Notes"
    notes.mkdir()
    body = "word " * 100
    (notes / "Long.md").write_text(
        f"---\ntitle: Long\n---\n\n{body}", encoding="utf-8"
    )

    added: list = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=added.append)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    await upsert_vault_note_index(db, "Notes/Long.md")

    chunks_added = [r for r in added if isinstance(r, VaultChunk)]
    assert len(chunks_added) >= 2
    assert [c.chunk_index for c in chunks_added] == list(range(len(chunks_added)))


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
