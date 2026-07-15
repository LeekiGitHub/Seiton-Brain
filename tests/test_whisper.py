"""Tests fuer Whisper-Transkription (E6-3)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.transcription.whisper import normalize_whisper_language, transcribe_audio


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", None),
        ("   ", None),
        ("de", "de"),
        ("DE", "de"),
        ("en-US", "en"),
        ("invalid", None),
        ("deu", None),
        (None, None),
    ],
)
def test_normalize_whisper_language(raw, expected):
    assert normalize_whisper_language(raw) == expected


@pytest.mark.asyncio
async def test_transcribe_passes_language_hint(monkeypatch):
    monkeypatch.setattr(settings, "whisper_language", "de")
    mock_create = AsyncMock(return_value=MagicMock(text="  Hallo Welt  "))

    with patch("app.transcription.whisper.AsyncOpenAI") as mock_client_cls:
        mock_client_cls.return_value.audio.transcriptions.create = mock_create
        text = await transcribe_audio(b"fake-ogg")

    assert text == "Hallo Welt"
    kwargs = mock_create.await_args.kwargs
    assert kwargs["model"] == "whisper-1"
    assert kwargs["language"] == "de"


@pytest.mark.asyncio
async def test_transcribe_skips_language_when_empty(monkeypatch):
    monkeypatch.setattr(settings, "whisper_language", "")
    mock_create = AsyncMock(return_value=MagicMock(text="hello"))

    with patch("app.transcription.whisper.AsyncOpenAI") as mock_client_cls:
        mock_client_cls.return_value.audio.transcriptions.create = mock_create
        await transcribe_audio(b"fake-ogg")

    kwargs = mock_create.await_args.kwargs
    assert "language" not in kwargs


@pytest.mark.asyncio
async def test_transcribe_skips_invalid_language(monkeypatch):
    monkeypatch.setattr(settings, "whisper_language", "deutsch")
    mock_create = AsyncMock(return_value=MagicMock(text="ok"))

    with patch("app.transcription.whisper.AsyncOpenAI") as mock_client_cls:
        mock_client_cls.return_value.audio.transcriptions.create = mock_create
        await transcribe_audio(b"fake-ogg")

    assert "language" not in mock_create.await_args.kwargs
