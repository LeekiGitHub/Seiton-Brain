from abc import ABC, abstractmethod

from app.config import settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import ClassificationResult, LLMAnswer


class LLMProvider(ABC):
    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        pass

    @abstractmethod
    async def answer(self, question: str, context: str) -> LLMAnswer:
        """RAG-Antwort auf ``question``, gestuetzt auf den ``context``-Block (E17-3)."""


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
