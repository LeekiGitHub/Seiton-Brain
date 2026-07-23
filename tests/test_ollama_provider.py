"""Tests fuer Ollama-Provider und LLM-Factory (E7-2)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.llm.ollama_provider import OllamaProvider, ollama_v1_base_url
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult


def test_ollama_v1_base_url_appends_v1():
    assert ollama_v1_base_url("http://localhost:11434") == "http://localhost:11434/v1/"
    assert ollama_v1_base_url("http://host:11434/") == "http://host:11434/v1/"
    assert ollama_v1_base_url("http://host:11434/v1") == "http://host:11434/v1/"
    assert ollama_v1_base_url("http://host:11434/v1/") == "http://host:11434/v1/"


def test_get_llm_provider_openai(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    assert isinstance(get_llm_provider(), OpenAIProvider)


def test_get_llm_provider_ollama(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "Ollama")
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:11434")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2")
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "llama3.2"
    assert str(provider.client.base_url).rstrip("/") == "http://127.0.0.1:11434/v1"


def test_get_llm_provider_unsupported(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        get_llm_provider()


@pytest.mark.asyncio
async def test_ollama_classify_reuses_openai_pipeline(monkeypatch):
    """OllamaProvider erbt Sanitize/Parse — nur der Client ist Ollama."""
    monkeypatch.setattr(settings, "ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr(settings, "ollama_model", "llama3.2")

    provider = OllamaProvider()
    payload = (
        '{"action":"create","title":"T","summary":"S","category":"inbox",'
        '"tags":[],"related":[],"target_title":null}'
    )
    provider.client = MagicMock()
    provider.client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content=payload))]
        )
    )

    with (
        patch("app.llm.openai_provider.list_existing_notes", new_callable=AsyncMock) as notes,
        patch("app.llm.openai_provider.prefilter_notes_for_llm", return_value=[]),
    ):
        notes.return_value = []
        result = await provider.classify("hello")

    assert isinstance(result, ClassificationResult)
    assert result.title == "T"
    provider.client.chat.completions.create.assert_awaited_once()
    call_kwargs = provider.client.chat.completions.create.await_args.kwargs
    assert call_kwargs["model"] == "llama3.2"
    assert call_kwargs["response_format"] == {"type": "json_object"}
