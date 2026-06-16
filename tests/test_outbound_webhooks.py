from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.llm.schemas import ClassificationResult
from app.services.process_message import ProcessMessageResult
from app.webhooks.outbound import (
    EVENT_ENTRY_FAILED,
    EVENT_NOTE_APPENDED,
    EVENT_NOTE_CREATED,
    build_entry_failed_payload,
    build_note_event_payload,
    emit_capture_event,
    emit_entry_failed_event,
    emit_webhook,
    event_for_capture_status,
)


def _result(*, status: str = "processed") -> ProcessMessageResult:
    return ProcessMessageResult(
        classification=ClassificationResult(
            category="idea",
            title="Test Note",
            summary="Summary.",
        ),
        entry_id=1,
        vault_path="Ideas/Test Note.md",
        status=status,
    )


def test_event_for_capture_status():
    assert event_for_capture_status("processed") == EVENT_NOTE_CREATED
    assert event_for_capture_status("appended") == EVENT_NOTE_APPENDED


def test_build_note_event_payload_created():
    payload = build_note_event_payload(
        _result(),
        kind="text",
        telegram_chat_id=42,
        telegram_update_id=99,
    )
    assert payload["event"] == EVENT_NOTE_CREATED
    assert payload["entry_id"] == 1
    assert payload["kind"] == "text"
    assert payload["telegram_chat_id"] == 42
    assert payload["classification"]["title"] == "Test Note"


def test_build_note_event_payload_appended():
    payload = build_note_event_payload(_result(status="appended"))
    assert payload["event"] == EVENT_NOTE_APPENDED
    assert payload["status"] == "appended"


def test_build_entry_failed_payload_truncates_raw_input():
    payload = build_entry_failed_payload(
        task_name="process_text_message",
        error=ValueError("boom"),
        raw_input="x" * 300,
    )
    assert payload["event"] == EVENT_ENTRY_FAILED
    assert len(payload["raw_input_preview"]) <= 200


@pytest.mark.asyncio
@patch("app.webhooks.outbound.httpx.AsyncClient")
async def test_emit_webhook_skipped_when_url_empty(mock_client_cls, monkeypatch):
    monkeypatch.setattr("app.webhooks.outbound.settings.seiton_webhook_url", "")
    await emit_webhook({"event": EVENT_NOTE_CREATED})
    mock_client_cls.assert_not_called()


@pytest.mark.asyncio
@patch("app.webhooks.outbound.httpx.AsyncClient")
async def test_emit_webhook_posts_json(mock_client_cls, monkeypatch):
    monkeypatch.setattr(
        "app.webhooks.outbound.settings.seiton_webhook_url",
        "https://n8n.example/hook",
    )
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_cls.return_value = mock_client

    await emit_webhook({"event": EVENT_NOTE_CREATED, "entry_id": 1})

    mock_client.post.assert_awaited_once()
    call_kwargs = mock_client.post.await_args.kwargs
    assert call_kwargs["json"]["entry_id"] == 1
    assert call_kwargs["headers"]["X-Seiton-Event"] == EVENT_NOTE_CREATED


@pytest.mark.asyncio
@patch("app.webhooks.outbound.httpx.AsyncClient")
async def test_emit_webhook_logs_http_errors(mock_client_cls, monkeypatch):
    monkeypatch.setattr(
        "app.webhooks.outbound.settings.seiton_webhook_url",
        "https://n8n.example/hook",
    )
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPError("down"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_cls.return_value = mock_client

    await emit_webhook({"event": EVENT_ENTRY_FAILED})


@pytest.mark.asyncio
@patch("app.webhooks.outbound.emit_webhook", new_callable=AsyncMock)
async def test_emit_capture_event_delegates(mock_emit):
    result = _result()
    await emit_capture_event(result, kind="voice", telegram_chat_id=7)
    mock_emit.assert_awaited_once()
    assert mock_emit.await_args.args[0]["event"] == EVENT_NOTE_CREATED
    assert mock_emit.await_args.args[0]["kind"] == "voice"


@pytest.mark.asyncio
@patch("app.webhooks.outbound.emit_webhook", new_callable=AsyncMock)
async def test_emit_entry_failed_event_delegates(mock_emit):
    await emit_entry_failed_event(
        task_name="process_text_message",
        error=RuntimeError("fail"),
        chat_id=1,
    )
    mock_emit.assert_awaited_once()
    assert mock_emit.await_args.args[0]["event"] == EVENT_ENTRY_FAILED
