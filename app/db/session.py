import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


@asynccontextmanager
async def worker_session():
    """Fresh engine per Celery task — avoids async event loop conflicts."""
    task_engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(
        task_engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        async with session_factory() as session:
            yield session
    finally:
        await task_engine.dispose()