"""Text chunking for retrieval (E18-4).

Splits long document text into overlapping sections so keyword and
semantic search work beyond the first 2000 characters.
"""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1500,
    overlap: int = 200,
) -> list[str]:
    """Split ``text`` into sections of length ``chunk_size`` with overlap.

    Empty/whitespace-only text → ``[]``. ``chunk_size`` must be > ``overlap``;
    invalid parameters fall back to safe defaults.
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
        # Prefer breaks at whitespace (no mid-word cuts) while we are
        # not yet at the end of the text.
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
