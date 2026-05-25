import json
import os
from pathlib import Path

from openai import AsyncOpenAI

from app.llm.schemas import ClassificationResult

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "classify.txt"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        self.prompt_template = PROMPT_PATH.read_text()

    async def classify(self, text: str) -> ClassificationResult:
        prompt = self.prompt_template.replace("{input}", text)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        return ClassificationResult.model_validate(data)
