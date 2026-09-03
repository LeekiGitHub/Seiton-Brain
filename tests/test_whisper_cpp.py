"""Tests for local Whisper via whisper.cpp (E6-4)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.transcription import whisper_cpp as cpp
from app.transcription.whisper import _normalize_provider, transcribe_audio


@pytest.fixture(autouse=True)
def _clear_cpp_cache():
    cpp.clear_whisper_cpp_availability_cache()
    yield
    cpp.clear_whisper_cpp_availability_cache()


def test_normalize_provider():
    assert _normalize_provider("openai") == "openai"
    assert _normalize_provider("whisper.cpp") == "whisper.cpp"
    assert _normalize_provider("whisper_cpp") == "whisper.cpp"
    assert _normalize_provider("LOCAL") == "whisper.cpp"


def test_parse_whisper_stdout_strips_timestamps():
    raw = "[00:00:00.000 --> 00:00:01.000]  Hallo Welt\nwhisper_print_timings\n"
    assert cpp._parse_whisper_stdout(raw) == "Hallo Welt"


def test_is_whisper_cpp_available_false_without_model(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "whisper_cpp_binary", "whisper-cli")
    monkeypatch.setattr(settings, "whisper_cpp_model", str(tmp_path / "missing.bin"))
    cpp.clear_whisper_cpp_availability_cache()
    assert cpp.is_whisper_cpp_available() is False


def test_transcribe_whisper_cpp_sync(tmp_path: Path, monkeypatch):
    model = tmp_path / "ggml-base.bin"
    model.write_bytes(b"fake")
    binary = tmp_path / "whisper-cli"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    binary.chmod(0o755)

    monkeypatch.setattr(settings, "whisper_cpp_binary", str(binary))
    monkeypatch.setattr(settings, "whisper_cpp_model", str(model))
    monkeypatch.setattr(settings, "whisper_language", "de")
    monkeypatch.setattr(cpp, "_ffmpeg_available", lambda: False)

    completed = MagicMock(returncode=0, stdout="Lokaler Text\n", stderr="")
    with patch("app.transcription.whisper_cpp.subprocess.run", return_value=completed) as run:
        text = cpp.transcribe_whisper_cpp_sync(b"ogg-bytes", filename="voice.ogg")

    assert text == "Lokaler Text"
    cmd = run.call_args.args[0]
    assert str(binary) in cmd[0] or cmd[0].endswith("whisper-cli")
    assert "-m" in cmd
    assert "-l" in cmd
    assert "de" in cmd


@pytest.mark.asyncio
async def test_transcribe_audio_uses_whisper_cpp(monkeypatch):
    monkeypatch.setattr(settings, "whisper_provider", "whisper.cpp")
    monkeypatch.setattr(settings, "whisper_cpp_fallback_openai", False)
    monkeypatch.setattr(cpp, "is_whisper_cpp_available", lambda: True)

    with patch(
        "app.transcription.whisper_cpp.transcribe_whisper_cpp",
        new_callable=AsyncMock,
        return_value="cpp ok",
    ) as mock_cpp:
        text = await transcribe_audio(b"x")

    assert text == "cpp ok"
    mock_cpp.assert_awaited_once()


@pytest.mark.asyncio
async def test_transcribe_audio_fallback_to_openai(monkeypatch):
    monkeypatch.setattr(settings, "whisper_provider", "whisper.cpp")
    monkeypatch.setattr(settings, "whisper_cpp_fallback_openai", True)
    monkeypatch.setattr(cpp, "is_whisper_cpp_available", lambda: False)

    with patch(
        "app.transcription.whisper.transcribe_openai",
        new_callable=AsyncMock,
        return_value="openai ok",
    ) as mock_oa:
        text = await transcribe_audio(b"x")

    assert text == "openai ok"
    mock_oa.assert_awaited_once()


@pytest.mark.asyncio
async def test_transcribe_audio_raises_without_fallback(monkeypatch):
    monkeypatch.setattr(settings, "whisper_provider", "whisper.cpp")
    monkeypatch.setattr(settings, "whisper_cpp_fallback_openai", False)
    monkeypatch.setattr(cpp, "is_whisper_cpp_available", lambda: False)

    with pytest.raises(RuntimeError, match="whisper.cpp"):
        await transcribe_audio(b"x")
