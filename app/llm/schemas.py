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
