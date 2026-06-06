"""Tests fuer die Slash-Command-Handler.

Wir patchen die ``_query_*``- und ``_delete_entry``-Helper, damit die
Tests komplett ohne DB laufen. ``db``-Argument wird einfach als ``None``
durchgereicht (Handler nutzen es nur via die gemockten Helper).
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.models.entry import Entry
from app.telegram.commands import (
    DEFAULT_RECENT_LIMIT,
    HELP_TEXT,
    MAX_RECENT_LIMIT,
    handle_command,
)


def _make_entry(
    id_: int = 1,
    title: str = "Test",
    status: str = "processed",
    vault_path: str | None = "Notes/Test.md",
    chat_id: int = 42,
) -> Entry:
    return Entry(
        id=id_,
        title=title,
        category="note",
        summary="x",
        status=status,
        kind="text",
        vault_path=vault_path,
        telegram_chat_id=chat_id,
    )


# ── Dispatch ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_command_returns_none_for_non_command():
    assert await handle_command("Hello world", 42, None) is None  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_handle_command_strips_bot_suffix():
    reply = await handle_command("/help@SeitonBrainBot", 42, None)  # type: ignore[arg-type]
    assert reply == HELP_TEXT


@pytest.mark.asyncio
async def test_handle_command_unknown_command_replies_with_help():
    reply = await handle_command("/foobar", 42, None)  # type: ignore[arg-type]
    assert reply is not None
    assert "Unbekannter Command" in reply
    assert "/help" in reply


# ── /help and /start ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_help_command_returns_help_text():
    assert await handle_command("/help", 42, None) == HELP_TEXT  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_start_command_returns_help_text():
    assert await handle_command("/start", 42, None) == HELP_TEXT  # type: ignore[arg-type]


# ── /recent ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.telegram.commands._query_recent", new_callable=AsyncMock)
async def test_recent_default_limit(mock_query):
    mock_query.return_value = [_make_entry(1, "Note A"), _make_entry(2, "Note B")]
    reply = await handle_command("/recent", 42, None)  # type: ignore[arg-type]
    mock_query.assert_awaited_once_with(None, 42, DEFAULT_RECENT_LIMIT)
    assert "Note A" in reply
    assert "Note B" in reply
    assert "[[Note A]]" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._query_recent", new_callable=AsyncMock)
async def test_recent_custom_limit_respects_max(mock_query):
    mock_query.return_value = []
    await handle_command("/recent 100", 42, None)  # type: ignore[arg-type]
    mock_query.assert_awaited_once_with(None, 42, MAX_RECENT_LIMIT)


@pytest.mark.asyncio
@patch("app.telegram.commands._query_recent", new_callable=AsyncMock)
async def test_recent_invalid_arg_falls_back_to_default(mock_query):
    mock_query.return_value = []
    await handle_command("/recent abc", 42, None)  # type: ignore[arg-type]
    mock_query.assert_awaited_once_with(None, 42, DEFAULT_RECENT_LIMIT)


@pytest.mark.asyncio
@patch("app.telegram.commands._query_recent", new_callable=AsyncMock)
async def test_recent_empty_replies_with_hint(mock_query):
    mock_query.return_value = []
    reply = await handle_command("/recent", 42, None)  # type: ignore[arg-type]
    assert "Noch keine Notizen" in reply


# ── /find ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_without_query_shows_usage():
    reply = await handle_command("/find", 42, None)  # type: ignore[arg-type]
    assert "Nutzung" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._query_find", new_callable=AsyncMock)
async def test_find_with_query_passes_through(mock_query):
    mock_query.return_value = [_make_entry(1, "Fitness App")]
    reply = await handle_command("/find fitness", 42, None)  # type: ignore[arg-type]
    mock_query.assert_awaited_once()
    args, _ = mock_query.call_args
    assert args[1] == 42
    assert args[2] == "fitness"
    assert "Fitness App" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._query_find", new_callable=AsyncMock)
async def test_find_no_results(mock_query):
    mock_query.return_value = []
    reply = await handle_command("/find nothing", 42, None)  # type: ignore[arg-type]
    assert "Keine Notiz gefunden" in reply
    assert "nothing" in reply
    assert "„" in reply  # german quotes intact


# ── /undo ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_without_confirm_shows_preview(mock_latest):
    mock_latest.return_value = _make_entry(7, "Fitness App")
    reply = await handle_command("/undo", 42, None)  # type: ignore[arg-type]
    assert "Fitness App" in reply
    assert "/undo confirm" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_without_confirm_appended_warns_about_manual_cleanup(
    mock_latest,
):
    mock_latest.return_value = _make_entry(7, "Project X", status="appended")
    reply = await handle_command("/undo", 42, None)  # type: ignore[arg-type]
    assert "Update-Block" in reply
    assert "manuell" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_when_nothing_to_delete(mock_latest):
    mock_latest.return_value = None
    reply = await handle_command("/undo", 42, None)  # type: ignore[arg-type]
    assert "Nichts" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._delete_entry", new_callable=AsyncMock)
@patch("app.telegram.commands.delete_note")
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_confirm_deletes_db_and_vault(
    mock_latest, mock_delete_note, mock_delete_entry
):
    entry = _make_entry(7, "Doomed", status="processed", vault_path="Notes/Doomed.md")
    mock_latest.return_value = entry
    mock_delete_note.return_value = True

    reply = await handle_command("/undo confirm", 42, None)  # type: ignore[arg-type]

    mock_delete_note.assert_called_once_with("Notes/Doomed.md")
    mock_delete_entry.assert_awaited_once()
    assert "Gelöscht" in reply
    assert "Doomed" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._delete_entry", new_callable=AsyncMock)
@patch("app.telegram.commands.delete_note")
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_confirm_appended_keeps_vault_file(
    mock_latest, mock_delete_note, mock_delete_entry
):
    entry = _make_entry(7, "Project X", status="appended", vault_path="Notes/Project X.md")
    mock_latest.return_value = entry

    reply = await handle_command("/undo confirm", 42, None)  # type: ignore[arg-type]

    # Appended-Entries duerfen die Vault-Datei NICHT loeschen — sonst geht
    # die Original-Notiz mit potenziell vielen Update-Bloecken verloren.
    mock_delete_note.assert_not_called()
    mock_delete_entry.assert_awaited_once()
    assert "manuell" in reply


@pytest.mark.asyncio
@patch("app.telegram.commands._delete_entry", new_callable=AsyncMock)
@patch("app.telegram.commands.delete_note")
@patch("app.telegram.commands._query_latest", new_callable=AsyncMock)
async def test_undo_confirm_handles_missing_vault_file(
    mock_latest, mock_delete_note, mock_delete_entry
):
    entry = _make_entry(7, "Ghost", status="processed", vault_path="Notes/Ghost.md")
    mock_latest.return_value = entry
    mock_delete_note.return_value = False  # Datei war schon weg

    reply = await handle_command("/undo confirm", 42, None)  # type: ignore[arg-type]

    mock_delete_entry.assert_awaited_once()
    assert "nicht (mehr) vorhanden" in reply
