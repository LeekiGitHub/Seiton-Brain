"""Settings-Ansicht und Speichern fuer die Web-UI (E19-5)."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.setup.env_file import read_env_values, resolve_env_path
from app.setup.status import component_status, is_placeholder, is_setup_complete
from app.licensing.startup import check_current_license
from app.vault.categories import get_category_folders
from app.ui.schemas import BackupInfo, EditionInfo, SettingsSaveRequest, SettingsViewResponse

EDITION_INFO = EditionInfo(
    name="Seiton Brain (Open Source)",
    license="MIT",
    description=(
        "Öffentliche Entwicklung / Portfolio-Edition. Geplante kommerzielle "
        "Consumer-Edition bei verkaufsfertigem Produkt (ADR 0004/0005)."
    ),
)


def resolve_edition_info() -> EditionInfo:
    info = check_current_license()
    key = settings.seiton_license_key.strip()
    if key and info.valid:
        label = (info.edition or "consumer").replace("_", " ").title()
        features = ", ".join(info.features) if info.features else "—"
        return EditionInfo(
            name=f"Seiton Brain ({label})",
            license="Kommerzielle Lizenz",
            description=f"Lizenziert für {info.licensee}. Enthalten: {features}.",
        )
    return EDITION_INFO


def mask_secret(value: str) -> str:
    stripped = value.strip()
    if not stripped or is_placeholder(stripped):
        return ""
    if len(stripped) <= 4:
        return "••••"
    return f"{'•' * 8}{stripped[-4:]}"


def _backups_dir() -> Path:
    env_parent = resolve_env_path(settings.seiton_env_file).parent
    return env_parent / "backups"


def list_recent_backups(limit: int = 5) -> list[str]:
    backups_dir = _backups_dir()
    if not backups_dir.is_dir():
        return []
    names = sorted(
        (p.name for p in backups_dir.iterdir() if p.is_dir()),
        reverse=True,
    )
    return names[:limit]


def load_settings_view() -> SettingsViewResponse:
    file_values = read_env_values(settings.seiton_env_file)
    vault_host = file_values.get(
        "OBSIDIAN_VAULT_HOST_PATH", settings.obsidian_vault_path
    )
    return SettingsViewResponse(
        complete=is_setup_complete(),
        components=component_status(),
        env_file=str(resolve_env_path(settings.seiton_env_file)),
        vault_host_path=vault_host,
        vault_container_path=settings.obsidian_vault_path,
        llm_provider=settings.llm_provider,
        openai_model=file_values.get("OPENAI_MODEL", settings.openai_model),
        embeddings_enabled=settings.embeddings_enabled,
        embedding_model=settings.embedding_model,
        openai_key_masked=mask_secret(settings.openai_api_key),
        seiton_api_key_masked=mask_secret(settings.seiton_api_key),
        telegram_configured=component_status()["telegram"],
        telegram_allowed_user_ids=settings.telegram_allowed_user_ids,
        seiton_webhook_url=file_values.get(
            "SEITON_WEBHOOK_URL", settings.seiton_webhook_url
        ),
        categories=dict(get_category_folders()),
        edition=resolve_edition_info(),
        backup=BackupInfo(
            command="./scripts/backup.sh",
            directory=str(_backups_dir()),
            recent=list_recent_backups(),
        ),
    )


def save_settings(body: SettingsSaveRequest):
    from app.setup.config_save import save_settings_config

    return save_settings_config(
        obsidian_vault_host_path=body.obsidian_vault_host_path,
        openai_api_key=body.openai_api_key,
        embeddings_enabled=body.embeddings_enabled,
        openai_model=body.openai_model,
        telegram_bot_token=body.telegram_bot_token,
        telegram_webhook_secret=body.telegram_webhook_secret,
        telegram_allowed_user_ids=body.telegram_allowed_user_ids,
        seiton_api_key=body.seiton_api_key,
        seiton_webhook_url=body.seiton_webhook_url,
    )
