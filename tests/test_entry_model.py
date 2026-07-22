from app.models.entry import KIND_VALUES, STATUS_VALUES, Entry


def test_entry_required_fields_only():
    entry = Entry(title="T", category="note", summary="S")

    assert entry.title == "T"
    assert entry.category == "note"
    assert entry.summary == "S"
    assert entry.raw_input is None
    assert entry.vault_path is None
    assert entry.telegram_chat_id is None
    assert entry.telegram_message_id is None
    assert entry.telegram_update_id is None


def test_entry_can_be_constructed_with_extended_fields():
    entry = Entry(
        title="Test",
        category="idea",
        summary="Summary",
        raw_input="Original telegram text",
        vault_path="Ideas/Test.md",
        telegram_chat_id=12345,
        telegram_message_id=67,
        telegram_update_id=890,
        kind="text",
        status="processed",
        prompt_version="v1",
    )

    assert entry.raw_input == "Original telegram text"
    assert entry.vault_path == "Ideas/Test.md"
    assert entry.telegram_chat_id == 12345
    assert entry.telegram_message_id == 67
    assert entry.telegram_update_id == 890
    assert entry.kind == "text"
    assert entry.status == "processed"
    assert entry.prompt_version == "v1"


def test_value_sets_are_documented():
    assert "text" in KIND_VALUES
    assert "voice" in KIND_VALUES
    assert "processed" in STATUS_VALUES
    assert "appended" in STATUS_VALUES
    assert "failed" in STATUS_VALUES
    assert "rejected" in STATUS_VALUES
