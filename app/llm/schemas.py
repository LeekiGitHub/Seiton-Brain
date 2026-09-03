from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["create", "append"]


class RouterResult(BaseModel):
    """LLM Router role (E7-3): create/append + note identity."""

    action: Action = Field(
        default="create",
        description="create = new note; append = extend existing note",
    )
    target_title: str | None = Field(
        default=None,
        description="Exact existing note title when action=append; else null",
    )
    category: str = Field(description="Vault category for the note")
    title: str = Field(description="Short title for the new content")


class WriterResult(BaseModel):
    """LLM Writer role (E7-3): summary and tags."""

    summary: str = Field(description="Structured summary of the input")
    tags: list[str] = Field(
        default_factory=list,
        description="0-5 short lowercase tags (no '#', no spaces)",
    )


class LinkerResult(BaseModel):
    """LLM Linker role (E7-3): related vault titles."""

    related: list[str] = Field(
        default_factory=list,
        description="0-3 titles of existing vault notes to link",
    )


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


class VisionImageResult(BaseModel):
    """Vision LLM result for photo-only content (E18-6)."""

    description: str = Field(description="Searchable description of the image")
    tags: list[str] = Field(
        default_factory=list,
        description="0-8 short lowercase tags (no '#', no spaces)",
    )


class LLMAnswer(BaseModel):
    """Raw RAG answer from the LLM (E17-3), before sources are resolved.

    ``sources`` are **titles** from the provided context — the service maps
    them onto real notes (``NoteRef``) and drops hallucinations.
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
    """Resolved source: title plus vault path for links when known."""

    title: str
    vault_path: str | None = None


class AnswerResult(BaseModel):
    """Final RAG result (E17-3) for consumers (Telegram, REST, MCP)."""

    answer: str
    sources: list[NoteRef] = Field(default_factory=list)
    confidence: float = 0.0


class LLMDigest(BaseModel):
    """Raw digest synthesis from the LLM (E17-8), before sources are resolved."""

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
    """Final digest result (E17-8) for Telegram, REST, n8n."""

    topic: str
    digest: str
    sources: list[NoteRef] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    note_count: int = 0
    days: int | None = None
