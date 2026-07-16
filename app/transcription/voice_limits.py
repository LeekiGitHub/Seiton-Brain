"""Voice-Dateigroessen-Pruefung (E6-1)."""

from __future__ import annotations

from app.config import settings


class VoiceTooLargeError(Exception):
    """Sprachnachricht ueberschreitet das konfigurierte Byte-Limit."""

    def __init__(self, size_bytes: int, max_bytes: int) -> None:
        self.size_bytes = size_bytes
        self.max_bytes = max_bytes
        super().__init__(f"Voice file {size_bytes} bytes exceeds limit {max_bytes}")


def voice_size_limit() -> int:
    return settings.telegram_voice_max_bytes


def format_voice_too_large_message(max_bytes: int | None = None) -> str:
    limit = max_bytes if max_bytes is not None else voice_size_limit()
    mb = max(1, limit // (1024 * 1024))
    return (
        f"Die Sprachnachricht ist zu groß (max. {mb} MB). "
        "Bitte kürzer aufnehmen oder als Text senden."
    )


def assert_voice_within_limit(size_bytes: int) -> None:
    limit = voice_size_limit()
    if size_bytes > limit:
        raise VoiceTooLargeError(size_bytes, limit)
