from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.auth import verify_api_key
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    CaptureRequest,
    CaptureResponse,
    ClassifyRequest,
    EntryListResponse,
    EntrySummary,
)
from app.db.session import get_db
from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult
from app.models.entry import Entry
from app.services.process_message import process_text_message

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/capture", response_model=CaptureResponse)
async def capture_text(body: CaptureRequest, db: AsyncSession = Depends(get_db)):
    """Text erfassen, klassifizieren und wie Telegram in Vault + DB speichern."""
    result = await process_text_message(body.text, db, kind="text")
    if result is None:
        raise HTTPException(status_code=409, detail="Duplicate capture rejected")
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
        EntrySummary(
            id=row.id,
            title=row.title,
            category=row.category,
            summary=row.summary,
            vault_path=row.vault_path,
            status=row.status,
            kind=row.kind,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return EntryListResponse(items=items, limit=limit, offset=offset)
