"""Tests for UI capture (E22-1)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.llm.schemas import ClassificationResult
from app.main import app
from app.services.process_message import ProcessMessageResult

client = TestClient(app)


def _process_result(action: str = "create") -> ProcessMessageResult:
    return ProcessMessageResult(
        classification=ClassificationResult(
            category="idea",
            title="Fitness App",
            summary="Eine App-Idee.",
            related=[],
            tags=["fitness"],
            action=action,
            target_title=None if action == "create" else "Fitness App",
        ),
        entry_id=42,
        vault_path="Ideas/Fitness App.md",
        status="processed",
    )


def test_dashboard_page_has_capture_form():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert 'id="capture-form"' in response.text
    assert 'id="capture-text"' in response.text


@patch("app.ui.router.emit_capture_event", new_callable=AsyncMock)
@patch("app.ui.router.process_text_message", new_callable=AsyncMock)
def test_capture_api_creates_note(mock_process, mock_emit):
    mock_process.return_value = _process_result()

    response = client.post("/api/ui/capture", json={"text": "Idee: Fitness App"})

    assert response.status_code == 200
    data = response.json()
    assert data["entry_id"] == 42
    assert data["title"] == "Fitness App"
    assert data["category"] == "idea"
    assert data["action"] == "create"
    assert data["vault_path"] == "Ideas/Fitness App.md"
    assert data["tags"] == ["fitness"]
    mock_process.assert_awaited_once()
    assert mock_process.call_args.kwargs.get("kind") == "text"
    mock_emit.assert_awaited_once()


@patch("app.ui.router.emit_capture_event", new_callable=AsyncMock)
@patch("app.ui.router.process_text_message", new_callable=AsyncMock)
def test_capture_api_append(mock_process, mock_emit):
    mock_process.return_value = _process_result(action="append")

    response = client.post("/api/ui/capture", json={"text": "Noch ein Gedanke"})

    assert response.status_code == 200
    assert response.json()["action"] == "append"


@patch("app.ui.router.process_text_message", new_callable=AsyncMock)
def test_capture_api_duplicate_conflict(mock_process):
    mock_process.return_value = None

    response = client.post("/api/ui/capture", json={"text": "Doppelt"})

    assert response.status_code == 409


def test_capture_api_rejects_empty_text():
    response = client.post("/api/ui/capture", json={"text": ""})
    assert response.status_code == 422
