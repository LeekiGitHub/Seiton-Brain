from unittest.mock import AsyncMock, patch

import pytest

from app.telegram.admin_notify import format_admin_error_message, notify_admin_error


def test_format_admin_error_message_includes_context():
    message = format_admin_error_message(
        task_name="process_text_message",
        error=ValueError("boom"),
        chat_id=42,
        task_id="celery-task-1",
        telegram_update_id=999,
    )
    assert "process_text_message" in message
    assert "celery-task-1" in message
    assert "Chat: 42" in message
    assert "Update: 999" in message
    assert "ValueError: boom" in message


def test_format_admin_error_message_truncates_long_traceback():
    try:
        raise RuntimeError("x" * 2000)
    except RuntimeError as exc:
        message = format_admin_error_message(
            task_name="process_voice_message",
            error=exc,
        )
    assert len(message) <= 3900
    assert "..." in message


@pytest.mark.asyncio
@patch("app.telegram.admin_notify.send_message", new_callable=AsyncMock)
async def test_notify_admin_error_skipped_when_not_configured(mock_send, monkeypatch):
    monkeypatch.setattr("app.telegram.admin_notify.settings.telegram_admin_chat_id", "")
    await notify_admin_error(
        task_name="process_text_message",
        error=ValueError("boom"),
        chat_id=42,
    )
    mock_send.assert_not_called()


@pytest.mark.asyncio
@patch("app.telegram.admin_notify.send_message", new_callable=AsyncMock)
async def test_notify_admin_error_sends_dm(mock_send, monkeypatch):
    monkeypatch.setattr("app.telegram.admin_notify.settings.telegram_admin_chat_id", "12345")
    await notify_admin_error(
        task_name="process_text_message",
        error=ValueError("boom"),
        chat_id=42,
        task_id="task-1",
    )
    mock_send.assert_awaited_once()
    assert mock_send.await_args.args[0] == 12345
    assert "ValueError: boom" in mock_send.await_args.args[1]


@pytest.mark.asyncio
@patch("app.telegram.admin_notify.send_message", new_callable=AsyncMock)
async def test_notify_admin_error_swallows_send_failure(mock_send, monkeypatch):
    monkeypatch.setattr("app.telegram.admin_notify.settings.telegram_admin_chat_id", "12345")
    mock_send.side_effect = RuntimeError("telegram down")
    await notify_admin_error(
        task_name="process_text_message",
        error=ValueError("boom"),
    )
