import io
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return transcript.text.strip()
