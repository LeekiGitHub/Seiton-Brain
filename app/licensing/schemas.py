"""Pydantic-Schemas fuer Lizenzschlüssel (E21-1)."""

from datetime import date

from pydantic import BaseModel, Field


class LicensePayload(BaseModel):
    """Signierter Inhalt eines Lizenzschlüssels."""

    edition: str = Field(description="z. B. consumer, pro")
    licensee: str = Field(description="Käufer-Identifikator (E-Mail o. ä.)")
    issued: date
    expires: date | None = None
    features: list[str] = Field(default_factory=list)


class LicenseInfo(BaseModel):
    """Ergebnis der Offline-Pruefung."""

    valid: bool
    edition: str | None = None
    licensee: str | None = None
    issued: date | None = None
    expires: date | None = None
    features: list[str] = Field(default_factory=list)
    message: str = ""
