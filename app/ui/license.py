"""Lizenz-UI und Speichern (E21-1)."""

from __future__ import annotations

from app.config import settings
from app.licensing.startup import check_current_license
from app.licensing.validate import verify_license_key
from app.setup.config_save import _save_response
from app.setup.env_file import resolve_env_path, update_env_file
from app.ui.schemas import LicenseSaveRequest, LicenseStatusResponse
from app.ui.settings import mask_secret


def license_status() -> LicenseStatusResponse:
    info = check_current_license()
    key = settings.seiton_license_key.strip()
    return LicenseStatusResponse(
        required=settings.seiton_license_required,
        valid=info.valid if key else False,
        edition=info.edition,
        licensee=info.licensee,
        issued=info.issued,
        expires=info.expires,
        features=info.features,
        message=info.message if key else "Keine Lizenz hinterlegt",
        key_masked=mask_secret(key) if key else "",
    )


def save_license(body: LicenseSaveRequest):
    info = verify_license_key(body.license_key)
    if not info.valid:
        raise ValueError(info.message)
    env_path = update_env_file(
        {"SEITON_LICENSE_KEY": body.license_key.strip()},
        resolve_env_path(settings.seiton_env_file),
    )
    return _save_response(env_path)
