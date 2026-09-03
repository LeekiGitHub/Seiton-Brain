from abc import ABC, abstractmethod

from app.config import settings
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import ClassificationResult, LLMAnswer, LLMDigest


class LLMProvider(ABC):
    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        pass

    @abstractmethod
    async def answer(self, question: str, context: str) -> LLMAnswer:
        """RAG answer for ``question``, grounded in the ``context`` block (E17-3)."""

    @abstractmethod
    async def digest(self, topic: str, context: str, *, days: int | None) -> LLMDigest:
        """Digest synthesis (E17-8) of multiple notes into one topic."""


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.strip().lower()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
