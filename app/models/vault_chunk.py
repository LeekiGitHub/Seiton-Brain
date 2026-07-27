"""Vault-Chunks fuer Retrieval (E18-4)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.vault_note_index import EMBEDDING_DIM

if TYPE_CHECKING:
    from app.models.vault_note_index import VaultNoteIndex


class VaultChunk(Base):
    """Ein retrieval-tauglicher Textabschnitt einer indexierten Vault-Datei.

    Parent bleibt ``VaultNoteIndex`` (Metadaten, UI-Liste). Embeddings und
    Keyword-Treffer auf langen Dokumenten laufen ueber diese Tabelle.
    """

    __tablename__ = "vault_chunk"
    __table_args__ = (
        UniqueConstraint("note_id", "chunk_index", name="uq_vault_chunk_note_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("vault_note_index.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, default="", server_default="")
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )

    note: Mapped[VaultNoteIndex] = relationship(
        "VaultNoteIndex",
        back_populates="chunks",
    )
