"""Tests fuer Suche & Ask UI (E19-3)."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.llm.schemas import AnswerResult, NoteRef
from app.main import app
from app.vault.index import SearchHit

client = TestClient(app)


def test_ask_page_renders():
    response = client.get("/ask")
    assert response.status_code == 200
    assert "Suchen" in response.text
    assert "ask.js" in response.text
    assert 'href="/ask"' in response.text


@patch("app.ui.router.retrieve_vault_notes", new_callable=AsyncMock)
def test_search_api_returns_hits(mock_retrieve):
    mock_retrieve.return_value = [
        SearchHit(
            title="Fitness App",
            vault_path="Ideas/Fitness App.md",
            snippet="Workout tracking",
            category="idea",
            folder="Ideas",
        )
    ]

    response = client.get("/api/ui/search?q=fitness&limit=5")

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "fitness"
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Fitness App"
    mock_retrieve.assert_awaited_once()


@patch("app.ui.router.answer_question", new_callable=AsyncMock)
def test_ask_api_returns_answer(mock_answer):
    mock_answer.return_value = AnswerResult(
        answer="Du hattest Ideen zu Japan.",
        sources=[NoteRef(title="Japan Reiseroute", vault_path="Travel/Japan.md")],
        confidence=0.85,
    )

    response = client.post(
        "/api/ui/ask",
        json={"question": "Was weiß ich über Japan?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "Japan" in data["answer"]
    assert len(data["sources"]) == 1
    mock_answer.assert_awaited_once()
