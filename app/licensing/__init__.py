"""Offline-Lizenzierung (E21-1) — Ed25519-signierte Lizenzschlüssel."""

from app.licensing.schemas import LicenseInfo
from app.licensing.validate import verify_license_key

__all__ = ["LicenseInfo", "verify_license_key"]
