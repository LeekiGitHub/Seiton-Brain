"""Tests fuer Voice-Dateigroessen-Limit (E6-1)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.transcription.voice_limits import (
    VoiceTooLargeError,
    assert_voice_within_limit,
    format_voice_too_large_message,
)
from app.worker.tasks import _process_voice


def test_format_voice_too_large_message():
    msg = format_voice_too_large_message(10_485_760)
    assert "10 MB" in msg
    assert "Text senden" in msg


def test_assert_voice_within_limit_ok():
    assert_voice_within_limit(1024)


def test_assert_voice_within_limit_raises(monkeypatch):
    monkeypatch.setattr(settings, "telegram_voice_max_bytes", 100)
    with pytest.raises(VoiceTooLargeError) as exc_info:
        assert_voice_within_limit(101)
    assert exc_info.value.size_bytes == 101
    assert exc_info.value.max_bytes == 100


@pytest.mark.asyncio
@patch("app.worker.tasks.send_message", new_callable=AsyncMock)
@patch("app.worker.tasks.transcribe_audio", new_callable=AsyncMock)
@patch("app.worker.tasks.download_file", new_callable=AsyncMock)
async def test_process_voice_rejects_oversized_file(
    mock_download, mock_transcribe, mock_send, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    mock_download.return_value = b"x" * 200
    with patch.object(settings, "telegram_voice_max_bytes", 100):
        await _process_voice("file123", 42)

    mock_transcribe.assert_not_called()
    mock_send.assert_awaited_once()
    assert "zu groß" in mock_send.await_args.args[1]


@pytest.mark.asyncio
@patch("app.worker.tasks._process_text", new_callable=AsyncMock)
@patch("app.worker.tasks.transcribe_audio", new_callable=AsyncMock, return_value="hallo")
@patch("app.worker.tasks.download_file", new_callable=AsyncMock, return_value=b"small")
async def test_process_voice_accepts_small_file(
    mock_download, mock_transcribe, mock_process, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "telegram_voice_cache_dir", str(tmp_path))
    await _process_voice("file123", 42)
    mock_process.assert_awaited_once()
    assert list(tmp_path.glob("*.ogg")) == []
