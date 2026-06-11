import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.routes import router as api_v1_router
from app.health import run_health_checks
from app.logging_config import bind_log_context, clear_log_context, configure_logging
from app.telegram.webhook import router as telegram_router

configure_logging()

app = FastAPI()
app.include_router(telegram_router)
app.include_router(api_v1_router)


@app.middleware("http")
async def logging_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    bind_log_context(request_id=request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        clear_log_context()


@app.get("/health")
async def health():
    checks = await run_health_checks()
    all_ok = all(status == "ok" for status in checks.values())
    body = {
        "status": "ok" if all_ok else "unhealthy",
        "checks": checks,
    }
    if all_ok:
        return body
    return JSONResponse(status_code=503, content=body)
