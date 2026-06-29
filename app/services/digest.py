"""Themen-Digest-Service (E17-8).

Sammelt verwandte Vault-Notizen zu einem Thema (Ordner, Kategorie oder
Freitext) und erzeugt eine LLM-Synthese — Wochenrückblick, Themen-Brief.

Konsumenten: ``/digest`` (Telegram), ``POST /v1/digest`` (REST).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import DigestResult, NoteRef
from app.vault.index import SearchHit, collect_digest_notes

NO_NOTES_DIGEST = "Keine passenden Notizen im gewählten Zeitraum gefunden."


def _format_context(hits: list[SearchHit]) -> str:
    lines: list[str] = []
    for hit in hits:
        lines.append(f'- "{hit.title}" ({hit.folder}): {hit.snippet}')
    return "\n".join(lines)


def _resolve_sources(source_titles: list[str], hits: list[SearchHit]) -> list[NoteRef]:
    by_title = {hit.title.lower(): hit for hit in hits}
    resolved: list[NoteRef] = []
    seen: set[str] = set()
    for title in source_titles:
        hit = by_title.get(title.strip().lower())
        if hit is not None and hit.title not in seen:
            seen.add(hit.title)
            resolved.append(NoteRef(title=hit.title, vault_path=hit.vault_path))
    return resolved


async def build_digest(
    topic: str,
    db: AsyncSession,
    *,
    days: int | None = 7,
    limit: int = 15,
) -> DigestResult:
    """Erstellt einen Digest zu ``topic`` aus den passendsten Vault-Notizen."""
    t = topic.strip()
    if not t:
        return DigestResult(
            topic="",
            digest=NO_NOTES_DIGEST,
            sources=[],
            highlights=[],
            note_count=0,
            days=days,
        )

    hits = await collect_digest_notes(db, t, days=days, limit=limit)
    if not hits:
        return DigestResult(
            topic=t,
            digest=NO_NOTES_DIGEST,
            sources=[],
            highlights=[],
            note_count=0,
            days=days,
        )

    raw = await get_llm_provider().digest(t, _format_context(hits), days=days)

    return DigestResult(
        topic=t,
        digest=raw.digest.strip(),
        sources=_resolve_sources(raw.sources, hits),
        highlights=[h.strip() for h in raw.highlights if h.strip()],
        note_count=len(hits),
        days=days,
    )


def format_digest_for_chat(result: DigestResult) -> str:
    """Rendert ``DigestResult`` fuer Telegram mit ``[[Quellen]]``."""
    header = f"Digest: {result.topic}"
    if result.days:
        header += f" (letzte {result.days} Tage)"
    parts = [header, "", result.digest]
    if result.highlights:
        parts.extend(["", "Highlights:", *[f"• {h}" for h in result.highlights]])
    if result.sources:
        links = ", ".join(f"[[{s.title}]]" for s in result.sources)
        parts.extend(["", f"Quellen ({result.note_count}): {links}"])
    return "\n".join(parts)
