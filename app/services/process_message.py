from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import get_llm_provider
from app.llm.schemas import ClassificationResult
from app.models.entry import Entry
from app.vault.writer import write_note


async def process_text_message(text: str, db: AsyncSession) -> ClassificationResult:
    llm = get_llm_provider()
    result = await llm.classify(text)

    entry = Entry(
        title=result.title,
        category=result.category,
        summary=result.summary,
    )
    db.add(entry)
    await db.commit()

    write_note(result)
    return result
