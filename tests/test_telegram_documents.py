"""Tests fuer Telegram Foto-/Dokument-Capture (E22-2)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.document_capture import (
    MAX_EXTRACT_CHARS,
    TRUNCATION_MARKER,
    compose_capture_text,
    extract_document_text,
    supported_document,
)

SECRET = "test-webhook-secret"
client = TestClient(app)

HEADERS = {"X-Telegram-Bot-Api-Secret-Token": SECRET}


# --- Service ---------------------------------------------------------------


def test_supported_document():
    assert supported_document("notes.md") is True
    assert supported_document("scan.pdf") is True
    assert supported_document("brief.docx") is True
    assert supported_document("archiv.zip") is False
    assert supported_document("") is False


def test_extract_document_text_txt():
    text = extract_document_text("Hallo Welt\n".encode(), "note.txt")
    assert text == "Hallo Welt"


def test_extract_document_text_unsupported():
    assert extract_document_text(b"binary", "data.zip") == ""


def test_extract_document_text_truncates():
    huge = ("x" * (MAX_EXTRACT_CHARS + 500)).encode()
    text = extract_document_text(huge, "big.txt")
    assert text.endswith(TRUNCATION_MARKER)
    assert len(text) <= MAX_EXTRACT_CHARS + len(TRUNCATION_MARKER)


def test_compose_capture_text_with_caption():
    text = compose_capture_text("Inhalt", file_name="cv.pdf", caption="Mein Lebenslauf")
    assert text.startswith("Mein Lebenslauf")
    assert "Aus Datei: cv.pdf" in text
    assert text.endswith("Inhalt")


def test_compose_capture_text_without_caption():
    text = compose_capture_text("Inhalt", file_name="cv.pdf", caption=None)
    assert text.startswith("Aus Datei: cv.pdf")


# --- Webhook ----------------------------------------------------------------


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_document_message_task")
def test_webhook_enqueues_document(mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 3001,
            "message": {
                "message_id": 11,
                "document": {
                    "file_id": "doc123",
                    "file_name": "lebenslauf.pdf",
                    "file_size": 1024,
                },
                "caption": "Mein CV",
                "chat": {"id": 42},
            },
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with(
        "doc123", "lebenslauf.pdf", "Mein CV", 42, 3001, 11
    )
    assert "Dokument" in mock_send.call_args[0][1]


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_document_message_task")
def test_webhook_rejects_unsupported_document(mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 3002,
            "message": {
                "message_id": 12,
                "document": {"file_id": "zip1", "file_name": "archiv.zip"},
                "chat": {"id": 42},
            },
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    assert "nicht unterstützt" in mock_send.call_args[0][1]


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_document_message_task")
def test_webhook_rejects_oversized_document(mock_task, mock_send, mock_dup, monkeypatch):
    monkeypatch.setattr(settings, "telegram_document_max_bytes", 100)
    response = client.post(
        "/webhook",
        json={
            "update_id": 3003,
            "message": {
                "message_id": 13,
                "document": {
                    "file_id": "big1",
                    "file_name": "gross.pdf",
                    "file_size": 500,
                },
                "chat": {"id": 42},
            },
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    assert "zu groß" in mock_send.call_args[0][1]


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_document_message_task")
@patch("app.telegram.webhook.photo_extraction_ready", return_value=True)
def test_webhook_enqueues_largest_photo(mock_ready, mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 3004,
            "message": {
                "message_id": 14,
                "photo": [
                    {"file_id": "small", "file_size": 100},
                    {"file_id": "large", "file_size": 900},
                ],
                "caption": "Whiteboard",
                "chat": {"id": 42},
            },
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    mock_task.delay.assert_called_once_with(
        "large", "foto.jpg", "Whiteboard", 42, 3004, 14, "photo"
    )
    assert "Foto" in mock_send.call_args[0][1]


@patch("app.telegram.webhook._is_duplicate_update", new_callable=AsyncMock, return_value=False)
@patch("app.telegram.webhook.send_message", new_callable=AsyncMock)
@patch("app.telegram.webhook.process_document_message_task")
@patch("app.telegram.webhook.photo_extraction_ready", return_value=False)
def test_webhook_photo_needs_ocr_or_vision(mock_ready, mock_task, mock_send, mock_dup):
    response = client.post(
        "/webhook",
        json={
            "update_id": 3005,
            "message": {
                "message_id": 15,
                "photo": [{"file_id": "p1", "file_size": 100}],
                "chat": {"id": 42},
            },
        },
        headers=HEADERS,
    )

    assert response.status_code == 200
    mock_task.delay.assert_not_called()
    assert "OCR" in mock_send.call_args[0][1]


# --- Worker -----------------------------------------------------------------


@patch("app.worker.tasks._process_text", new_callable=AsyncMock)
@patch("app.worker.tasks.download_file", new_callable=AsyncMock)
def test_process_document_extracts_and_captures(mock_download, mock_process_text):
    from app.worker.tasks import _process_document
    import asyncio

    mock_download.return_value = "Notizinhalt aus Datei\n".encode()

    asyncio.run(
        _process_document(
            "doc123",
            "notiz.txt",
            "Kontext",
            42,
            telegram_update_id=3001,
            telegram_message_id=11,
        )
    )

    mock_process_text.assert_awaited_once()
    composed = mock_process_text.call_args.args[0]
    assert composed.startswith("Kontext")
    assert "Aus Datei: notiz.txt" in composed
    assert "Notizinhalt aus Datei" in composed
    assert mock_process_text.call_args.kwargs["kind"] == "document"


@patch("app.worker.tasks.send_message", new_callable=AsyncMock)
@patch("app.worker.tasks._process_text", new_callable=AsyncMock)
@patch("app.worker.tasks.download_file", new_callable=AsyncMock)
def test_process_document_no_text_informs_user(
    mock_download, mock_process_text, mock_send
):
    from app.worker.tasks import _process_document
    import asyncio

    mock_download.return_value = b"binarydata"

    asyncio.run(_process_document("doc456", "scan.zip", None, 42))

    mock_process_text.assert_not_awaited()
    mock_send.assert_awaited_once()
    assert "kein Text" in mock_send.call_args.args[1]
