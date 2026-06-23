from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Vektor-Dimension fuer Embeddings (E17-2). Passt zu OpenAI
# ``text-embedding-3-small`` (1536 Dim) — dem Default in den Settings. Wird die
# Spalte/Migration geaendert, muss ``embedding_model`` ein Modell mit gleicher
# Dimension liefern, sonst schlagen Inserts fehl.
EMBEDDING_DIM = 1536


class VaultNoteIndex(Base):
    """DB-Spiegel von Vault-Dateien (E5-1, multi-format ab E18-1).

    Wird beim Schreiben/Append/Delete aktualisiert und fuer Keyword-Suche
    (E17-1) genutzt — statt bei jedem LLM-Aufruf ``rglob`` ueber den Vault.
    ``doc_type`` unterscheidet die Quelle (markdown, text, pdf, …).
    ``embedding`` haelt den pgvector-Vektor fuer semantische Suche (E17-2);
    ``None`` solange Embeddings deaktiviert sind oder die Berechnung scheiterte.
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
