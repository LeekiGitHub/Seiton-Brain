"""Tests fuer den RAG-Antwort-Service + Provider/Parser (E17-3)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.config import settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.parser import AnswerParseError, parse_answer_json
from app.llm.schemas import AnswerResult, LLMAnswer, NoteRef
from app.services import answer as answer_service
from app.services.answer import (
    NO_CONTEXT_ANSWER,
    answer_question,
    format_answer_for_chat,
)
from app.vault.index import SearchHit


def _hit(title: str, vault_path: str, snippet: str = "snippet") -> SearchHit:
    return SearchHit(
        title=title,
        vault_path=vault_path,
        snippet=snippet,
        category="idea",
        folder="Ideas",
    )


def _chat_completion(content: str) -> MagicMock:
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


# ─── Parser ───────────────────────────────────────────────────────────────


def test_parse_answer_json_valid():
    parsed = parse_answer_json(
        '{"answer": "Ja", "sources": ["A", "B"], "confidence": 0.8}'
    )
    assert isinstance(parsed, LLMAnswer)
    assert parsed.answer == "Ja"
    assert parsed.sources == ["A", "B"]
    assert parsed.confidence == 0.8


def test_parse_answer_json_defaults():
    parsed = parse_answer_json('{"answer": "Nur Antwort"}')
    assert parsed.sources == []
    assert parsed.confidence == 0.0


def test_parse_answer_json_invalid_json_raises():
    with pytest.raises(json.JSONDecodeError):
        parse_answer_json("not json {{")


def test_parse_answer_json_invalid_schema_raises():
    with pytest.raises(ValidationError):
        parse_answer_json('{"sources": []}')  # 'answer' fehlt


# ─── Provider.answer ────────────────────────────────────────────────────────


def _provider() -> OpenAIProvider:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.answer_template = "Q: {question}\nC: {context}"
    return provider


@pytest.mark.asyncio
async def test_provider_answer_success():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        return_value=_chat_completion(
            '{"answer": "42", "sources": ["Note A"], "confidence": 0.9}'
        )
    )

    result = await provider.answer("Wieviel?", "- \"Note A\": ...")

    assert result.answer == "42"
    assert result.sources == ["Note A"]
    provider.client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_provider_answer_retries_then_succeeds():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        side_effect=[
            _chat_completion("broken {{"),
            _chat_completion('{"answer": "ok", "sources": [], "confidence": 0.5}'),
        ]
    )

    result = await provider.answer("Frage", "ctx")

    assert result.answer == "ok"
    assert provider.client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_provider_answer_gives_up_raises():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        return_value=_chat_completion("still broken {{")
    )

    with pytest.raises(AnswerParseError):
        await provider.answer("Frage", "ctx")


# ─── Service answer_question ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_answer_question_empty_question_skips_llm():
    db = AsyncMock()
    with patch("app.services.answer.get_llm_provider") as mock_provider:
        result = await answer_question("   ", db)
    assert result.answer == NO_CONTEXT_ANSWER
    assert result.sources == []
    mock_provider.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.answer.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.get_llm_provider")
async def test_answer_question_no_hits_skips_llm(
    mock_provider, mock_keyword, mock_semantic, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    mock_keyword.return_value = []
    db = AsyncMock()

    result = await answer_question("Was weiß ich über X?", db)

    assert result.answer == NO_CONTEXT_ANSWER
    assert result.confidence == 0.0
    mock_provider.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.answer.search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.get_llm_provider")
async def test_answer_question_with_hits_resolves_sources(
    mock_provider, mock_keyword, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", False)
    mock_keyword.return_value = [
        _hit("Japan Reiseroute", "Travel/Japan Reiseroute.md"),
        _hit("Tokio Cafés", "Travel/Tokio Cafés.md"),
    ]
    llm = MagicMock()
    llm.answer = AsyncMock(
        return_value=LLMAnswer(
            answer="Du hattest Ideen zu Japan.",
            # "Hokkaido" ist halluziniert -> muss verworfen werden
            sources=["Japan Reiseroute", "Hokkaido"],
            confidence=1.5,  # ausserhalb [0,1] -> wird geklemmt
        )
    )
    mock_provider.return_value = llm
    db = AsyncMock()

    result = await answer_question("Japan-Ideen?", db)

    assert isinstance(result, AnswerResult)
    assert result.answer == "Du hattest Ideen zu Japan."
    assert [s.title for s in result.sources] == ["Japan Reiseroute"]
    assert result.sources[0].vault_path == "Travel/Japan Reiseroute.md"
    assert result.confidence == 1.0  # geklemmt
    llm.answer.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.answer.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.get_llm_provider")
async def test_answer_question_prefers_semantic_when_enabled(
    mock_provider, mock_keyword, mock_semantic, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    mock_semantic.return_value = [_hit("Semantic Hit", "Notes/Semantic Hit.md")]
    llm = MagicMock()
    llm.answer = AsyncMock(
        return_value=LLMAnswer(answer="a", sources=[], confidence=0.3)
    )
    mock_provider.return_value = llm
    db = AsyncMock()

    await answer_question("frage", db)

    mock_semantic.assert_awaited_once()
    mock_keyword.assert_not_awaited()  # semantische Treffer -> kein Fallback


@pytest.mark.asyncio
@patch("app.services.answer.semantic_search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.search_vault_notes", new_callable=AsyncMock)
@patch("app.services.answer.get_llm_provider")
async def test_answer_question_falls_back_to_keyword(
    mock_provider, mock_keyword, mock_semantic, monkeypatch
):
    monkeypatch.setattr(settings, "embeddings_enabled", True)
    mock_semantic.return_value = []  # keine semantischen Treffer
    mock_keyword.return_value = [_hit("Keyword Hit", "Notes/Keyword Hit.md")]
    llm = MagicMock()
    llm.answer = AsyncMock(
        return_value=LLMAnswer(answer="a", sources=["Keyword Hit"], confidence=0.6)
    )
    mock_provider.return_value = llm
    db = AsyncMock()

    result = await answer_question("frage", db)

    mock_semantic.assert_awaited_once()
    mock_keyword.assert_awaited_once()
    assert [s.title for s in result.sources] == ["Keyword Hit"]


# ─── Chat-Formatter ─────────────────────────────────────────────────────────


def test_format_answer_for_chat_with_sources():
    result = AnswerResult(
        answer="Antwort.",
        sources=[NoteRef(title="A"), NoteRef(title="B")],
        confidence=0.7,
    )
    text = format_answer_for_chat(result)
    assert "Antwort." in text
    assert "Quellen: [[A]], [[B]]" in text


def test_format_answer_for_chat_without_sources():
    result = AnswerResult(answer="Nur Antwort.", sources=[], confidence=0.0)
    assert format_answer_for_chat(result) == "Nur Antwort."


def test_no_context_answer_constant_used():
    """Sanity: Service-Modul exportiert die Konstante stabil."""
    assert answer_service.NO_CONTEXT_ANSWER == NO_CONTEXT_ANSWER
