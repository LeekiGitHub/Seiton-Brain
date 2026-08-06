"""Lokaler Whisper via whisper.cpp (E6-4) — optional, Soft-Probe.

Braucht Host-Binary (z. B. ``whisper-cli``) und ein GGML-Modell unter
``models/`` (gitignored). Optional ``ffmpeg`` fuer OGG→WAV. Siehe
``docs/whisper-cpp.md``.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from app.config import settings
from app.transcription.whisper import normalize_whisper_language

logger = logging.getLogger(__name__)

# whisper.cpp CLI-Timeout (lange Sprachdateien / CPU).
_DEFAULT_TIMEOUT_SEC = 300


@lru_cache(maxsize=1)
def is_whisper_cpp_available() -> bool:
    """True, wenn Binary und Modell-Datei nutzbar erscheinen."""
    binary = (settings.whisper_cpp_binary or "").strip()
    model = Path(settings.whisper_cpp_model or "").expanduser()
    if not binary or not model.is_file():
        logger.debug(
            "whisper.cpp nicht verfuegbar (binary=%r model=%s)",
            binary,
            model,
        )
        return False
    if shutil.which(binary) is None and not Path(binary).expanduser().is_file():
        logger.debug("whisper.cpp Binary nicht gefunden: %s", binary)
        return False
    try:
        subprocess.run(
            [_resolve_binary(), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("whisper.cpp Probe fehlgeschlagen: %s", exc)
        return False


def clear_whisper_cpp_availability_cache() -> None:
    is_whisper_cpp_available.cache_clear()


def _resolve_binary() -> str:
    binary = settings.whisper_cpp_binary.strip()
    path = Path(binary).expanduser()
    if path.is_file():
        return str(path)
    found = shutil.which(binary)
    if found:
        return found
    return binary


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _ensure_wav(src: Path, wav: Path) -> Path:
    """Konvertiert nach WAV wenn noetig (Telegram: meist OGG/Opus)."""
    suffix = src.suffix.lower()
    if suffix in {".wav", ".wave"}:
        return src
    if not _ffmpeg_available():
        # Manche Builds akzeptieren OGG direkt — Versuch ohne Konvertierung.
        logger.warning(
            "ffmpeg fehlt — uebergebe %s direkt an whisper.cpp "
            "(bei Fehlern: brew/apt install ffmpeg)",
            src.name,
        )
        return src
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg-Konvertierung fehlgeschlagen: {result.stderr.strip()[:400]}"
        )
    return wav


def _parse_whisper_stdout(stdout: str) -> str:
    lines: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # Zeitstempel-Zeilen / Rauschen ausblenden
        # "[00:00:00.000 --> 00:00:01.000] text" → text
        if stripped.startswith("[") and "]" in stripped:
            after = stripped.split("]", 1)
            if len(after) == 2 and after[1].strip():
                lines.append(after[1].strip())
            continue
        if stripped.startswith("whisper_") or stripped.startswith("system_info"):
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def transcribe_whisper_cpp_sync(
    audio_bytes: bytes,
    *,
    filename: str = "voice.ogg",
    timeout: int = _DEFAULT_TIMEOUT_SEC,
) -> str:
    """Synchrone whisper.cpp-Transkription (fuer ``asyncio.to_thread``)."""
    if not audio_bytes:
        return ""

    binary = _resolve_binary()
    model = str(Path(settings.whisper_cpp_model).expanduser())
    language = normalize_whisper_language(settings.whisper_language)

    with tempfile.TemporaryDirectory(prefix="seiton-whisper-") as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / (filename or "voice.ogg")
        src.write_bytes(audio_bytes)
        wav = tmp_path / "audio.wav"
        media = _ensure_wav(src, wav)

        cmd = [
            binary,
            "-m",
            model,
            "-f",
            str(media),
            "-nt",  # no timestamps
            "-np",  # no prints / quieter
        ]
        if language:
            cmd.extend(["-l", language])

        logger.debug("whisper.cpp cmd: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()[:500]
            raise RuntimeError(f"whisper.cpp exit {result.returncode}: {err}")

        text = _parse_whisper_stdout(result.stdout or "")
        if not text and result.stderr:
            # Manche Builds schreiben nur nach stderr
            text = _parse_whisper_stdout(result.stderr)
        return text


async def transcribe_whisper_cpp(
    audio_bytes: bytes, filename: str = "voice.ogg"
) -> str:
    return await asyncio.to_thread(
        transcribe_whisper_cpp_sync, audio_bytes, filename=filename
    )
