"""Startup license check (E21-1)."""

from __future__ import annotations

import sys

from app.config import settings
from app.licensing.validate import verify_license_key


def check_current_license():
    return verify_license_key(settings.seiton_license_key)


def enforce_license_if_required() -> None:
    """Exit the process when SEITON_LICENSE_REQUIRED=true and the license is invalid."""
    if not settings.seiton_license_required:
        return
    info = check_current_license()
    if info.valid:
        return
    print(
        f"Seiton Brain: Lizenz erforderlich — {info.message}\n"
        "Trage einen gültigen SEITON_LICENSE_KEY in .env ein "
        "(Einstellungen → Lizenz oder docs/licensing.md).",
        file=sys.stderr,
    )
    raise SystemExit(1)
