from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.llm.schemas import ClassificationResult
from app.services.process_message import process_text_message


def _classification(title: str = "Test", category: str = "note") -> ClassificationResult:
    return ClassificationResult(
        category=category,
        title=title,
        summary="Summary",
        related=[],
    )


async def _assign_entry_id(entry) -> None:
    entry.id = 42


def _db_with_pre_check_result(found: bool) -> MagicMock:
    """Mock-DB, deren erstes execute() einen 'gefunden / nicht gefunden'-Result liefert."""
    db = MagicMock()
    pre_check = MagicMock()
    pre_check.scalar_one_or_none.return_value = 1 if found else None
    db.execute = AsyncMock(return_value=pre_check)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock(side_effect=_assign_entry_id)
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


def _mock_vault(*, write_rel: str | None = None, append_rel: str | None = None):
    vault = MagicMock()
    vault.note_exists.return_value = True
    if write_rel is not None:
        vault.write_note.return_value = write_rel
    if append_rel is not None:
        vault.append_to_note.return_value = append_rel
    return vault


@pytest.mark.asyncio
@patch("app.services.process_message.upsert_vault_note_index", new_callable=AsyncMock)
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_persists_with_telegram_fields(
    mock_provider, mock_get_vault, mock_upsert_index
):
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification(title="Idea X", category="idea"))
    mock_provider.return_value = llm
    mock_get_vault.return_value = _mock_vault(write_rel="Ideas/Idea X.md")
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
    assert result.classification.title == "Idea X"
    assert result.entry_id == 42
    db.add.assert_called_once()
    entry = db.add.call_args[0][0]
    assert entry.raw_input == "Original text"
    assert entry.vault_path == "Ideas/Idea X.md"
    assert entry.telegram_update_id == 1234
    assert entry.telegram_message_id == 42
    assert entry.telegram_chat_id == 99
    assert entry.kind == "text"
    db.commit.assert_awaited_once()
    mock_get_vault.return_value.write_note.assert_called_once()
    mock_upsert_index.assert_awaited_once_with(db, "Ideas/Idea X.md")


@pytest.mark.asyncio
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_skips_duplicate_update(mock_provider, mock_get_vault):
    db = _db_with_pre_check_result(found=True)

    result = await process_text_message(
        "Original text",
        db,
        telegram_update_id=1234,
    )

    assert result is None
    mock_provider.assert_not_called()
    mock_get_vault.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_handles_integrity_error_race(
    mock_provider, mock_get_vault
):
    """E28-3: UNIQUE-Claim per flush vor Vault-Write — bei Race kein Orphan."""
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm
    vault = _mock_vault(write_rel="Notes/Test.md")
    mock_get_vault.return_value = vault
    db = _db_with_pre_check_result(found=False)
    db.flush = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("dup")))

    result = await process_text_message(
        "Original text",
        db,
        telegram_update_id=5555,
    )

    assert result is None
    db.rollback.assert_awaited_once()
    vault.write_note.assert_not_called()
    vault.delete_note.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_compensates_orphan_on_commit_failure(
    mock_provider, mock_get_vault
):
    """E28-3: Create-Datei wird gelöscht, wenn Commit nach Write scheitert."""
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm
    vault = _mock_vault(write_rel="Notes/Test.md")
    vault.delete_note.return_value = True
    mock_get_vault.return_value = vault
    db = _db_with_pre_check_result(found=False)
    db.commit = AsyncMock(side_effect=RuntimeError("db down"))

    with pytest.raises(RuntimeError, match="db down"):
        await process_text_message(
            "Original text",
            db,
            telegram_update_id=5555,
        )

    vault.write_note.assert_called_once()
    vault.delete_note.assert_called_once_with("Notes/Test.md")
    db.rollback.assert_awaited()


