import json
import logging
from pathlib import Path

from openai import AsyncOpenAI

from app.config import settings
from app.llm.schemas import ClassificationResult
from app.llm.tags import normalize_tags
from app.vault.reader import format_notes_for_prompt, known_titles, list_existing_notes

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "classify.txt"
MAX_RELATED = 3
MAX_TAGS = 5


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
        result = self._sanitize_related(result, existing)
        result = self._sanitize_action(result, existing)
        result = self._sanitize_tags(result)
        return result

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

    def _sanitize_action(
        self, result: ClassificationResult, existing: list
    ) -> ClassificationResult:
        """Stellt sicher, dass append nur fuer real existierende Titel erlaubt ist.

        Halluziniert das LLM einen target_title, der nicht im Vault existiert,
        fallen wir auf action='create' zurueck statt eine nicht existierende
        Notiz zu ergaenzen.
        """
        if result.action != "append":
            result.target_title = None
            return result

        if not result.target_title:
            logger.warning(
                "LLM returned action=append without target_title; falling back to create"
            )
            result.action = "create"
            result.target_title = None
            return result

        titles = known_titles(existing)
        canonical = titles.get(result.target_title.lower())
        if not canonical:
            logger.warning(
                "LLM hallucinated target_title=%r; falling back to action=create",
                result.target_title,
            )
            result.action = "create"
            result.target_title = None
            return result

        result.target_title = canonical
        return result

    def _sanitize_tags(self, result: ClassificationResult) -> ClassificationResult:
        result.tags = normalize_tags(result.tags, max_tags=MAX_TAGS)
        return result
