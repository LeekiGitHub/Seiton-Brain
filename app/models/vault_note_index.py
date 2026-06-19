from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class VaultNoteIndex(Base):
    """DB-Spiegel von Vault-Markdown-Dateien (E5-1).

    Wird beim Schreiben/Append/Delete aktualisiert und fuer Keyword-Suche
    (E17-1) genutzt — statt bei jedem LLM-Aufruf ``rglob`` ueber den Vault.
    """

    __tablename__ = "vault_note_index"

    id: Mapped[int] = mapped_column(primary_key=True)
    vault_path: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(50), default="", server_default="")
    folder: Mapped[str] = mapped_column(String(100), default="", server_default="")
    body_snippet: Mapped[str] = mapped_column(Text, default="", server_default="")
    mtime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
