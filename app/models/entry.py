from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Erlaubte Werte fuer `kind` und `status`.
# Wir benutzen VARCHAR statt Enum, damit Werte ohne Migration ergaenzt werden
# koennen; die Listen hier sind die Quelle der Wahrheit fuer Code-Reviews.
KIND_VALUES = {"text", "voice"}
STATUS_VALUES = {"processed", "appended", "failed", "rejected"}


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    vault_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    telegram_chat_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    telegram_message_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )
    telegram_update_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, unique=True
    )

    kind: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="text"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="processed"
    )
    # Classify-Prompt-Version (E4-4), z. B. "v1" — fuer Audit/Replays.
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
