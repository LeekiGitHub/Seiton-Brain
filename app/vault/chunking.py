"""Text-Chunking fuer Retrieval (E18-4).

Teilt langen Dokumenttext in ueberlappende Abschnitte, damit Keyword- und
semantische Suche ueber die ersten 2000 Zeichen hinaus greifen.
"""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> list[str]:
    """Zerlegt ``text`` in Abschnitte der Laenge ``chunk_size`` mit Overlap.

    Leerer/Whitespace-only Text → ``[]``. ``chunk_size`` muss > ``overlap`` sein;
    ungueltige Parameter fallen auf sichere Defaults zurueck.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    size = chunk_size if chunk_size > 0 else 1500
    ov = overlap if overlap >= 0 else 0
    if ov >= size:
        ov = max(0, size // 5)

    if len(cleaned) <= size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    n = len(cleaned)
    while start < n:
        end = min(start + size, n)
        # Bevorzuge Abschnitte an Whitespace-Grenzen (kein Wortmitten-Schnitt),
        # solange wir noch nicht am Textende sind.
        if end < n:
            window = cleaned[start:end]
            split_at = max(window.rfind("\n"), window.rfind(" "))
            if split_at > size // 3:
                end = start + split_at
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        start = max(end - ov, start + 1)
    return chunks
