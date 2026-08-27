#!/usr/bin/env python3
"""CI-Smoke (E29-2): Insert + kNN-Query gegen echte pgvector-Spalte.

Voraussetzung: ``alembic upgrade head`` gegen ``DATABASE_URL`` (asyncpg).
Kein Import von ``app.config.settings`` — nur Modelle + Engine.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.vault_note_index import EMBEDDING_DIM, VaultNoteIndex


async def _run() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL fehlt", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(url)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    try:
        emb = [0.0] * EMBEDDING_DIM
        emb[0] = 1.0
        query = list(emb)

        async with session_factory() as session:
            session.add(
                VaultNoteIndex(
                    vault_path="ci/vector-smoke.md",
                    title="CI vector smoke",
                    category="",
                    folder="ci",
                    doc_type="markdown",
                    body_snippet="pgvector smoke",
                    embedding=emb,
                    mtime=datetime.now(UTC),
                )
            )
            await session.commit()

            result = await session.execute(
                select(VaultNoteIndex)
                .where(VaultNoteIndex.embedding.is_not(None))
                .order_by(VaultNoteIndex.embedding.cosine_distance(query))
                .limit(1)
            )
            row = result.scalar_one()
            if row.vault_path != "ci/vector-smoke.md":
                raise SystemExit(f"unerwarteter Treffer: {row.vault_path!r}")

        print(f"vector smoke ok (dim={EMBEDDING_DIM})")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_run())
