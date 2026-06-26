"""RAG-Antwort-Service (E17-3).

Bindet Retrieval (E17-1 Keyword / E17-2 semantisch) und LLM-Generierung
zusammen: Frage -> relevante Vault-Notizen -> Answer-Prompt mit Kontext ->
``AnswerResult`` mit aufgeloesten Quellen.

Bewusst **kein** Telegram-/REST-Code hier — Konsumenten sind ``/ask``
(E17-4) und ``POST /v1/ask`` (E17-5). Dieser Service ist der gemeinsame Kern.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import AnswerResult, NoteRef
from app.vault.index import SearchHit, retrieve_vault_notes

logger = logging.getLogger(__name__)

DEFAULT_CONTEXT_LIMIT = 5

# Antwort, wenn der Vault nichts Passendes hergibt — bewusst ohne LLM-Call,
# spart Kosten und verhindert Halluzinationen ueber leeren Kontext.
NO_CONTEXT_ANSWER = "Dazu habe ich nichts in deinem Vault gefunden."


def _format_context(hits: list[SearchHit]) -> str:
    """Nummerierter Kontextblock fuer den Prompt — Titel exakt zum Kopieren."""
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
    """Mappt vom LLM genannte Titel auf echte Notizen — verwirft Halluzinationen."""
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
    """Beantwortet ``question`` auf Basis der relevantesten Vault-Notizen.

    ``semantic`` nutzt die Embedding-Suche, wenn aktiviert; faellt sonst (oder
    bei fehlenden Treffern) auf Keyword-Suche zurueck. Ohne Treffer wird ohne
    LLM-Call eine ehrliche "nichts gefunden"-Antwort geliefert.
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
    """Rendert ``AnswerResult`` fuer Chat-Surfaces (Telegram) mit ``[[Links]]``."""
    text = result.answer
    if result.sources:
        links = ", ".join(f"[[{source.title}]]" for source in result.sources)
        text = f"{text}\n\nQuellen: {links}"
    return text
