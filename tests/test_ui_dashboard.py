"""Tests fuer Dashboard (E19-2)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.entry import Entry
from app.ui.schemas import DashboardResponse, DashboardStats
from app.ui.service import load_dashboard

client = TestClient(app)


def _entry(**kwargs) -> Entry:
    row = Entry(
        title="Test Note",
        category="idea",
        summary="Summary text",
        vault_path="Ideas/Test.md",
        kind="text",
        status="processed",
    )
    row.id = 1
    row.created_at = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


def test_dashboard_page_renders():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "dashboard.js" in response.text
    assert 'href="/setup"' in response.text


@patch("app.ui.router.load_dashboard", new_callable=AsyncMock)
def test_dashboard_api_returns_data(mock_load):
    mock_load.return_value = DashboardResponse(
        stats=DashboardStats(
            total_entries=3,
            entries_by_status={"processed": 2, "appended": 1, "failed": 0, "rejected": 0},
            entries_by_kind={"text": 3, "voice": 0},
            vault_notes_indexed=5,
            embeddings_enabled=False,
        ),
        recent_entries=[],
        recent_vault_notes=[],
    )
    response = client.get("/api/ui/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_entries"] == 3
    assert data["stats"]["vault_notes_indexed"] == 5


@pytest.mark.asyncio
async def test_load_dashboard_aggregates():
    db = AsyncMock()
    entry = _entry()

    count_results = [
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[entry])))),
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        MagicMock(scalar_one=MagicMock(return_value=0)),
        MagicMock(scalar_one=MagicMock(return_value=2)),
        MagicMock(all=MagicMock(return_value=[("processed", 2)])),
        MagicMock(all=MagicMock(return_value=[("text", 2)])),
    ]
    db.execute = AsyncMock(side_effect=count_results)

    result = await load_dashboard(db, entry_limit=5, vault_limit=5)

    assert result.stats.total_entries == 2
    assert len(result.recent_entries) == 1
    assert result.recent_entries[0].title == "Test Note"
