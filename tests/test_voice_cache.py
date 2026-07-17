"""Tests fuer Voice-Cache (E6-2)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.transcription import voice_cache
from app.worker.tasks import _process_voice


def test_voice_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    file_id = "AgACAgIAAxkBAAId"
    assert voice_cache.load_voice_cache(file_id) is None

    voice_cache.save_voice_cache(file_id, b"ogg-bytes")
    assert voice_cache.load_voice_cache(file_id) == b"ogg-bytes"

    voice_cache.delete_voice_cache(file_id)
    assert voice_cache.load_voice_cache(file_id) is None


def test_voice_cache_safe_filename_independent_of_path_chars(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    file_id = "weird/../file:id"
    path = voice_cache.save_voice_cache(file_id, b"x")
    assert path.parent == tmp_path
    assert ".." not in path.name
    assert path.suffix == ".ogg"


@pytest.mark.asyncio
@patch("app.worker.tasks._process_text", new_callable=AsyncMock)
@patch("app.worker.tasks.transcribe_audio", new_callable=AsyncMock, return_value="hallo")
@patch("app.worker.tasks.download_file", new_callable=AsyncMock, return_value=b"audio")
async def test_process_voice_uses_cache_on_retry(
    mock_download, mock_transcribe, mock_process, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    file_id = "voice-retry-1"

    await _process_voice(file_id, 42)
    mock_download.assert_awaited_once()
    mock_process.assert_awaited_once()
    # Nach Erfolg geloescht
    assert voice_cache.load_voice_cache(file_id) is None

    mock_download.reset_mock()
    mock_process.reset_mock()
    # Simuliere Crash vor delete: Datei manuell wieder anlegen
    voice_cache.save_voice_cache(file_id, b"audio")
    await _process_voice(file_id, 42)
    mock_download.assert_not_awaited()
    mock_process.assert_awaited_once()
    assert voice_cache.load_voice_cache(file_id) is None


@pytest.mark.asyncio
@patch("app.worker.tasks.send_message", new_callable=AsyncMock)
@patch("app.worker.tasks.transcribe_audio", new_callable=AsyncMock)
@patch("app.worker.tasks.download_file", new_callable=AsyncMock)
async def test_process_voice_does_not_cache_oversized(
    mock_download, mock_transcribe, mock_send, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    monkeypatch.setattr(settings, "telegram_voice_max_bytes", 100)
    mock_download.return_value = b"x" * 200

    await _process_voice("big", 42)

    assert list(tmp_path.glob("*.ogg")) == []
    mock_transcribe.assert_not_called()
