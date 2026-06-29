"""Tests fuer Digest-Service + Parser/Provider (E17-8)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.llm.openai_provider import OpenAIProvider
from app.llm.parser import parse_digest_json
from app.llm.schemas import DigestResult, LLMDigest, NoteRef
from app.services.digest import (
    NO_NOTES_DIGEST,
    build_digest,
    format_digest_for_chat,
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


def test_parse_digest_json_valid():
    parsed = parse_digest_json(
        '{"digest": "Zusammenfassung", "sources": ["A"], "highlights": ["h1"]}'
    )
    assert isinstance(parsed, LLMDigest)
    assert parsed.digest == "Zusammenfassung"
    assert parsed.highlights == ["h1"]


def test_parse_digest_json_invalid_schema_raises():
    with pytest.raises(ValidationError):
        parse_digest_json('{"sources": []}')


def _provider() -> OpenAIProvider:
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.digest_template = "T: {topic}\nD: {days}\nC: {context}"
    return provider


@pytest.mark.asyncio
async def test_provider_digest_success():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        return_value=_chat_completion(
            '{"digest": "Overview", "sources": ["Note A"], "highlights": ["x"]}'
        )
    )
    result = await provider.digest("Ideas", '- "Note A"', days=7)
    assert result.digest == "Overview"
    assert result.sources == ["Note A"]


@pytest.mark.asyncio
@patch("app.services.digest.get_llm_provider")
@patch("app.services.digest.collect_digest_notes", new_callable=AsyncMock)
async def test_build_digest_no_notes(mock_collect, mock_provider):
    mock_collect.return_value = []
    result = await build_digest("Ideas", AsyncMock())
    assert result.digest == NO_NOTES_DIGEST
    assert result.note_count == 0
    mock_provider.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.digest.get_llm_provider")
@patch("app.services.digest.collect_digest_notes", new_callable=AsyncMock)
async def test_build_digest_with_notes(mock_collect, mock_provider):
    mock_collect.return_value = [_hit("Note A", "Ideas/A.md")]
    llm = MagicMock()
    llm.digest = AsyncMock(
        return_value=LLMDigest(
            digest="Synthese",
            sources=["Note A"],
            highlights=["Takeaway"],
        )
    )
    mock_provider.return_value = llm

    result = await build_digest("Ideas", AsyncMock(), days=7)

    assert result.topic == "Ideas"
    assert result.digest == "Synthese"
    assert result.note_count == 1
    assert result.sources == [NoteRef(title="Note A", vault_path="Ideas/A.md")]
    assert result.highlights == ["Takeaway"]


def test_format_digest_for_chat_includes_sources():
    text = format_digest_for_chat(
        DigestResult(
            topic="Ideas",
            digest="Kurz",
            sources=[NoteRef(title="A", vault_path="Ideas/A.md")],
            highlights=["h"],
            note_count=1,
            days=7,
        )
    )
    assert "Digest: Ideas" in text
    assert "letzte 7 Tage" in text
    assert "[[A]]" in text
    assert "Highlights:" in text
