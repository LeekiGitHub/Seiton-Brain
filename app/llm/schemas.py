from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["create", "append"]


class ClassificationResult(BaseModel):
    category: str = Field(
        description="One of: school, work, private, idea, travel, note"
    )
    title: str = Field(description="Short descriptive title for the note")
    summary: str = Field(description="Structured summary of the input")
    related: list[str] = Field(
        default_factory=list,
        description="Titles of existing vault notes to link to",
    )
    tags: list[str] = Field(
        default_factory=list,
        description=(
            "0-5 short lowercase tags describing the note "
            "(topic keywords, no spaces, no '#' prefix)"
        ),
    )
    action: Action = Field(
        default="create",
        description=(
            "create = new note (default). append = add an update section to an "
            "existing note (target_title required and must match an existing note)."
        ),
    )
    target_title: str | None = Field(
        default=None,
        description=(
            "When action='append': exact title of the existing note to extend. "
            "Must be one of the existing notes; otherwise the request falls back "
            "to action='create' in the sanitizer."
        ),
    )


class LLMAnswer(BaseModel):
    """Rohe RAG-Antwort des LLM (E17-3), bevor Quellen aufgeloest werden.

    ``sources`` sind **Titel** aus dem mitgelieferten Kontext — der Service
    mappt sie auf echte Notizen (``NoteRef``) und verwirft Halluzinationen.
    """

    answer: str = Field(description="Answer based strictly on the provided notes")
    sources: list[str] = Field(
        default_factory=list,
        description="Titles of context notes actually used (subset of context)",
    )
    confidence: float = Field(
        default=0.0,
        description="0.0-1.0 how well the notes support the answer",
    )


class NoteRef(BaseModel):
    """Aufgeloeste Quelle: Titel plus (falls bekannt) Vault-Pfad fuer Links."""

    title: str
    vault_path: str | None = None


class AnswerResult(BaseModel):
    """Finales RAG-Ergebnis (E17-3) fuer Konsumenten (Telegram, REST, MCP)."""

    answer: str
    sources: list[NoteRef] = Field(default_factory=list)
    confidence: float = 0.0


class LLMDigest(BaseModel):
    """Rohe Digest-Synthese des LLM (E17-8), bevor Quellen aufgeloest werden."""

    digest: str = Field(description="Synthesized overview of the provided notes")
    sources: list[str] = Field(
        default_factory=list,
        description="Titles of context notes actually used (subset of context)",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="Short takeaway bullets",
    )


class DigestResult(BaseModel):
    """Finales Digest-Ergebnis (E17-8) fuer Telegram, REST, n8n."""

    topic: str
    digest: str
    sources: list[NoteRef] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    note_count: int = 0
    days: int | None = None
