from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entry import Entry

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/entries")
async def create_entry(db: AsyncSession = Depends(get_db)):
    entry = Entry(
        title="Test Notiz",
        category="note",
        summary="Mein erster DB-Eintrag",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"id": entry.id, "title": entry.title}


@app.get("/entries")
async def list_entries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Entry).order_by(Entry.created_at.desc()))
    entries = result.scalars().all()
    return [
        {"id": e.id, "title": e.title, "category": e.category, "summary": e.summary}
        for e in entries
    ]