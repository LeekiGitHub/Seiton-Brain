from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.main.run_health_checks", new_callable=AsyncMock)
def test_health_returns_ok_when_all_checks_pass(mock_checks):
    mock_checks.return_value = {"database": "ok", "redis": "ok"}

    response = client.get("/health", headers={"X-Request-ID": "req-health-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-health-1"
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok"},
    }


@patch("app.main.run_health_checks", new_callable=AsyncMock)
def test_health_returns_503_when_database_fails(mock_checks):
    mock_checks.return_value = {"database": "error", "redis": "ok"}

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"
    assert response.json()["checks"]["database"] == "error"


@patch("app.main.run_health_checks", new_callable=AsyncMock)
def test_health_returns_503_when_redis_fails(mock_checks):
    mock_checks.return_value = {"database": "ok", "redis": "error"}

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "error"


@patch("app.health.engine")
async def test_check_database_ok(mock_engine):
    from app.health import check_database

    conn = AsyncMock()
    mock_engine.connect.return_value.__aenter__.return_value = conn

    assert await check_database() == "ok"
    conn.execute.assert_awaited_once()


@patch("app.health.engine")
async def test_check_database_error_on_exception(mock_engine):
    from app.health import check_database

    mock_engine.connect.side_effect = OSError("connection refused")

    assert await check_database() == "error"


@patch("app.health.Redis")
async def test_check_redis_ok(mock_redis_cls):
    from app.health import check_redis

    client = AsyncMock()
    client.ping.return_value = True
    mock_redis_cls.from_url.return_value = client

    assert await check_redis() == "ok"
    client.aclose.assert_awaited_once()


@patch("app.health.Redis")
async def test_check_redis_error_on_exception(mock_redis_cls):
    from app.health import check_redis

    client = AsyncMock()
    client.ping.side_effect = ConnectionError("redis down")
    mock_redis_cls.from_url.return_value = client

    assert await check_redis() == "error"
    client.aclose.assert_awaited_once()
