from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.services.process_message import process_text_message

VAULT_ROOT = Path(settings.obsidian_vault_path)


def _classification(title: str = "Test", category: str = "note") -> ClassificationResult:
    return ClassificationResult(
        category=category,
        title=title,
        summary="Summary",
        related=[],
    )


def _db_with_pre_check_result(found: bool) -> MagicMock:
    """Mock-DB, deren erstes execute() einen 'gefunden / nicht gefunden'-Result liefert."""
    db = MagicMock()
    pre_check = MagicMock()
    pre_check.scalar_one_or_none.return_value = 1 if found else None
    db.execute = AsyncMock(return_value=pre_check)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
@patch("app.services.process_message.write_note")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_persists_with_telegram_fields(
    mock_provider, mock_write_note
):
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification(title="Idea X", category="idea"))
    mock_provider.return_value = llm
    mock_write_note.return_value = VAULT_ROOT / "Ideas" / "Idea X.md"
    db = _db_with_pre_check_result(found=False)

    result = await process_text_message(
        "Original text",
        db,
        telegram_update_id=1234,
        telegram_message_id=42,
        telegram_chat_id=99,
        kind="text",
    )

    assert result is not None
    assert result.title == "Idea X"
    db.add.assert_called_once()
    entry = db.add.call_args[0][0]
    assert entry.raw_input == "Original text"
    assert entry.vault_path == "Ideas/Idea X.md"
    assert entry.telegram_update_id == 1234
    assert entry.telegram_message_id == 42
    assert entry.telegram_chat_id == 99
    assert entry.kind == "text"
    db.commit.assert_awaited_once()
    mock_write_note.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.process_message.write_note")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_skips_duplicate_update(
    mock_provider, mock_write_note
):
    db = _db_with_pre_check_result(found=True)

    result = await process_text_message(
        "Original text",
        db,
        telegram_update_id=1234,
    )

    assert result is None
    mock_provider.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()
    mock_write_note.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.process_message.write_note")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_handles_integrity_error_race(
    mock_provider, mock_write_note
):
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm
    mock_write_note.return_value = VAULT_ROOT / "Notes" / "Test.md"
    db = _db_with_pre_check_result(found=False)
    db.commit = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("dup")))

    result = await process_text_message(
        "Original text",
        db,
        telegram_update_id=5555,
    )

    assert result is None
    db.rollback.assert_awaited_once()
    # Vault-Datei wurde geschrieben (Race-Edge-Case dokumentiert im Code).
    mock_write_note.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.process_message.write_note")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_without_update_id_skips_pre_check(
    mock_provider, mock_write_note
):
    """Backwards compat: ohne update_id keine Duplikat-Pruefung."""
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm
    mock_write_note.return_value = VAULT_ROOT / "Notes" / "Test.md"

    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    result = await process_text_message("Hi", db)

    assert result is not None
    db.execute.assert_not_called()
    db.add.assert_called_once()
    entry = db.add.call_args[0][0]
    assert entry.vault_path == "Notes/Test.md"
    db.commit.assert_awaited_once()
    mock_write_note.assert_called_once()
