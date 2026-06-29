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


@patch("app.api.v1.routes.emit_capture_event", new_callable=AsyncMock)
@patch("app.api.v1.routes.process_text_message", new_callable=AsyncMock)
def test_capture_returns_pipeline_result(mock_process, mock_emit):
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
    mock_emit.assert_awaited_once()


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


@patch("app.api.v1.routes.retrieve_vault_notes", new_callable=AsyncMock)
def test_search_notes_returns_hits(mock_retrieve):
    from app.vault.index import SearchHit

    mock_retrieve.return_value = [
        SearchHit(
            title="Fitness App",
            vault_path="Ideas/Fitness App.md",
            snippet="Workout tracking",
            category="idea",
            folder="Ideas",
        )
    ]

    response = client.get(
        "/v1/notes/search?q=fitness&limit=5",
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "fitness"
    assert data["limit"] == 5
    assert data["semantic"] is False
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Fitness App"
    mock_retrieve.assert_awaited_once()
    assert mock_retrieve.await_args.kwargs["semantic"] is False


@patch("app.api.v1.routes.retrieve_vault_notes", new_callable=AsyncMock)
def test_search_notes_semantic_flag(mock_retrieve):
    from app.vault.index import SearchHit

    mock_retrieve.return_value = [
        SearchHit(
            title="Japan Trip",
            vault_path="Travel/Japan.md",
            snippet="Tokyo plans",
            category="travel",
            folder="Travel",
        )
    ]

    response = client.get(
        "/v1/notes/search?q=japan&semantic=true",
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["semantic"] is True
    assert data["items"][0]["title"] == "Japan Trip"
    assert mock_retrieve.await_args.kwargs["semantic"] is True


@patch("app.api.v1.routes.answer_question", new_callable=AsyncMock)
def test_ask_returns_answer_result(mock_answer):
    from app.llm.schemas import AnswerResult, NoteRef

    mock_answer.return_value = AnswerResult(
        answer="Du hattest Ideen zu Japan.",
        sources=[NoteRef(title="Japan Reiseroute", vault_path="Travel/Japan.md")],
        confidence=0.85,
    )

    response = client.post(
        "/v1/ask",
        json={"question": "Was weiß ich über Japan?"},
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Du hattest Ideen zu Japan."
    assert data["confidence"] == 0.85
    assert len(data["sources"]) == 1
    assert data["sources"][0]["title"] == "Japan Reiseroute"
    mock_answer.assert_awaited_once()


def test_ask_rejects_empty_question():
    response = client.post(
        "/v1/ask",
        json={"question": ""},
        headers=API_HEADERS,
    )
    assert response.status_code == 422


@patch("app.api.v1.routes.build_digest", new_callable=AsyncMock)
def test_digest_returns_digest_result(mock_digest):
    from app.llm.schemas import DigestResult, NoteRef

    mock_digest.return_value = DigestResult(
        topic="Ideas",
        digest="Drei Ideen diese Woche.",
        sources=[NoteRef(title="Side Project", vault_path="Ideas/Side.md")],
        highlights=["Fokus auf API"],
        note_count=3,
        days=7,
    )

    response = client.post(
        "/v1/digest",
        json={"topic": "Ideas", "days": 7},
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Ideas"
    assert data["note_count"] == 3
    assert data["highlights"] == ["Fokus auf API"]
    mock_digest.assert_awaited_once()


def test_digest_rejects_empty_topic():
    response = client.post(
        "/v1/digest",
        json={"topic": ""},
        headers=API_HEADERS,
    )
    assert response.status_code == 422


def test_get_entry_returns_summary():
    entry = MagicMock()
    entry.id = 99
    entry.title = "Note A"
    entry.category = "note"
    entry.summary = "Summary"
    entry.vault_path = "Notes/Note A.md"
    entry.status = "processed"
    entry.kind = "text"
    entry.created_at = datetime(2026, 6, 7, tzinfo=timezone.utc)

    db = MagicMock()
    db.get = AsyncMock(return_value=entry)

    async def fake_get_db():
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    try:
        response = client.get("/v1/entries/99", headers=API_HEADERS)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == 99
    assert response.json()["title"] == "Note A"


def test_get_entry_not_found():
    db = MagicMock()
    db.get = AsyncMock(return_value=None)

    async def fake_get_db():
        yield db

    app.dependency_overrides[get_db] = fake_get_db
    try:
        response = client.get("/v1/entries/404", headers=API_HEADERS)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_note_content_reads_vault_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))
    notes = tmp_path / "Notes"
    notes.mkdir()
    note = notes / "Hello.md"
    note.write_text("---\ntitle: Hello\n---\n\n# Body", encoding="utf-8")

    response = client.get(
        "/v1/notes/content?vault_path=Notes/Hello.md",
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["vault_path"] == "Notes/Hello.md"
    assert "Body" in data["content"]
    assert data["title"] == "Hello"


def test_get_note_content_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "obsidian_vault_path", str(tmp_path))

    response = client.get(
        "/v1/notes/content?vault_path=../../../etc/passwd",
        headers=API_HEADERS,
    )

    assert response.status_code == 400


def test_capture_rejects_empty_text():
    response = client.post(
        "/v1/capture",
        json={"text": ""},
        headers=API_HEADERS,
    )
    assert response.status_code == 422
