"""Web-UI Router (E19): Setup-Wizard und statische Assets."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.setup.security import require_localhost
from app.setup.status import is_setup_complete

UI_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(UI_DIR / "templates"))

router = APIRouter(tags=["ui"])


def _localhost_dep(request: Request) -> None:
    require_localhost(request)


@router.get("/", response_class=HTMLResponse)
async def home():
    if not is_setup_complete():
        return RedirectResponse(url="/setup", status_code=302)
    return RedirectResponse(url="/setup", status_code=302)


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
        },
    )


def mount_ui_static(app) -> None:
    static_dir = UI_DIR / "static"
    if static_dir.is_dir():
        app.mount("/ui/static", StaticFiles(directory=str(static_dir)), name="ui-static")
