from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

SECRET = "test-webhook-secret"
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_rejects_missing_secret():
    response = client.post("/webhook", json={"message": {"text": "hi", "chat": {"id": 1}}})
    assert response.status_code == 401


def test_webhook_rejects_wrong_secret():
    response = client.post(
        "/webhook",
        json={"message": {"text": "hi", "chat": {"id": 1}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    )
    assert response.status_code == 401


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_enqueues_text_message(mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 1001,
            "message": {
                "message_id": 7,
                "text": "Hello",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_task.delay.assert_called_once_with("Hello", 42, 1001, 7)
    mock_send.assert_called_once()
    assert mock_send.call_args[0][1] == "Wird verarbeitet…"


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_voice_message_task")
def test_webhook_enqueues_voice_message(mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 1002,
            "message": {
                "message_id": 8,
                "voice": {"file_id": "voice123"},
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with("voice123", 42, 1002, 8)
    mock_send.assert_called_once()
    assert "Sprachnachricht" in mock_send.call_args[0][1]


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_allows_user_in_allowlist(mock_task, mock_send, mock_dup, monkeypatch):
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42,99")
    response = client.post(
        "/webhook",
        json={
            "update_id": 2001,
            "message": {
                "message_id": 1,
                "text": "Hi",
                "from": {"id": 42},
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with("Hi", 42, 2001, 1)
    mock_send.assert_called_once()
    assert mock_send.call_args[0][1] == "Wird verarbeitet…"


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_rejects_user_not_in_allowlist(
    mock_task, mock_send, mock_dup, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42,99")
    response = client.post(
        "/webhook",
        json={
            "update_id": 2002,
            "message": {
                "message_id": 1,
                "text": "Hi",
                "from": {"id": 7},
                "chat": {"id": 7},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "privat" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_rejects_missing_from_when_allowlist_active(
    mock_task, mock_send, mock_dup, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_allowed_user_ids", "42")
    response = client.post(
        "/webhook",
        json={
            "update_id": 2003,
            "message": {"message_id": 1, "text": "Hi", "chat": {"id": 42}},
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "privat" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=True)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_silently_drops_duplicate_update(mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 3001,
            "message": {
                "message_id": 1,
                "text": "Hi",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_dup.assert_awaited_once_with(3001)
    mock_task.delay.assert_not_called()
    mock_send.assert_not_called()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.handle_command", new_callable=AsyncMock)
def test_webhook_dispatches_slash_command_without_enqueue(
    mock_handle, mock_task, mock_send, mock_dup
):
    """Slash-Commands gehen direkt durch handle_command, nicht in den
    Celery-Worker — kein LLM-Call, keine Notiz-Anlage."""
    mock_handle.return_value = "Letzte Notizen: ..."

    response = client.post(
        "/webhook",
        json={
            "update_id": 4001,
            "message": {
                "message_id": 1,
                "text": "/recent",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_handle.assert_awaited_once()
    args, _ = mock_handle.call_args
    assert args[0] == "/recent"
    assert args[1] == 42
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert mock_send.call_args[0][1] == "Letzte Notizen: ..."


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.handle_command", new_callable=AsyncMock)
def test_webhook_normal_text_still_goes_to_worker(
    mock_handle, mock_task, mock_send, mock_dup
):
    """Sanity: nicht-Command-Text loest weiterhin den Worker aus
    (kein versehentlicher Command-Dispatch)."""
    response = client.post(
        "/webhook",
        json={
            "update_id": 4002,
            "message": {
                "message_id": 1,
                "text": "Merke dir diese Idee",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_handle.assert_not_awaited()
    mock_task.delay.assert_called_once()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_skips_duplicate_check_when_no_update_id(
    mock_task, mock_send, mock_dup
):
    response = client.post(
        "/webhook",
        json={"message": {"text": "Hi", "chat": {"id": 42}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_dup.assert_not_awaited()
    mock_task.delay.assert_called_once_with("Hi", 42, None, None)
