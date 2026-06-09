from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.health import run_health_checks
from app.telegram.webhook import router as telegram_router

app = FastAPI()
app.include_router(telegram_router)


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
