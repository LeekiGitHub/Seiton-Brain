import json
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.vault.reader import format_notes_for_prompt, known_titles, list_existing_notes

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "classify.txt"
MAX_RELATED = 3


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.prompt_template = PROMPT_PATH.read_text()

    async def classify(self, text: str) -> ClassificationResult:
        existing = list_existing_notes()
        prompt = (
            self.prompt_template.replace("{input}", text)
            .replace("{existing_notes}", format_notes_for_prompt(existing))
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        result = ClassificationResult.model_validate(data)
        return self._sanitize_related(result, existing)

    def _sanitize_related(
        self, result: ClassificationResult, existing: list
    ) -> ClassificationResult:
        titles = known_titles(existing)
        resolved: list[str] = []
        for title in result.related:
            canonical = titles.get(title.lower())
            if canonical and canonical.lower() != result.title.lower():
                if canonical not in resolved:
                    resolved.append(canonical)
        result.related = resolved[:MAX_RELATED]
        return result