@pytest.mark.asyncio
@patch("app.services.process_message._resolve_append_target", new_callable=AsyncMock)
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_does_not_delete_on_append_commit_failure(
    mock_provider, mock_get_vault, mock_resolve
):
    """Append darf bestehende Notizen bei Commit-Fehler nicht löschen."""
    classification = ClassificationResult(
        category="idea",
        title="Workout log feature",
        summary="Add daily log.",
        action="append",
        target_title="Fitness App",
    )
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=classification)
    mock_provider.return_value = llm
    mock_resolve.return_value = "Ideas/Fitness App.md"
    vault = _mock_vault(append_rel="Ideas/Fitness App.md")
    mock_get_vault.return_value = vault
    db = _db_with_pre_check_result(found=False)
    db.commit = AsyncMock(side_effect=RuntimeError("db down"))

    with pytest.raises(RuntimeError, match="db down"):
        await process_text_message(
            "Add daily log",
            db,
            telegram_update_id=7002,
        )

    vault.append_to_note.assert_called_once()
    vault.delete_note.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.process_message.upsert_vault_note_index", new_callable=AsyncMock)
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_without_update_id_skips_pre_check(
    mock_provider, mock_get_vault, mock_upsert_index
):
    """Backwards compat: ohne update_id keine Duplikat-Pruefung."""
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm
    mock_get_vault.return_value = _mock_vault(write_rel="Notes/Test.md")

    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock(side_effect=_assign_entry_id)
    db.add = MagicMock()

    result = await process_text_message("Hi", db)

    assert result is not None
    db.execute.assert_not_called()
    db.add.assert_called_once()
    entry = db.add.call_args[0][0]
    assert entry.vault_path == "Notes/Test.md"
    db.commit.assert_awaited_once()
    mock_get_vault.return_value.write_note.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.process_message.upsert_vault_note_index", new_callable=AsyncMock)
@patch("app.services.process_message._resolve_append_target", new_callable=AsyncMock)
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_appends_when_target_resolves(
    mock_provider, mock_get_vault, mock_resolve, mock_upsert_index
):
    classification = ClassificationResult(
        category="idea",
        title="Workout log feature",
        summary="Add daily log.",
        action="append",
        target_title="Fitness App",
    )
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=classification)
    mock_provider.return_value = llm
    mock_resolve.return_value = "Ideas/Fitness App.md"
    vault = _mock_vault(append_rel="Ideas/Fitness App.md")
    mock_get_vault.return_value = vault
    db = _db_with_pre_check_result(found=False)

    result = await process_text_message(
        "Add daily log to fitness app",
        db,
        telegram_update_id=7001,
    )

    assert result is not None
    assert result.classification.action == "append"
    assert result.classification.target_title == "Fitness App"
    vault.append_to_note.assert_called_once_with("Ideas/Fitness App.md", classification)
    vault.write_note.assert_not_called()
    entry = db.add.call_args[0][0]
    assert entry.status == "appended"
    assert entry.vault_path == "Ideas/Fitness App.md"
    assert entry.title == "Workout log feature"


@pytest.mark.asyncio
@patch("app.services.process_message.upsert_vault_note_index", new_callable=AsyncMock)
@patch("app.services.process_message._resolve_append_target", new_callable=AsyncMock)
@patch("app.services.process_message.get_vault_backend")
@patch("app.services.process_message.get_llm_provider")
async def test_process_text_message_falls_back_to_create_when_target_missing(
    mock_provider, mock_get_vault, mock_resolve, mock_upsert_index
):
    classification = ClassificationResult(
        category="idea",
        title="Solo idea",
        summary="Stand alone.",
        action="append",
        target_title="Vanished Note",
    )
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=classification)
    mock_provider.return_value = llm
    mock_resolve.return_value = None
    vault = _mock_vault(write_rel="Ideas/Solo idea.md")
    mock_get_vault.return_value = vault
    db = _db_with_pre_check_result(found=False)

    result = await process_text_message(
        "Some content",
        db,
        telegram_update_id=7002,
    )

    assert result is not None
    assert result.classification.action == "create"
    assert result.classification.target_title is None
    vault.append_to_note.assert_not_called()
    vault.write_note.assert_called_once()
    entry = db.add.call_args[0][0]
    assert entry.status == "processed"
    assert entry.vault_path == "Ideas/Solo idea.md"
