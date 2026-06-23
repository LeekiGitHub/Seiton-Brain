"""Embedding-Provider fuer semantische Suche (E17-2).

Bewusst getrennt vom ``LLMProvider`` (Klassifikation), aber nach demselben
Muster: ein abstraktes Interface plus eine Factory, damit spaeter lokale
Embeddings (z. B. via Ollama) ohne Aenderung der Aufrufer andocken koennen.

Die Engine berechnet Embeddings **zentral** (beim Indexieren) — nicht in den
Konsumenten (REST, MCP). Siehe ``docs/integrations/knowledge-retrieval.md``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Vektor fuer einen einzelnen Text."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Vektoren fuer mehrere Texte (eine API-Runde, reihenfolgetreu)."""


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
        # API garantiert die Reihenfolge ueber das ``index``-Feld — defensiv sortieren.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]


def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.llm_provider
    if provider == "openai":
        return OpenAIEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider for LLM_PROVIDER={provider!r}")
