from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.db.session import get_db
from app.llm.schemas import ClassificationResult
from app.main import app
from app.services.process_message import ProcessMessageResult

client = TestClient(app)

API_HEADERS = {"X-Seiton-Api-Key": "test-seiton-api-key"}


def _classification() -> ClassificationResult:
    return ClassificationResult(
        category="idea",
        title="API Idea",
        summary="From API.",
        tags=["idea"],
    )


def _process_result() -> ProcessMessageResult:
    return ProcessMessageResult(
        classification=_classification(),
        entry_id=7,
        vault_path="Ideas/API Idea.md",
        status="processed",
    )


def test_api_disabled_when_key_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "seiton_api_key", "")

    response = client.post(
        "/v1/capture",
        json={"text": "hi"},
        headers=API_HEADERS,
    )

    assert response.status_code == 503
    assert "SEITON_API_KEY" in response.json()["detail"]


def test_api_rejects_missing_key_header():
    response = client.post("/v1/capture", json={"text": "hi"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"


def test_api_rejects_invalid_key_header():
    response = client.post(
        "/v1/capture",
        json={"text": "hi"},
        headers={"X-Seiton-Api-Key": "wrong-key"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


@patch("app.api.v1.routes.process_text_message", new_callable=AsyncMock)
def test_capture_returns_pipeline_result(mock_process):
    mock_process.return_value = _process_result()

    response = client.post(
        "/v1/capture",
        json={"text": "Merke dir diese Idee"},
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entry_id"] == 7
    assert data["vault_path"] == "Ideas/API Idea.md"
    assert data["status"] == "processed"
    assert data["classification"]["title"] == "API Idea"


@patch("app.api.v1.routes.process_text_message", new_callable=AsyncMock)
def test_capture_rejects_duplicate(mock_process):
    mock_process.return_value = None

    response = client.post(
        "/v1/capture",
        json={"text": "dup"},
        headers=API_HEADERS,
    )

    assert response.status_code == 409


@patch("app.api.v1.routes.get_llm_provider")
def test_classify_returns_llm_result(mock_provider):
    llm = MagicMock()
    llm.classify = AsyncMock(return_value=_classification())
    mock_provider.return_value = llm

    response = client.post(
        "/v1/classify",
        json={"text": "Nur klassifizieren"},
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "API Idea"
    llm.classify.assert_awaited_once_with("Nur klassifizieren")


def test_list_entries_returns_summaries():
    entry = MagicMock()
    entry.id = 1
    entry.title = "Note A"
    entry.category = "note"
    entry.summary = "Summary"
    entry.vault_path = "Notes/Note A.md"
    entry.status = "processed"
    entry.kind = "text"
    entry.created_at = datetime(2026, 6, 7, tzinfo=timezone.utc)

    result = MagicMock()
    result.scalars.return_value.all.return_value = [entry]

    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    async def fake_get_db():
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    try:
        response = client.get(
            "/v1/entries?limit=5&offset=0",
            headers=API_HEADERS,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Note A"


def test_capture_rejects_empty_text():
    response = client.post(
        "/v1/capture",
        json={"text": ""},
        headers=API_HEADERS,
    )
    assert response.status_code == 422
