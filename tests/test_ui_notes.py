"""Tests fuer Notizen-Verwaltung UI (E19-4)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.vault_note_index import VaultNoteIndex
from app.ui.notes import list_notes, load_vault_config, remove_note, update_note_content

client = TestClient(app)


def test_notes_page_renders():
    response = client.get("/notes")
    assert response.status_code == 200
    assert "Notizen verwalten" in response.text
    assert "notes.js" in response.text
    assert 'href="/notes"' in response.text


def test_vault_config_api():
    response = client.get("/api/ui/vault-config")
    assert response.status_code == 200
    data = response.json()
    assert "vault_path" in data
    assert "school" in data["categories"]
    assert data["categories"]["idea"] == "Ideas"


@patch("app.ui.router.list_notes", new_callable=AsyncMock)
def test_notes_list_api(mock_list):
    from app.ui.schemas import NoteListItem, NoteListResponse

    mock_list.return_value = NoteListResponse(
        items=[
            NoteListItem(
                title="Test",
                vault_path="Ideas/Test.md",
                folder="Ideas",
                category="idea",
                mtime=datetime(2026, 6, 1, tzinfo=UTC),
            )
        ],
        limit=50,
        offset=0,
    )
    response = client.get("/api/ui/notes?folder=Ideas")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


@patch("app.ui.router.remove_note", new_callable=AsyncMock)
@patch("app.ui.router.update_note_content", new_callable=AsyncMock)
def test_notes_content_save_delete_routes(mock_update, mock_remove, tmp_path, monkeypatch):
    from app.ui.schemas import NoteDeleteResponse, NoteSaveResponse

    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "Notes" / "Hello.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Hello\n\nBody", encoding="utf-8")
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(vault))

    mock_update.return_value = NoteSaveResponse(vault_path="Notes/Hello.md", title="Hello")
    mock_remove.return_value = NoteDeleteResponse(vault_path="Notes/Hello.md", deleted=True)

    get_res = client.get("/api/ui/notes/content?vault_path=Notes/Hello.md")
    assert get_res.status_code == 200
    assert "Hello" in get_res.json()["content"]

    put_res = client.put(
        "/api/ui/notes/content",
        json={"vault_path": "Notes/Hello.md", "content": "# Hello\n\nUpdated"},
    )
    assert put_res.status_code == 200

    del_res = client.delete("/api/ui/notes?vault_path=Notes/Hello.md")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True


def test_notes_content_rejects_traversal(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(vault))

    response = client.get("/api/ui/notes/content?vault_path=../../../etc/passwd")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_notes_filters_folder():
    db = AsyncMock()
    row = VaultNoteIndex(
        vault_path="Ideas/A.md",
        title="A",
        category="idea",
        folder="Ideas",
        doc_type="markdown",
        body_snippet="snippet",
        mtime=datetime(2026, 6, 1, tzinfo=UTC),
    )
    db.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row]))))
    )

    result = await list_notes(db, folder="Ideas")

    assert len(result.items) == 1
    assert result.items[0].title == "A"


def test_load_vault_config_categories():
    config = load_vault_config()
    assert config.categories["travel"] == "Travel"


@pytest.mark.asyncio
@patch("app.ui.notes.upsert_vault_note_index", new_callable=AsyncMock)
async def test_update_note_content(mock_upsert, tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "Notes" / "X.md"
    note.parent.mkdir(parents=True)
    note.write_text("old", encoding="utf-8")
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(vault))

    db = AsyncMock()
    result = await update_note_content(db, "Notes/X.md", "new content")

    assert note.read_text(encoding="utf-8") == "new content"
    mock_upsert.assert_awaited_once_with(db, "Notes/X.md")
    assert result.vault_path == "Notes/X.md"


@pytest.mark.asyncio
@patch("app.ui.notes.remove_vault_note_index", new_callable=AsyncMock)
async def test_remove_note(mock_remove, tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    note = vault / "Notes" / "Y.md"
    note.parent.mkdir(parents=True)
    note.write_text("bye", encoding="utf-8")
    monkeypatch.setattr("app.config.settings.obsidian_vault_path", str(vault))

    db = AsyncMock()
    result = await remove_note(db, "Notes/Y.md")

    assert result.deleted is True
    assert not note.exists()
    mock_remove.assert_awaited_once_with(db, "Notes/Y.md")
