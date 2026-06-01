from abc import ABC, abstractmethod

from app.config import settings
from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import ClassificationResult


class LLMProvider(ABC):
    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        pass


def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
