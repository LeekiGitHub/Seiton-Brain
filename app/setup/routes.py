"""Setup-API fuer den Web-Wizard (E19-1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.config import settings
from app.setup import checks, status
from app.setup.config_save import save_setup_config
from app.setup.env_file import resolve_env_path
from app.setup.schemas import (
    SetupCheckResult,
    SetupSaveRequest,
    SetupSaveResponse,
    SetupStatusResponse,
    SetupTestRequest,
    SetupTestResponse,
)
from app.setup.security import require_localhost

router = APIRouter(prefix="/api/setup", tags=["setup"])


def _localhost_dep(request: Request) -> None:
    require_localhost(request)


@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(_: None = Depends(_localhost_dep)) -> SetupStatusResponse:
    env_path = resolve_env_path(settings.seiton_env_file)
    return SetupStatusResponse(
        complete=status.is_setup_complete(),
        missing=status.missing_setup_fields(),
        components=status.component_status(),
        env_file=str(env_path),
    )


async def _run_check(name: str, body: SetupTestRequest) -> SetupCheckResult:
    if name == "vault":
        path = body.obsidian_vault_host_path or settings.obsidian_vault_path
        ok, message = await checks.check_vault_path(path)
        return SetupCheckResult(ok=ok, message=message)
    if name == "openai":
        key = body.openai_api_key or settings.openai_api_key
        ok, message = await checks.check_openai(key)
        return SetupCheckResult(ok=ok, message=message)
    if name == "telegram":
        token = body.telegram_bot_token or settings.telegram_bot_token
        ok, message = await checks.check_telegram(token)
        return SetupCheckResult(ok=ok, message=message)
    if name == "database":
        ok, message = await checks.check_database()
        return SetupCheckResult(ok=ok, message=message)
    if name == "redis":
        ok, message = await checks.check_redis()
        return SetupCheckResult(ok=ok, message=message)
    return SetupCheckResult(ok=False, message=f"Unbekannter Check: {name}")


@router.post("/test", response_model=SetupTestResponse)
async def setup_test(
    body: SetupTestRequest,
    _: None = Depends(_localhost_dep),
) -> SetupTestResponse:
    names = (
        ["vault", "openai", "telegram", "database", "redis"]
        if body.check == "all"
        else [body.check]
    )
    results: dict[str, SetupCheckResult] = {}
    for name in names:
        if name == "telegram" and not (
            body.telegram_bot_token or settings.telegram_bot_token
        ).strip():
            results[name] = SetupCheckResult(
                ok=True, message="Telegram übersprungen (optional)"
            )
            continue
        results[name] = await _run_check(name, body)
    return SetupTestResponse(results=results)


@router.post("/save", response_model=SetupSaveResponse)
async def setup_save(
    body: SetupSaveRequest,
    _: None = Depends(_localhost_dep),
) -> SetupSaveResponse:
    return save_setup_config(body)
