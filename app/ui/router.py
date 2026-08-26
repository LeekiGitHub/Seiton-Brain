"""Web-UI Router (E19): Setup-Wizard, Dashboard und statische Assets."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    AskRequest,
    DigestRequest,
    NoteContentResponse,
    NoteSearchHit,
    NoteSearchResponse,
)
from app.config import settings
from app.db.session import get_db
from app.llm.schemas import AnswerResult, DigestResult
from app.services.answer import answer_question
from app.services.backup import (
    backups_dir,
    create_backup_sync,
    list_backup_details,
    restore_commands,
)
from app.services.digest import build_digest
from app.services.process_message import process_text_message
from app.webhooks.outbound import emit_capture_event
from app.setup.security import require_localhost
from app.setup.status import is_setup_complete
from app.ui.auth import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    clear_failed_attempts,
    create_session_token,
    lockout_remaining,
    register_failed_attempt,
    ui_auth_enabled,
    verify_password,
    verify_session_token,
)
from app.ui.notes import (
    list_notes,
    load_vault_config,
    read_note_content,
    remove_note,
    update_note_content,
)
from app.ui.schemas import (
    BackupCreateResponse,
    BackupListItem,
    BackupListResponse,
    ReindexResponse,
    DashboardResponse,
    LicenseSaveRequest,
    LicenseStatusResponse,
    LoginRequest,
    LoginResponse,
    NoteDeleteResponse,
    NoteListResponse,
    NoteSaveRequest,
    NoteSaveResponse,
    SettingsSaveRequest,
    SettingsViewResponse,
    UiCaptureRequest,
    UiCaptureResponse,
    VaultConfigResponse,
)
from app.setup.schemas import SetupSaveResponse, SetupTestRequest, SetupTestResponse
from app.ui.service import load_dashboard
from app.ui.license import license_status, save_license
from app.ui.settings import load_settings_view, save_settings
from app.vault.index import retrieve_vault_notes, sync_vault_index

logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(UI_DIR / "templates"))
templates.env.globals["ui_auth_enabled"] = ui_auth_enabled

router = APIRouter(tags=["ui"])
ui_api_router = APIRouter(prefix="/api/ui", tags=["ui-api"])


def _localhost_dep(request: Request) -> None:
    require_localhost(request)


def _has_session(request: Request) -> bool:
    return verify_session_token(request.cookies.get(SESSION_COOKIE, ""))


def _ui_page_dep(request: Request) -> None:
    """Guard für HTML-Seiten (E23-1): Login-Redirect statt 403/401."""
    if not ui_auth_enabled():
        require_localhost(request)
        return
    if not _has_session(request):
        raise HTTPException(
            status_code=303,
            detail="Login erforderlich",
            headers={"Location": "/login"},
        )


def _ui_api_dep(request: Request) -> None:
    """Guard für /api/ui/* (E23-1): 401 ohne gültige Session."""
    if not ui_auth_enabled():
        require_localhost(request)
        return
    if not _has_session(request):
        raise HTTPException(status_code=401, detail="Login erforderlich")


@router.get("/manifest.webmanifest", include_in_schema=False)
async def pwa_manifest() -> FileResponse:
    """PWA-Manifest (E23-2) — korrekter MIME-Type, kein Guard (keine Daten)."""
    return FileResponse(
        UI_DIR / "static" / "manifest.webmanifest",
        media_type="application/manifest+json",
    )


@router.get("/sw.js", include_in_schema=False)
async def service_worker() -> FileResponse:
    """Service Worker (E23-2) — muss auf Root liegen fuer Scope ``/``."""
    return FileResponse(
        UI_DIR / "static" / "sw.js",
        media_type="text/javascript",
    )


@router.get("/", response_class=HTMLResponse)
async def home():
    if not is_setup_complete():
        return RedirectResponse(url="/setup", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if not ui_auth_enabled() or _has_session(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"active": "login"})


@router.get("/logout")
async def logout_get():
    """Legacy-GET: leitet auf Login um; Cookie wird nur per POST gelöscht (E27-3)."""
    return RedirectResponse(url="/login", status_code=302)


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        samesite="lax",
        secure=settings.ui_cookie_secure,
    )
    return response


@ui_api_router.post("/login", response_model=LoginResponse)
async def login_api(body: LoginRequest, request: Request) -> Response:
    """Login mit UI-Passwort → Session-Cookie (E23-1)."""
    if not ui_auth_enabled():
        raise HTTPException(status_code=404, detail="UI-Auth ist nicht aktiviert")
    host = request.client.host if request.client else "unknown"
    retry_in = lockout_remaining(host)
    if retry_in:
        raise HTTPException(
            status_code=429,
            detail=f"Zu viele Fehlversuche — bitte in {retry_in}s erneut versuchen.",
        )
    if not verify_password(body.password):
        register_failed_attempt(host)
        logger.warning("UI login failed for host=%s", host)
        raise HTTPException(status_code=401, detail="Falsches Passwort")
    clear_failed_attempts(host)
    response = JSONResponse(LoginResponse(ok=True).model_dump())
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.ui_cookie_secure,
    )
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    _: None = Depends(_ui_page_dep),
):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"active": "dashboard"},
    )


@router.get("/ask", response_class=HTMLResponse)
async def ask_page(
    request: Request,
    _: None = Depends(_ui_page_dep),
):
    return templates.TemplateResponse(
        request,
        "ask.html",
        {
            "active": "ask",
            "embeddings_enabled": settings.embeddings_enabled,
        },
    )


@router.get("/notes", response_class=HTMLResponse)
async def notes_page(
    request: Request,
    _: None = Depends(_ui_page_dep),
):
    return templates.TemplateResponse(
        request,
        "notes.html",
        {"active": "notes"},
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    _: None = Depends(_ui_page_dep),
):
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"active": "settings"},
    )


@router.get("/setup", response_class=HTMLResponse)
async def setup_wizard(
    request: Request,
    # Setup schreibt Secrets in die .env — bleibt bewusst localhost-only.
    _: None = Depends(_localhost_dep),
):
    return templates.TemplateResponse(
        request,
        "setup.html",
        {
            "title": "Seiton Brain — Setup",
            "complete": is_setup_complete(),
            "active": "setup",
        },
    )


@ui_api_router.get("/dashboard", response_model=DashboardResponse)
async def dashboard_api(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> DashboardResponse:
    return await load_dashboard(db)


@ui_api_router.post("/capture", response_model=UiCaptureResponse)
async def capture_api(
    body: UiCaptureRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> UiCaptureResponse:
    """Notiz aus der Web-UI erfassen — gleiche Pipeline wie Telegram/REST (E22-1)."""
    result = await process_text_message(body.text, db, kind="text")
    if result is None:
        raise HTTPException(status_code=409, detail="Duplicate capture rejected")
    await emit_capture_event(result, kind="text")
    return UiCaptureResponse(
        entry_id=result.entry_id,
        title=result.classification.title,
        category=result.classification.category,
        action=result.classification.action,
        vault_path=result.vault_path,
        status=result.status,
        tags=result.classification.tags,
    )


@ui_api_router.get("/search", response_model=NoteSearchResponse)
async def search_api(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=10, ge=1, le=50),
    semantic: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> NoteSearchResponse:
    use_semantic = settings.embeddings_enabled if semantic is None else semantic
    hits = await retrieve_vault_notes(db, q, limit=limit, semantic=use_semantic)
    items = [
        NoteSearchHit(
            title=hit.title,
            vault_path=hit.vault_path,
            snippet=hit.snippet,
            category=hit.category,
            folder=hit.folder,
        )
        for hit in hits
    ]
    return NoteSearchResponse(
        query=q, items=items, limit=limit, semantic=use_semantic
    )


@ui_api_router.post("/ask", response_model=AnswerResult)
async def ask_api(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> AnswerResult:
    return await answer_question(body.question, db)


@ui_api_router.post("/digest", response_model=DigestResult)
async def digest_api(
    body: DigestRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> DigestResult:
    """Themen-Digest in der UI — gleiche Pipeline wie Telegram/REST (E22-3)."""
    return await build_digest(body.topic, db, days=body.days, limit=body.limit)


@ui_api_router.get("/notes", response_model=NoteListResponse)
async def notes_list_api(
    q: str | None = Query(default=None, max_length=200),
    folder: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> NoteListResponse:
    return await list_notes(
        db, q=q, folder=folder, category=category, limit=limit, offset=offset
    )


@ui_api_router.get("/notes/content", response_model=NoteContentResponse)
async def notes_content_api(
    vault_path: str = Query(min_length=1, max_length=500),
    _: None = Depends(_ui_api_dep),
) -> NoteContentResponse:
    try:
        return read_note_content(vault_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid vault path") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Note not found") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read note") from exc


@ui_api_router.put("/notes/content", response_model=NoteSaveResponse)
async def notes_save_api(
    body: NoteSaveRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> NoteSaveResponse:
    try:
        return await update_note_content(db, body.vault_path, body.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid vault path") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Note not found") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not save note") from exc


@ui_api_router.delete("/notes", response_model=NoteDeleteResponse)
async def notes_delete_api(
    vault_path: str = Query(min_length=1, max_length=500),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> NoteDeleteResponse:
    try:
        return await remove_note(db, vault_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid vault path") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not delete note") from exc


@ui_api_router.post("/backup", response_model=BackupCreateResponse)
async def backup_create_api(
    _: None = Depends(_ui_api_dep),
) -> BackupCreateResponse:
    """One-Click-Backup: Postgres-Dump + Vault-Archiv (E25-1)."""
    try:
        outcome = await asyncio.to_thread(create_backup_sync)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return BackupCreateResponse(
        name=outcome.name,
        directory=outcome.directory,
        files=outcome.files,
        warnings=outcome.warnings,
    )


@ui_api_router.post("/reindex", response_model=ReindexResponse)
async def reindex_api(
    full: bool = Query(True, description="True = Full-Sync, False = inkrementell"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_ui_api_dep),
) -> ReindexResponse:
    """Vault neu indexieren (E28-1). Default: Full-Sync (Reparatur)."""
    result = await sync_vault_index(db, incremental=not full)
    mode_label = "Vollständig" if result.mode == "full" else "Inkrementell"
    return ReindexResponse(
        mode=result.mode,
        indexed=result.indexed,
        skipped=result.skipped,
        removed=result.removed,
        message=(
            f"{mode_label}: {result.indexed} indexiert, "
            f"{result.skipped} unverändert, {result.removed} entfernt."
        ),
    )


@ui_api_router.get("/backups", response_model=BackupListResponse)
async def backup_list_api(
    _: None = Depends(_ui_api_dep),
) -> BackupListResponse:
    items = [
        BackupListItem(
            name=entry.name,
            created_at=entry.created_at,
            files=entry.files,
            restore=restore_commands(entry.name),
        )
        for entry in list_backup_details()
    ]
    return BackupListResponse(directory=str(backups_dir()), items=items)


@ui_api_router.get("/vault-config", response_model=VaultConfigResponse)
async def vault_config_api(
    _: None = Depends(_ui_api_dep),
) -> VaultConfigResponse:
    return load_vault_config()


@ui_api_router.get("/settings", response_model=SettingsViewResponse)
async def settings_api(
    _: None = Depends(_ui_api_dep),
) -> SettingsViewResponse:
    return load_settings_view()


@ui_api_router.post("/settings", response_model=SetupSaveResponse)
async def settings_save_api(
    body: SettingsSaveRequest,
    _: None = Depends(_ui_api_dep),
) -> SetupSaveResponse:
    try:
        return save_settings(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@ui_api_router.post("/settings/test", response_model=SetupTestResponse)
async def settings_test_api(
    body: SetupTestRequest,
    _: None = Depends(_ui_api_dep),
) -> SetupTestResponse:
    from app.setup.routes import setup_test

    return await setup_test(body)


@ui_api_router.get("/license", response_model=LicenseStatusResponse)
async def license_api(
    _: None = Depends(_ui_api_dep),
) -> LicenseStatusResponse:
    return license_status()


@ui_api_router.post("/license", response_model=SetupSaveResponse)
async def license_save_api(
    body: LicenseSaveRequest,
    _: None = Depends(_ui_api_dep),
) -> SetupSaveResponse:
    try:
        return save_license(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def mount_ui_static(app) -> None:
    static_dir = UI_DIR / "static"
    if static_dir.is_dir():
        app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="ui-static")
