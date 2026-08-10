"""Tests fuer Digest in der Web-UI (E22-3)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.llm.schemas import DigestResult, NoteRef
from app.main import app

client = TestClient(app)


def test_ask_page_has_digest_card():
    response = client.get("/ask")
    assert response.status_code == 200
    assert 'id="digest-form"' in response.text
    assert 'id="digest-topic"' in response.text


@patch("app.ui.router.build_digest", new_callable=AsyncMock)
def test_digest_api_returns_result(mock_digest):
    mock_digest.return_value = DigestResult(
        topic="japan",
        digest="Du planst eine Japan-Reise im Herbst.",
        sources=[NoteRef(title="Japan Reiseroute", vault_path="Travel/Japan.md")],
        highlights=["Kyoto im November"],
        note_count=3,
        days=7,
    )

    response = client.post("/api/ui/digest", json={"topic": "japan"})

    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "japan"
    assert "Japan" in data["digest"]
    assert data["note_count"] == 3
    assert data["sources"][0]["vault_path"] == "Travel/Japan.md"
    mock_digest.assert_awaited_once()
    assert mock_digest.call_args.kwargs.get("days") == 7


@patch("app.ui.router.build_digest", new_callable=AsyncMock)
def test_digest_api_all_time(mock_digest):
    mock_digest.return_value = DigestResult(
        topic="work", digest="…", sources=[], highlights=[], note_count=1, days=None
    )

    response = client.post("/api/ui/digest", json={"topic": "work", "days": None})

    assert response.status_code == 200
    assert mock_digest.call_args.kwargs.get("days") is None


def test_digest_api_rejects_empty_topic():
    response = client.post("/api/ui/digest", json={"topic": ""})
    assert response.status_code == 422
