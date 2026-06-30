from typing import Literal

from pydantic import BaseModel, Field


class SetupStatusResponse(BaseModel):
    complete: bool
    missing: list[str]
    components: dict[str, bool]
    env_file: str
    telegram_optional: bool = True
    restart_required_after_save: bool = True


class SetupCheckResult(BaseModel):
    ok: bool
    message: str


class SetupTestRequest(BaseModel):
    check: Literal["vault", "openai", "telegram", "database", "redis", "all"]
    obsidian_vault_host_path: str | None = None
    openai_api_key: str | None = None
    telegram_bot_token: str | None = None


class SetupTestResponse(BaseModel):
    results: dict[str, SetupCheckResult]


class SetupSaveRequest(BaseModel):
    obsidian_vault_host_path: str = Field(min_length=1, max_length=500)
    openai_api_key: str = Field(min_length=1, max_length=500)
    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_allowed_user_ids: str = ""
    seiton_api_key: str = ""
    embeddings_enabled: bool = False


class SetupSaveResponse(BaseModel):
    saved: bool
    env_file: str
    restart_required: bool = True
    message: str
