from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import verify_api_key
from app.api.v1.schemas import (
    AskRequest,
    CaptureRequest,
    CaptureResponse,
    ClassifyRequest,
    DigestRequest,
    EntryListResponse,
    EntrySummary,
    NoteContentResponse,
    NoteSearchHit,
    NoteSearchResponse,
)
from app.db.session import get_db
from app.llm.provider import get_llm_provider
from app.llm.schemas import AnswerResult, ClassificationResult, DigestResult
from app.models.entry import Entry
from app.services.answer import answer_question
from app.services.digest import build_digest
from app.services.process_message import process_text_message
from app.vault.index import parse_note_file, retrieve_vault_notes
from app.vault.paths import resolve_vault_file
from app.webhooks.outbound import emit_capture_event

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
    dependencies=[Depends(verify_api_key)],
)


def _resolve_vault_file(vault_relative_path: str) -> Path:
    """Sicherer Pfad unterhalb des Vault-Roots — kein Path-Traversal."""
    try:
        return resolve_vault_file(vault_relative_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid vault path") from exc


def _entry_to_summary(row: Entry) -> EntrySummary:
    return EntrySummary(
        id=row.id,
        title=row.title,
        category=row.category,
        summary=row.summary,
        vault_path=row.vault_path,
        status=row.status,
        kind=row.kind,
        created_at=row.created_at,
    )


@router.post("/capture", response_model=CaptureResponse)
async def capture_text(body: CaptureRequest, db: AsyncSession = Depends(get_db)):
    """Text erfassen, klassifizieren und wie Telegram in Vault + DB speichern."""
    result = await process_text_message(body.text, db, kind="text")
    if result is None:
        raise HTTPException(status_code=409, detail="Duplicate capture rejected")
    await emit_capture_event(result, kind="text")
    return CaptureResponse(
        classification=result.classification,
        entry_id=result.entry_id,
        vault_path=result.vault_path,
        status=result.status,
    )


@router.post("/classify", response_model=ClassificationResult)
async def classify_text(body: ClassifyRequest):
    """Nur LLM-Klassifikation — ohne Vault oder DB."""
    llm = get_llm_provider()
    return await llm.classify(body.text)


@router.get("/entries", response_model=EntryListResponse)
async def list_entries(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Letzte Entries aus der DB (neueste zuerst)."""
    stmt = (
        select(Entry)
        .order_by(Entry.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        _entry_to_summary(row)
        for row in rows
    ]
    return EntryListResponse(items=items, limit=limit, offset=offset)


@router.get("/entries/{entry_id}", response_model=EntrySummary)
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Einzelnen Entry aus der DB (fuer MCP ``get_note`` per ID)."""
    row = await db.get(Entry, entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _entry_to_summary(row)


@router.get("/notes/content", response_model=NoteContentResponse)
async def get_note_content(
    vault_path: str = Query(min_length=1, max_length=500),
):
    """Vault-Datei lesen (read-only) — fuer MCP ``get_note`` per Pfad."""
    filepath = _resolve_vault_file(vault_path)
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="Note not found")
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read note") from exc
    title: str | None = None
    if filepath.suffix.lower() in {".md", ".markdown"}:
        try:
            title = parse_note_file(filepath).title
        except OSError:
            pass
    return NoteContentResponse(vault_path=vault_path, content=content, title=title)


@router.get("/notes/search", response_model=NoteSearchResponse)
async def search_notes(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=10, ge=1, le=50),
    semantic: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Vault-Suche: Keyword (Default) oder semantisch mit ``semantic=true``."""
    hits = await retrieve_vault_notes(db, q, limit=limit, semantic=semantic)
    items = [
        NoteSearchHit(
            title=hit.title,
            vault_path=hit.vault_path,
            snippet=hit.snippet,
            category=hit.category,
            folder=hit.folder,
        )
        for hit in hits
    ]
    return NoteSearchResponse(query=q, items=items, limit=limit, semantic=semantic)


@router.post("/ask", response_model=AnswerResult)
async def ask_brain(body: AskRequest, db: AsyncSession = Depends(get_db)):
    """RAG-Antwort auf Basis des Vaults (E17-3) — gleiche Pipeline wie ``/ask``."""
    return await answer_question(body.question, db)


@router.post("/digest", response_model=DigestResult)
async def digest_topic(body: DigestRequest, db: AsyncSession = Depends(get_db)):
    """Themen-Digest: Synthese verwandter Notizen (E17-8)."""
    return await build_digest(
        body.topic,
        db,
        days=body.days,
        limit=body.limit,
    )
