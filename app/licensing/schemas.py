"""Pydantic schemas for license keys (E21-1)."""

from datetime import date

from pydantic import BaseModel, Field


class LicensePayload(BaseModel):
    """Signed payload of a license key."""

    edition: str = Field(description="e.g. consumer, pro")
    licensee: str = Field(description="Buyer identifier (email etc.)")
    issued: date
    expires: date | None = None
    features: list[str] = Field(default_factory=list)


class LicenseInfo(BaseModel):
    """Result of offline verification."""

    valid: bool
    edition: str | None = None
    licensee: str | None = None
    issued: date | None = None
    expires: date | None = None
    features: list[str] = Field(default_factory=list)
    message: str = ""
