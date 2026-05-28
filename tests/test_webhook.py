from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

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


@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_enqueues_text_message(mock_task, mock_send):
    response = client.post(
        "/webhook",
        json={"message": {"text": "Hello", "chat": {"id": 42}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_task.delay.assert_called_once_with("Hello", 42)
    mock_send.assert_called_once()
    assert mock_send.call_args[0][1] == "Wird verarbeitet…"


@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_voice_message_task")
def test_webhook_enqueues_voice_message(mock_task, mock_send):
    response = client.post(
        "/webhook",
        json={"message": {"voice": {"file_id": "voice123"}, "chat": {"id": 42}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with("voice123", 42)
    mock_send.assert_called_once()
    assert "Sprachnachricht" in mock_send.call_args[0][1]


@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_allows_user_in_allowlist(mock_task, mock_send, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "42,99")
    response = client.post(
        "/webhook",
        json={
            "message": {
                "text": "Hi",
                "from": {"id": 42},
                "chat": {"id": 42},
            }
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with("Hi", 42)
    mock_send.assert_called_once()
    assert mock_send.call_args[0][1] == "Wird verarbeitet…"


@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_rejects_user_not_in_allowlist(mock_task, mock_send, monkeypatch):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "42,99")
    response = client.post(
        "/webhook",
        json={
            "message": {
                "text": "Hi",
                "from": {"id": 7},
                "chat": {"id": 7},
            }
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "privat" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_text_message_task")
def test_webhook_rejects_missing_from_when_allowlist_active(
    mock_task, mock_send, monkeypatch
):
    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "42")
    response = client.post(
        "/webhook",
        json={"message": {"text": "Hi", "chat": {"id": 42}}},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "privat" in mock_send.call_args[0][1].lower()
