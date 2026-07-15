import io
import logging
import re

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# ISO-639-1: zwei Kleinbuchstaben (ggf. mit Region wie "en-US" → wir nehmen "en").
_LANGUAGE_RE = re.compile(r"^([a-z]{2})(?:-[a-zA-Z]{2,})?$")


def normalize_whisper_language(value: str | None) -> str | None:
    """Liefert einen gültigen ISO-639-1-Code oder None (Auto-Detect)."""
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


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
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
