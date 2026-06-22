"""Tests fuer den Long-Polling-Modus (E1-5)."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.telegram import client as tg_client
from app.telegram import polling


@pytest.mark.asyncio
@patch("app.telegram.polling.process_update", new_callable=AsyncMock)
@patch("app.telegram.polling.get_updates", new_callable=AsyncMock)
@patch("app.telegram.polling.delete_webhook", new_callable=AsyncMock)
async def test_run_polling_processes_updates(mock_delete, mock_get, mock_process):
    mock_get.return_value = [
        {"update_id": 10, "message": {"text": "a", "chat": {"id": 1}}},
        {"update_id": 11, "message": {"text": "b", "chat": {"id": 1}}},
    ]

    await polling.run_polling(poll_timeout=1, max_batches=1)

    mock_delete.assert_awaited_once()
    assert mock_process.await_count == 2


@pytest.mark.asyncio
@patch("app.telegram.polling.process_update", new_callable=AsyncMock)
@patch("app.telegram.polling.get_updates", new_callable=AsyncMock)
@patch("app.telegram.polling.delete_webhook", new_callable=AsyncMock)
async def test_run_polling_advances_offset(mock_delete, mock_get, mock_process):
    """Nach einer Runde muss der naechste getUpdates mit offset = max+1 kommen."""
    mock_get.side_effect = [
        [{"update_id": 41, "message": {"text": "a", "chat": {"id": 1}}}],
        [],
    ]

    await polling.run_polling(poll_timeout=1, max_batches=2)

    first_call, second_call = mock_get.await_args_list
    assert first_call.args[0] is None  # erster Aufruf ohne offset
    assert second_call.args[0] == 42


@pytest.mark.asyncio
@patch("app.telegram.polling.asyncio.sleep", new_callable=AsyncMock)
@patch("app.telegram.polling.process_update", new_callable=AsyncMock)
@patch("app.telegram.polling.get_updates", new_callable=AsyncMock)
@patch("app.telegram.polling.delete_webhook", new_callable=AsyncMock)
async def test_run_polling_survives_http_error(
    mock_delete, mock_get, mock_process, mock_sleep
):
    """Ein getUpdates-Fehler darf den Loop nicht beenden — Backoff + weiter."""
    mock_get.side_effect = [
        httpx.ConnectError("boom"),
        [{"update_id": 1, "message": {"text": "a", "chat": {"id": 1}}}],
    ]

    await polling.run_polling(poll_timeout=1, max_batches=2)

    mock_sleep.assert_awaited_once()
    mock_process.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.telegram.polling.process_update", new_callable=AsyncMock)
@patch("app.telegram.polling.get_updates", new_callable=AsyncMock)
@patch("app.telegram.polling.delete_webhook", new_callable=AsyncMock)
async def test_run_polling_keeps_going_on_poison_update(
    mock_delete, mock_get, mock_process
):
    """Wirft process_update, ruecken wir den offset trotzdem vor."""
    mock_process.side_effect = RuntimeError("poison")
    mock_get.side_effect = [
        [{"update_id": 7, "message": {"text": "x", "chat": {"id": 1}}}],
        [],
    ]

    await polling.run_polling(poll_timeout=1, max_batches=2)

    _, second_call = mock_get.await_args_list
    assert second_call.args[0] == 8


# ─── client.get_updates / delete_webhook ──────────────────────────────────


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    """Minimaler httpx.AsyncClient-Ersatz, der Aufrufe aufzeichnet."""

    last_get: tuple | None = None
    last_post: tuple | None = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url, params=None, timeout=None):
        _FakeAsyncClient.last_get = (url, params, timeout)
        return _FakeResponse({"ok": True, "result": [{"update_id": 1}]})

    async def post(self, url, json=None, timeout=None):
        _FakeAsyncClient.last_post = (url, json, timeout)
        return _FakeResponse({"ok": True})


@pytest.mark.asyncio
async def test_get_updates_builds_params_and_returns_result(monkeypatch):
    monkeypatch.setattr(tg_client.httpx, "AsyncClient", _FakeAsyncClient)

    result = await tg_client.get_updates(offset=99, timeout=25)

    url, params, timeout = _FakeAsyncClient.last_get
    assert url.endswith("/getUpdates")
    assert params == {"timeout": 25, "offset": 99}
    assert timeout == 35  # timeout + 10 Puffer
    assert result == [{"update_id": 1}]


@pytest.mark.asyncio
async def test_get_updates_omits_offset_when_none(monkeypatch):
    monkeypatch.setattr(tg_client.httpx, "AsyncClient", _FakeAsyncClient)

    await tg_client.get_updates(offset=None, timeout=10)

    _, params, _ = _FakeAsyncClient.last_get
    assert "offset" not in params


@pytest.mark.asyncio
async def test_delete_webhook_posts(monkeypatch):
    monkeypatch.setattr(tg_client.httpx, "AsyncClient", _FakeAsyncClient)

    await tg_client.delete_webhook()

    url, payload, _ = _FakeAsyncClient.last_post
    assert url.endswith("/deleteWebhook")
    assert payload == {"drop_pending_updates": False}
