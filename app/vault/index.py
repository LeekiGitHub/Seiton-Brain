"""Vault-Index in Postgres (E5-1), Keyword-Suche (E17-1), Chunks (E18-4)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.session import SessionLocal
from app.llm.embeddings import get_embedding_provider
from app.models.vault_chunk import VaultChunk
from app.models.vault_note_index import VaultNoteIndex
from app.vault.chunking import chunk_text
from app.vault.extractors import get_extractor
from app.vault.reader import VaultNote, _body_snippet, _parse_frontmatter

logger = logging.getLogger(__name__)

# Fuer UI-/Listen-Preview; Retrieval laeuft ueber Chunks (E18-4).
BODY_INDEX_CHARS = 2000
# Snippet in SearchHit / RAG-Kontext — etwas laenger als frueher, weil Chunks
# den relevanten Abschnitt liefern.
HIT_SNIPPET_CHARS = 400
LLM_NOTE_LIMIT = 80
# Kandidaten-Pool vor Heuristik-Prefilter (E5-2); danach max. ~30 im Prompt.
LLM_CANDIDATE_POOL = 200
DEFAULT_DIGEST_DAYS = 7
DEFAULT_DIGEST_LIMIT = 15


@dataclass(frozen=True)
class SearchHit:
    title: str
    vault_path: str
    snippet: str
    category: str
    folder: str


def _vault_root() -> Path:
    return Path(settings.obsidian_vault_path)


def _relative_vault_path(path: Path) -> str:
    return str(path.relative_to(_vault_root()))


def _file_mtime(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)


def _index_body_snippet(content: str) -> str:
    return _body_snippet(content, limit=BODY_INDEX_CHARS)


def parse_note_file(path: Path) -> VaultNote:
    content = path.read_text(encoding="utf-8")
    meta = _parse_frontmatter(content)
    title = meta.get("title") or path.stem
    category = meta.get("category", "")
    folder = path.parent.name
    snippet = _body_snippet(content)
    return VaultNote(title=title, category=category, folder=folder, snippet=snippet)


def _file_to_index_payload(
    path: Path,
) -> tuple[VaultNoteIndex, str] | None:
    """Indexzeile + voller Extrakt-Text — ``None`` bei nicht unterstuetztem Typ."""
    extractor = get_extractor(path)
    if extractor is None:
        return None
    doc = extractor.extract(path)
    row = VaultNoteIndex(
        vault_path=_relative_vault_path(path),
        title=doc.title,
        category=doc.category,
        folder=path.parent.name,
        doc_type=doc.doc_type,
        body_snippet=_index_body_snippet(doc.text),
        mtime=_file_mtime(path),
    )
    return row, doc.text or ""


def _file_to_index_row(path: Path) -> VaultNoteIndex | None:
    """Kompatibilitaets-Helfer fuer bestehende Tests."""
    payload = _file_to_index_payload(path)
    return payload[0] if payload else None


def _ilike_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _embedding_text(title: str, body: str) -> str:
    """Eingabetext fuer das Embedding: Titel traegt am meisten Signal, dann Body."""
    return f"{title}\n\n{body}".strip()


async def _embed_text(title: str, body: str, *, label: str) -> list[float] | None:
    if not settings.embeddings_enabled:
        return None
    try:
        return await get_embedding_provider().embed(_embedding_text(title, body))
    except Exception as exc:  # noqa: BLE001 — Embedding ist optional, nie fatal
        logger.warning("Embedding failed for %s: %s", label, exc)
        return None


async def _replace_chunks(
    db: AsyncSession,
    note: VaultNoteIndex,
    full_text: str,
) -> tuple[int, bool]:
    """Ersetzt alle Chunks einer Notiz. Liefert (Anzahl, hatte_embedding)."""
    await db.execute(delete(VaultChunk).where(VaultChunk.note_id == note.id))
    pieces = chunk_text(
        full_text,
        chunk_size=settings.seiton_chunk_size,
        overlap=settings.seiton_chunk_overlap,
    )
    if not pieces and note.body_snippet.strip():
        pieces = [note.body_snippet]

    embedded_any = False
    for idx, piece in enumerate(pieces):
        embedding = await _embed_text(
            note.title, piece, label=f"{note.vault_path}#{idx}"
        )
        if embedding is not None:
            embedded_any = True
        db.add(
            VaultChunk(
                note_id=note.id,
                chunk_index=idx,
                content=piece,
                embedding=embedding,
            )
        )
    return len(pieces), embedded_any


async def upsert_vault_note_index(db: AsyncSession, vault_relative_path: str) -> None:
    """Indexiert eine Datei (relativ zum Vault-Root). Ignoriert fehlende Pfade."""
    filepath = _vault_root() / vault_relative_path
    if not filepath.is_file():
        await remove_vault_note_index(db, vault_relative_path)
        return

    payload = _file_to_index_payload(filepath)
    if payload is None:
        return  # nicht unterstuetzter Dateityp — nicht indexieren
    row, full_text = payload
    existing = (
        await db.execute(
            select(VaultNoteIndex).where(
                VaultNoteIndex.vault_path == vault_relative_path
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        db.add(row)
        await db.flush()
        indexed_row = row
    else:
        existing.title = row.title
        existing.category = row.category
        existing.folder = row.folder
        existing.doc_type = row.doc_type
        existing.body_snippet = row.body_snippet
        existing.mtime = row.mtime
        existing.indexed_at = datetime.now(UTC)
        indexed_row = existing

    _, embedded_any = await _replace_chunks(db, indexed_row, full_text)
    await db.commit()

    if embedded_any:
        from app.webhooks.outbound import emit_note_indexed_event

        await emit_note_indexed_event(
            vault_path=vault_relative_path,
            title=indexed_row.title,
            category=indexed_row.category,
            folder=indexed_row.folder,
            doc_type=indexed_row.doc_type,
        )


async def remove_vault_note_index(db: AsyncSession, vault_relative_path: str) -> None:
    await db.execute(
        delete(VaultNoteIndex).where(VaultNoteIndex.vault_path == vault_relative_path)
    )
    await db.commit()


async def sync_vault_index_from_disk(db: AsyncSession) -> int:
    """Voller Vault-Scan — Bootstrap oder Reparatur des Index."""
    vault_path = _vault_root()
    if not vault_path.exists():
        return 0

    found_paths: set[str] = set()
    count = 0
    for file in sorted(vault_path.rglob("*")):
        if not file.is_file():
            continue
        rel_parts = file.relative_to(vault_path).parts
        if any(part.startswith(".") for part in rel_parts):
            continue  # versteckte Dateien/Ordner (.obsidian, .trash, …)
        if get_extractor(file) is None:
            continue  # nicht unterstuetzter Dateityp
        try:
            rel = _relative_vault_path(file)
            payload = _file_to_index_payload(file)
            if payload is None:
                continue
            row, full_text = payload
            found_paths.add(rel)
            existing = (
                await db.execute(
                    select(VaultNoteIndex).where(VaultNoteIndex.vault_path == rel)
                )
            ).scalar_one_or_none()
            if existing is None:
                db.add(row)
                await db.flush()
                note = row
            else:
                existing.title = row.title
                existing.category = row.category
                existing.folder = row.folder
                existing.doc_type = row.doc_type
                existing.body_snippet = row.body_snippet
                existing.mtime = row.mtime
                note = existing
            await _replace_chunks(db, note, full_text)
            count += 1
        except OSError as exc:
            logger.warning("Skipping unreadable vault file %s: %s", file, exc)

    if found_paths:
        await db.execute(
            delete(VaultNoteIndex).where(
                VaultNoteIndex.vault_path.not_in(found_paths)
            )
        )
    else:
        await db.execute(delete(VaultNoteIndex))

    await db.commit()
    logger.info("Vault index sync complete: %d files", count)
    return count


async def ensure_vault_index(db: AsyncSession) -> None:
    total = (await db.execute(select(func.count()).select_from(VaultNoteIndex))).scalar_one()
    if total == 0 and _vault_root().exists():
        await sync_vault_index_from_disk(db)


async def list_indexed_notes(db: AsyncSession, limit: int = LLM_NOTE_LIMIT) -> list[VaultNote]:
    await ensure_vault_index(db)
    rows = (
        await db.execute(
            select(VaultNoteIndex)
            .order_by(VaultNoteIndex.mtime.desc(), VaultNoteIndex.title.asc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        VaultNote(
            title=row.title,
            category=row.category,
            folder=row.folder,
            snippet=row.body_snippet[:120],
        )
        for row in rows
    ]


async def list_existing_notes(limit: int = LLM_CANDIDATE_POOL) -> list[VaultNote]:
    """LLM-Kontext: liest aus dem Vault-Index (E5-1), nicht mehr ``rglob``.

    Liefert einen groesseren Kandidaten-Pool; ``prefilter_notes_for_llm`` (E5-2)
    reduziert spaeter auf die Prompt-Obergrenze.
    """
    async with SessionLocal() as db:
        return await list_indexed_notes(db, limit=limit)


def _hit_from_note(note: VaultNoteIndex, snippet_source: str) -> SearchHit:
    return SearchHit(
        title=note.title,
        vault_path=note.vault_path,
        snippet=_body_snippet(snippet_source, limit=HIT_SNIPPET_CHARS),
        category=note.category,
        folder=note.folder,
    )


async def search_vault_notes(
    db: AsyncSession, query: str, limit: int = 10
) -> list[SearchHit]:
    await ensure_vault_index(db)
    term = query.strip()
    if not term:
        return []

    pattern = _ilike_pattern(term)
    title_match = VaultNoteIndex.title.ilike(pattern)
    body_match = VaultNoteIndex.body_snippet.ilike(pattern)
    chunk_match = VaultChunk.content.ilike(pattern)

    # Titel-Treffer zuerst (ohne Chunk-Join), dann Body/Chunk.
    title_rows = (
        await db.execute(
            select(VaultNoteIndex)
            .where(title_match)
            .order_by(VaultNoteIndex.mtime.desc())
            .limit(limit)
        )
    ).scalars().all()

    hits: list[SearchHit] = [
        _hit_from_note(row, row.body_snippet) for row in title_rows
    ]
    seen = {h.vault_path for h in hits}
    if len(hits) >= limit:
        return hits[:limit]

    remaining = limit - len(hits)
    # Chunk-Treffer mit Parent laden; Fallback Body-Match ohne Chunk.
    chunk_rows = (
        await db.execute(
            select(VaultChunk, VaultNoteIndex)
            .join(VaultNoteIndex, VaultChunk.note_id == VaultNoteIndex.id)
            .where(or_(chunk_match, body_match))
            .order_by(
                case((chunk_match, 0), else_=1),
                VaultNoteIndex.mtime.desc(),
            )
            .limit(remaining * 3)
        )
    ).all()

    for chunk, note in chunk_rows:
        if note.vault_path in seen:
            continue
        snippet_src = chunk.content if chunk.content else note.body_snippet
        hits.append(_hit_from_note(note, snippet_src))
        seen.add(note.vault_path)
        if len(hits) >= limit:
            break

    return hits[:limit]


async def semantic_search_vault_notes(
    db: AsyncSession, query: str, limit: int = 10
) -> list[SearchHit]:
    """Semantische Suche via pgvector-kNN auf Chunks (E17-2 + E18-4).

    Liefert ``[]``, wenn Embeddings deaktiviert sind, die Query leer ist oder
    noch kein Chunk ein Embedding hat.
    """
    if not settings.embeddings_enabled:
        return []
    term = query.strip()
    if not term:
        return []

    await ensure_vault_index(db)
    try:
        query_embedding = await get_embedding_provider().embed(term)
    except Exception as exc:  # noqa: BLE001 — Suche soll nicht hart fehlschlagen
        logger.warning("Query embedding failed for %r: %s", term, exc)
        return []

    # Mehr Chunks holen, dann nach Dokument deduplizieren (bester Chunk gewinnt).
    stmt = (
        select(VaultChunk)
        .options(selectinload(VaultChunk.note))
        .where(VaultChunk.embedding.is_not(None))
        .order_by(VaultChunk.embedding.cosine_distance(query_embedding))
        .limit(max(limit * 4, limit))
    )
    chunks = (await db.execute(stmt)).scalars().all()
    hits: list[SearchHit] = []
    seen: set[str] = set()
    for chunk in chunks:
        note = chunk.note
        if note is None or note.vault_path in seen:
            continue
        hits.append(_hit_from_note(note, chunk.content))
        seen.add(note.vault_path)
        if len(hits) >= limit:
            break
    return hits


def _rows_to_search_hits(rows: list[VaultNoteIndex]) -> list[SearchHit]:
    return [
        SearchHit(
            title=row.title,
            vault_path=row.vault_path,
            snippet=_body_snippet(row.body_snippet, limit=HIT_SNIPPET_CHARS),
            category=row.category,
            folder=row.folder,
        )
        for row in rows
    ]


async def collect_digest_notes(
    db: AsyncSession,
    topic: str,
    *,
    days: int | None = DEFAULT_DIGEST_DAYS,
    limit: int = DEFAULT_DIGEST_LIMIT,
) -> list[SearchHit]:
    """Notizen fuer einen Themen-Digest sammeln (E17-8).

  Matcht Ordner, Kategorie, Titel/Body (ILIKE). Optional ``days`` filtert
  nach ``mtime``. Bei wenigen Treffern: semantische Ergaenzung (wenn aktiv).
    """
    await ensure_vault_index(db)
    term = topic.strip()
    if not term:
        return []

    term_lower = term.lower()
    pattern = _ilike_pattern(term)
    cutoff: datetime | None = None
    if days is not None and days > 0:
        cutoff = datetime.now(UTC) - timedelta(days=days)

    conditions = or_(
        func.lower(VaultNoteIndex.folder) == term_lower,
        func.lower(VaultNoteIndex.category) == term_lower,
        VaultNoteIndex.title.ilike(pattern),
        VaultNoteIndex.body_snippet.ilike(pattern),
        VaultNoteIndex.id.in_(
            select(VaultChunk.note_id).where(VaultChunk.content.ilike(pattern))
        ),
    )
    stmt = (
        select(VaultNoteIndex)
        .where(conditions)
        .order_by(VaultNoteIndex.mtime.desc())
        .limit(limit)
    )
    if cutoff is not None:
        stmt = stmt.where(VaultNoteIndex.mtime >= cutoff)

    rows = list((await db.execute(stmt)).scalars().all())
    seen = {row.vault_path for row in rows}

    if len(rows) < limit and settings.embeddings_enabled:
        semantic_hits = await semantic_search_vault_notes(db, term, limit)
        extra_paths = [h.vault_path for h in semantic_hits if h.vault_path not in seen]
        if extra_paths:
            extra_stmt = (
                select(VaultNoteIndex)
                .where(VaultNoteIndex.vault_path.in_(extra_paths))
                .order_by(VaultNoteIndex.mtime.desc())
            )
            if cutoff is not None:
                extra_stmt = extra_stmt.where(VaultNoteIndex.mtime >= cutoff)
            for row in (await db.execute(extra_stmt)).scalars().all():
                if row.vault_path not in seen:
                    rows.append(row)
                    seen.add(row.vault_path)
                    if len(rows) >= limit:
                        break

    rows.sort(key=lambda r: r.mtime, reverse=True)
    return _rows_to_search_hits(rows[:limit])


async def retrieve_vault_notes(
    db: AsyncSession,
    query: str,
    limit: int = 10,
    *,
    semantic: bool = False,
) -> list[SearchHit]:
    """Keyword- oder semantische Suche mit Fallback (E17-1/2/5).

    ``semantic=True``: versucht Embedding-kNN, wenn ``EMBEDDINGS_ENABLED``;
    bei 0 Treffern oder deaktivierten Embeddings Fallback auf Keyword.
    ``semantic=False``: nur Keyword (Default fuer ``/find`` und Legacy-API).
    """
    if semantic and settings.embeddings_enabled:
        hits = await semantic_search_vault_notes(db, query, limit)
        if hits:
            return hits
    return await search_vault_notes(db, query, limit)
