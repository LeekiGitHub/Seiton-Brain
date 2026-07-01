"""Web-UI Router (E19): Setup-Wizard, Dashboard und statische Assets."""

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import AskRequest, NoteSearchHit, NoteSearchResponse
from app.config import settings
from app.db.session import get_db
from app.llm.schemas import AnswerResult
from app.services.answer import answer_question
from app.setup.security import require_localhost
from app.setup.status import is_setup_complete
from app.ui.schemas import DashboardResponse
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


def mount_ui_static(app) -> None:
    static_dir = UI_DIR / "static"
    if static_dir.is_dir():
        app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="ui-static")
