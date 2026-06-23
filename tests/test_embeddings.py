"""Tests fuer den Embedding-Provider (E17-2)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.llm.embeddings import OpenAIEmbeddingProvider, get_embedding_provider


def _provider() -> OpenAIEmbeddingProvider:
    provider = OpenAIEmbeddingProvider.__new__(OpenAIEmbeddingProvider)
    provider.model = "text-embedding-3-small"
    return provider


@pytest.mark.asyncio
async def test_embed_returns_vector():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])])
    )

    vec = await provider.embed("hello world")

    assert vec == [0.1, 0.2, 0.3]
    provider.client.embeddings.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_batch_orders_by_index():
    """OpenAI darf out-of-order liefern — wir sortieren nach ``index``."""
    provider = _provider()
    item0 = MagicMock(index=0, embedding=[1.0])
    item1 = MagicMock(index=1, embedding=[2.0])
    provider.client = MagicMock()
    provider.client.embeddings.create = AsyncMock(
        return_value=MagicMock(data=[item1, item0])
    )

    out = await provider.embed_batch(["a", "b"])

    assert out == [[1.0], [2.0]]


@pytest.mark.asyncio
async def test_embed_batch_empty_skips_api_call():
    provider = _provider()
    provider.client = MagicMock()
    provider.client.embeddings.create = AsyncMock()

    assert await provider.embed_batch([]) == []
    provider.client.embeddings.create.assert_not_awaited()


def test_get_embedding_provider_openai(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    assert isinstance(get_embedding_provider(), OpenAIEmbeddingProvider)


def test_get_embedding_provider_unsupported(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "does-not-exist")
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        get_embedding_provider()
