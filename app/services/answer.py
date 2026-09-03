"""RAG answer service (E17-3).

Wires retrieval (E17-1 keyword / E17-2 semantic) and LLM generation together:
question → relevant vault notes → answer prompt with context →
``AnswerResult`` with resolved sources.

Deliberately **no** Telegram/REST code here — consumers are ``/ask``
(E17-4) and ``POST /v1/ask`` (E17-5). This service is the shared core.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import AnswerResult, NoteRef
from app.vault.index import SearchHit, retrieve_vault_notes

logger = logging.getLogger(__name__)

DEFAULT_CONTEXT_LIMIT = 5

# Reply when the vault has nothing relevant — deliberately skip the LLM call
# to save cost and avoid hallucinations over empty context.
NO_CONTEXT_ANSWER = "Dazu habe ich nichts in deinem Vault gefunden."


def _format_context(hits: list[SearchHit]) -> str:
    """Numbered context block for the prompt — titles exact for copying."""
    lines: list[str] = []
    for hit in hits:
        lines.append(f'- "{hit.title}" ({hit.folder}): {hit.snippet}')
    return "\n".join(lines)


def _clamp_confidence(value: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def _resolve_sources(
    source_titles: list[str], hits: list[SearchHit]
) -> list[NoteRef]:
    """Map LLM-mentioned titles onto real notes — drop hallucinations."""
    by_title = {hit.title.lower(): hit for hit in hits}
    resolved: list[NoteRef] = []
    seen: set[str] = set()
    for title in source_titles:
        hit = by_title.get(title.strip().lower())
        if hit is not None and hit.title not in seen:
            seen.add(hit.title)
            resolved.append(NoteRef(title=hit.title, vault_path=hit.vault_path))
    return resolved


async def answer_question(
    question: str,
    db: AsyncSession,
    *,
    limit: int = DEFAULT_CONTEXT_LIMIT,
    semantic: bool = True,
) -> AnswerResult:
    """Answer ``question`` from the most relevant vault notes.

    ``semantic`` uses embedding search when enabled; otherwise (or on miss)
    falls back to keyword search. With no hits, return an honest "nothing
    found" answer without an LLM call.
    """
    q = question.strip()
    if not q:
        return AnswerResult(answer=NO_CONTEXT_ANSWER, sources=[], confidence=0.0)

    hits = await retrieve_vault_notes(db, q, limit, semantic=semantic)
    if not hits:
        return AnswerResult(answer=NO_CONTEXT_ANSWER, sources=[], confidence=0.0)

    raw = await get_llm_provider().answer(q, _format_context(hits))

    return AnswerResult(
        answer=raw.answer.strip(),
        sources=_resolve_sources(raw.sources, hits),
        confidence=_clamp_confidence(raw.confidence),
    )


def format_answer_for_chat(result: AnswerResult) -> str:
    """Render ``AnswerResult`` for chat surfaces (Telegram) with ``[[Links]]``."""
    text = result.answer
    if result.sources:
        links = ", ".join(f"[[{source.title}]]" for source in result.sources)
        text = f"{text}\n\nQuellen: {links}"
    return text
