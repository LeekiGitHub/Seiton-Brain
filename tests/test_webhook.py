from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

SECRET = "test-webhook-secret"
client = TestClient(app)


@patch("app.main.run_health_checks", new_callable=AsyncMock)
def test_health(mock_checks):
    mock_checks.return_value = {"database": "ok", "redis": "ok"}
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }


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
@patch("app.telegram.webhook.process_voice_message_task")
def test_webhook_rejects_oversized_voice(mock_task, mock_send, mock_dup, monkeypatch):
    monkeypatch.setattr(settings, "telegram_voice_max_bytes", 100)
    response = client.post(
        "/webhook",
        json={
            "update_id": 1003,
            "message": {
                "message_id": 9,
                "voice": {"file_id": "voice-big", "file_size": 500},
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "zu groß" in mock_send.call_args[0][1]


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
@patch("app.telegram.webhook.handle_command", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_ask_message_task")
def test_webhook_ask_command_enqueues_rag(mock_ask, mock_handle, mock_send, mock_dup):
    """`/ask` geht in den Worker (LLM-Call), NICHT synchron durch handle_command."""
    response = client.post(
        "/webhook",
        json={
            "update_id": 6001,
            "message": {
                "message_id": 1,
                "text": "/ask Was weiß ich über Japan?",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_ask.delay.assert_called_once_with("Was weiß ich über Japan?", 42)
    mock_handle.assert_not_awaited()
    mock_send.assert_called_once()
    assert "durchsuche" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_ask_message_task")
def test_webhook_ask_without_question_shows_usage(mock_ask, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 6002,
            "message": {"message_id": 1, "text": "/ask", "chat": {"id": 42}},
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_ask.delay.assert_not_called()
    mock_send.assert_called_once()
    assert "nutzung" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_ask_message_task")
def test_webhook_ask_strips_bot_suffix(mock_ask, mock_send, mock_dup):
    """`/ask@BotName frage` -> Bot-Suffix wird ignoriert, Frage bleibt."""
    response = client.post(
        "/webhook",
        json={
            "update_id": 6003,
            "message": {
                "message_id": 1,
                "text": "/ask@SeitonBot wo war ich im Mai?",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_ask.delay.assert_called_once_with("wo war ich im Mai?", 42)


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_digest_message_task")
def test_webhook_digest_command_enqueues_worker(mock_digest, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 6004,
            "message": {
                "message_id": 1,
                "text": "/digest Ideas",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_digest.delay.assert_called_once_with("Ideas", 42)
    mock_send.assert_called_once()
    assert "digest" in mock_send.call_args[0][1].lower()


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_digest_message_task")
def test_webhook_digest_without_topic_shows_usage(mock_digest, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 6005,
            "message": {"message_id": 1, "text": "/digest", "chat": {"id": 42}},
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )

    assert response.status_code == 200
    mock_digest.delay.assert_not_called()
    assert "nutzung" in mock_send.call_args[0][1].lower()


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


# ─── E1-4: Body-Size-Limit ────────────────────────────────────────────────


def test_webhook_rejects_oversized_body(monkeypatch):
    monkeypatch.setattr(settings, "telegram_webhook_max_body_bytes", 100)
    big_payload = {"x": "a" * 1000}
    response = client.post(
        "/webhook",
        json=big_payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 413


@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
def test_webhook_accepts_body_under_limit(mock_dup, mock_send, mock_task, monkeypatch):
    """Sanity: knapp unter dem Limit geht durch."""
    monkeypatch.setattr(settings, "telegram_webhook_max_body_bytes", 10_000)
    response = client.post(
        "/webhook",
        json={
            "update_id": 9001,
            "message": {"message_id": 1, "text": "hi", "chat": {"id": 42}},
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 200
    mock_task.delay.assert_called_once()


def test_webhook_rejects_invalid_json():
    response = client.post(
        "/webhook",
        content=b"not json {{{",
        headers={
            "X-Telegram-Bot-Api-Secret-Token": SECRET,
            "Content-Type": "application/json",
        },
    )
    assert response.status_code == 400


# ─── E1-4: Bekannte unsupported Update-Typen ──────────────────────────────


@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
def test_webhook_silently_ignores_edited_message(mock_send, mock_task):
    response = client.post(
        "/webhook",
        json={
            "update_id": 5001,
            "edited_message": {
                "message_id": 1,
                "text": "edited",
                "chat": {"id": 42},
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    mock_task.delay.assert_not_called()
    mock_send.assert_not_called()


@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
def test_webhook_silently_ignores_callback_query(mock_send, mock_task):
    response = client.post(
        "/webhook",
        json={
            "update_id": 5002,
            "callback_query": {"id": "cb1", "from": {"id": 42}, "data": "x"},
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    mock_send.assert_not_called()


@patch("app.telegram.webhook.process_text_message_task")
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
def test_webhook_silently_ignores_unknown_update_shape(mock_send, mock_task):
    """Vollkommen unbekanntes Update — wir 200en trotzdem, damit Telegram
    nicht retried."""
    response = client.post(
        "/webhook",
        json={"update_id": 5003, "some_future_field": {"foo": "bar"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    mock_send.assert_not_called()
