"""Web-UI Router (E19): Setup-Wizard, Dashboard und statische Assets."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.setup.security import require_localhost
from app.setup.status import is_setup_complete
from app.ui.schemas import DashboardResponse
from app.ui.service import load_dashboard

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


def mount_ui_static(app) -> None:
    static_dir = UI_DIR / "static"
    if static_dir.is_dir():
        app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="ui-static")
