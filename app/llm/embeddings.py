"""Embedding provider for semantic search (E17-2).

Kept separate from ``LLMProvider`` (classification), but same pattern: an
abstract interface plus a factory so local embeddings (e.g. via Ollama) can
plug in without changing callers.

The engine computes embeddings **centrally** (at index time) — not in
consumers (REST, MCP). See ``docs/integrations/knowledge-retrieval.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Vector for a single text."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Vectors for multiple texts (one API round-trip, order-preserving)."""


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        return list(response.data[0].embedding)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embeddings.create(model=self.model, input=texts)
        # API guarantees order via the ``index`` field — sort defensively anyway.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.llm_provider
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider for LLM_PROVIDER={provider!r}")
