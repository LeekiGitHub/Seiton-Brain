import os
from abc import ABC, abstractmethod

from app.llm.openai_provider import OpenAIProvider
from app.llm.schemas import ClassificationResult


class LLMProvider(ABC):
    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        pass


def get_llm_provider() -> LLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    if provider == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
