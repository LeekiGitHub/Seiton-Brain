import io
import logging
import re

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ISO-639-1: two lowercase letters (region like "en-US" → we take "en").
_LANGUAGE_RE = re.compile(r"^([a-z]{2})(?:-[a-zA-Z]{2,})?$")


def normalize_whisper_language(value: str | None) -> str | None:
    """Return a valid ISO-639-1 code or None (auto-detect)."""
    if value is None:
        return None
    stripped = value.strip().lower()
    if not stripped:
        return None
    match = _LANGUAGE_RE.match(stripped)
    if not match:
        logger.warning(
            "Ungültiger WHISPER_LANGUAGE=%r — ignoriere, Auto-Detect aktiv",
            value,
        )
        return None
    return match.group(1)


def _normalize_provider(value: str | None) -> str:
    raw = (value or "openai").strip().lower().replace("_", ".")
    if raw in {"whisper.cpp", "whispercpp", "local", "cpp"}:
        return "whisper.cpp"
    return "openai"


async def transcribe_openai(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """OpenAI Whisper API (``whisper-1``)."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    kwargs: dict = {
        "model": "whisper-1",
        "file": audio_file,
    }
    language = normalize_whisper_language(settings.whisper_language)
    if language:
        kwargs["language"] = language
        logger.debug("Whisper language hint: %s", language)

    transcript = await client.audio.transcriptions.create(**kwargs)
    return transcript.text.strip()


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    """Transcription depending on ``WHISPER_PROVIDER`` (openai | whisper.cpp).

    With ``whisper.cpp``: soft probe; on errors/missing install optionally
    Fallback auf OpenAI (``WHISPER_CPP_FALLBACK_OPENAI``, Default true).
    """
    provider = _normalize_provider(settings.whisper_provider)
    if provider == "whisper.cpp":
        from app.transcription.whisper_cpp import (
            is_whisper_cpp_available,
            transcribe_whisper_cpp,
        )

        if is_whisper_cpp_available():
            try:
                return await transcribe_whisper_cpp(audio_bytes, filename=filename)
            except Exception as exc:  # noqa: BLE001
                if not settings.whisper_cpp_fallback_openai:
                    raise
                logger.warning(
                    "whisper.cpp fehlgeschlagen (%s) — Fallback auf OpenAI",
                    exc,
                )
        else:
            if not settings.whisper_cpp_fallback_openai:
                raise RuntimeError(
                    "WHISPER_PROVIDER=whisper.cpp, aber Binary/Modell fehlen "
                    "(siehe docs/whisper-cpp.md)"
                )
            logger.warning(
                "whisper.cpp nicht verfuegbar — Fallback auf OpenAI Whisper"
            )

    return await transcribe_openai(audio_bytes, filename=filename)
