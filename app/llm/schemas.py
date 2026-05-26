from pydantic import BaseModel, Field


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
