from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Vector dimension for embeddings (E17-2). Matches OpenAI
# ``text-embedding-3-small`` (1536 dims) — the default in settings. If the
# column/migration changes, ``embedding_model`` must use a model with the same
# dimension, otherwise inserts fail.
EMBEDDING_DIM = 1536


class VaultNoteIndex(Base):
    """DB mirror of vault files (E5-1, multi-format from E18-1).

    Updated on write/append/delete and used for keyword search
    (E17-1) — instead of ``rglob`` over the vault on every LLM call.
    ``doc_type`` distinguishes the source (markdown, text, pdf, …).
    ``embedding`` (note-level) remains for compatibility; new embeddings
    live in ``vault_chunk`` (E18-4).
    """

    __tablename__ = "vault_note_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    vault_path: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(50), default="", server_default="")
    folder: Mapped[str] = mapped_column(String(100), default="", server_default="")
    doc_type: Mapped[str] = mapped_column(
        String(30), default="markdown", server_default="markdown", index=True
    )
    body_snippet: Mapped[str] = mapped_column(Text, default="", server_default="")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )
    mtime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chunks: Mapped[list["VaultChunk"]] = relationship(  # noqa: F821
        "VaultChunk",
        back_populates="note",
        cascade="all, delete-orphan",
        order_by="VaultChunk.chunk_index",
    )
