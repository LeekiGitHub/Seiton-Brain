"""Web-UI Router (E19): Setup-Wizard, Dashboard und statische Assets."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import AskRequest, NoteContentResponse, NoteSearchHit, NoteSearchResponse
from app.config import settings
from app.db.session import get_db
from app.llm.schemas import AnswerResult
from app.services.answer import answer_question
from app.setup.security import require_localhost
from app.setup.status import is_setup_complete
from app.ui.notes import (
    list_notes,
    load_vault_config,
    read_note_content,
    remove_note,
    update_note_content,
)
from app.ui.schemas import (
    DashboardResponse,
    NoteDeleteResponse,
    NoteListResponse,
    NoteSaveRequest,
    NoteSaveResponse,
    VaultConfigResponse,
)
from app.ui.service import load_dashboard
from app.vault.index import retrieve_vault_notes

UI_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(UI_DIR / "templates"))

router = APIRouter(tags=["ui"])
ui_api_router = APIRouter(prefix="/api/ui", tags=["ui-api"])


def _localhost_dep(request: Request) -> None:
    require_localhost(request)


@router.get("/", response_class=HTMLResponse)
async def home():
    if not is_setup_complete():
        return RedirectResponse(url="/setup", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    _: None = Depends(_localhost_dep),
):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"active": "dashboard"},
    )


@router.get("/ask", response_class=HTMLResponse)
async def ask_page(
    request: Request,
    _: None = Depends(_localhost_dep),
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
    _: None = Depends(_localhost_dep),
):
    return templates.TemplateResponse(
        request,
        "notes.html",
        {"active": "notes"},
    )


@router.get("/setup", response_class=HTMLResponse)
async def setup_wizard(
    request: Request,
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
    _: None = Depends(_localhost_dep),
) -> DashboardResponse:
    return await load_dashboard(db)


@ui_api_router.get("/search", response_model=NoteSearchResponse)
async def search_api(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=10, ge=1, le=50),
    semantic: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_localhost_dep),
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
    _: None = Depends(_localhost_dep),
) -> AnswerResult:
    return await answer_question(body.question, db)


@ui_api_router.get("/notes", response_model=NoteListResponse)
async def notes_list_api(
    q: str | None = Query(default=None, max_length=200),
    folder: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_localhost_dep),
) -> NoteListResponse:
    return await list_notes(
        db, q=q, folder=folder, category=category, limit=limit, offset=offset
    )


@ui_api_router.get("/notes/content", response_model=NoteContentResponse)
async def notes_content_api(
    vault_path: str = Query(min_length=1, max_length=500),
    _: None = Depends(_localhost_dep),
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
    _: None = Depends(_localhost_dep),
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
    _: None = Depends(_localhost_dep),
) -> NoteDeleteResponse:
    try:
        return await remove_note(db, vault_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid vault path") from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not delete note") from exc


@ui_api_router.get("/vault-config", response_model=VaultConfigResponse)
async def vault_config_api(
    _: None = Depends(_localhost_dep),
) -> VaultConfigResponse:
    return load_vault_config()


def mount_ui_static(app) -> None:
    static_dir = UI_DIR / "static"
    if static_dir.is_dir():
        app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="ui-static")
