#!/usr/bin/env python3
"""Generate README visual assets (E11-4).

Produces:
  docs/assets/dashboard.png
  docs/assets/ask.png
  docs/assets/flow.gif

Uses Pillow (dev dependency of the generator only). Mock HTML under
``docs/assets/_mockups/`` mirrors the real Web-UI for manual re-capture later.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"

BG = (15, 20, 25)
SURFACE = (26, 35, 50)
SURFACE2 = (36, 48, 68)
BORDER = (45, 58, 77)
TEXT = (232, 238, 247)
MUTED = (139, 156, 179)
ACCENT = (91, 159, 212)
OK = (61, 154, 106)
OK_SOFT = (143, 212, 168)


def _font(size: int) -> ImageFont.ImageFont:
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _round(draw: ImageDraw.ImageDraw, xy, fill, radius=10, outline=BORDER):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=1)


def _nav(draw: ImageDraw.ImageDraw, w: int, active: str) -> None:
    brand = _font(18)
    link = _font(14)
    draw.line((40, 56, w - 40, 56), fill=BORDER, width=1)
    draw.text((40, 22), "Seiton Brain", fill=TEXT, font=brand)
    items = [
        ("Dashboard", "dashboard"),
        ("Suchen & Fragen", "ask"),
        ("Notizen", "notes"),
        ("Einstellungen", "settings"),
    ]
    x = w - 40
    # right-align nav links
    widths = []
    for label, _ in items:
        bbox = draw.textbbox((0, 0), label, font=link)
        widths.append(bbox[2] - bbox[0])
    gap = 22
    total = sum(widths) + gap * (len(items) - 1)
    x = w - 40 - total
    for (label, key), tw in zip(items, widths, strict=True):
        color = TEXT if key == active else MUTED
        draw.text((x, 26), label, fill=color, font=link)
        x += tw + gap


def dashboard_png() -> Image.Image:
    w, h = 1000, 720
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    title_f = _font(26)
    body_f = _font(15)
    small_f = _font(13)
    value_f = _font(24)
    _nav(draw, w, "dashboard")

    draw.text((40, 76), "Dashboard", fill=TEXT, font=title_f)
    draw.text(
        (40, 112),
        "Letzte Captures und Vault-Aktivität — lokal auf deiner Maschine.",
        fill=MUTED,
        font=body_f,
    )

    # Stats card
    _round(draw, (40, 150, w - 40, 290), SURFACE)
    draw.text((60, 168), "Überblick", fill=TEXT, font=_font(17))
    stats = [
        ("Entries gesamt", "128"),
        ("Vault-Notizen", "94"),
        ("Text / Voice", "101 / 27"),
        ("Semantische Suche", "an"),
    ]
    box_w = 200
    for i, (label, value) in enumerate(stats):
        x0 = 60 + i * (box_w + 16)
        _round(draw, (x0, 205, x0 + box_w, 265), SURFACE2, radius=8)
        draw.text((x0 + 14, 214), label, fill=MUTED, font=small_f)
        draw.text((x0 + 14, 234), value, fill=TEXT, font=value_f)

    # Entries table
    _round(draw, (40, 310, w - 40, 500), SURFACE)
    draw.text((60, 328), "Letzte Entries", fill=TEXT, font=_font(17))
    headers = ["Zeit", "Status", "Titel", "Art"]
    xs = [60, 170, 280, 780]
    for x, hlabel in zip(xs, headers, strict=True):
        draw.text((x, 362), hlabel, fill=MUTED, font=small_f)
    draw.line((60, 384, w - 60, 384), fill=BORDER, width=1)
    rows = [
        ("heute 09:14", "done", "Ideen für Mac-Mini Hosting", "text"),
        ("heute 08:02", "done", "Reiseplanung Tokio", "voice"),
        ("gestern 22:41", "done", "Meeting-Notizen Product Pivot", "text"),
    ]
    y = 398
    for zeit, status, titel, art in rows:
        draw.text((60, y), zeit, fill=TEXT, font=body_f)
        _round(draw, (170, y - 2, 230, y + 20), (28, 55, 42), radius=999, outline=None)
        draw.text((178, y), status, fill=OK_SOFT, font=small_f)
        draw.text((280, y), titel, fill=TEXT, font=body_f)
        draw.text((780, y), art, fill=MUTED, font=body_f)
        y += 34

    # Vault table
    _round(draw, (40, 520, w - 40, 680), SURFACE)
    draw.text((60, 538), "Zuletzt im Vault", fill=TEXT, font=_font(17))
    draw.text((60, 572), "Titel", fill=MUTED, font=small_f)
    draw.text((420, 572), "Pfad", fill=MUTED, font=small_f)
    draw.line((60, 594, w - 60, 594), fill=BORDER, width=1)
    vault = [
        ("Ideen für Mac-Mini Hosting", "work/Ideen für Mac-Mini Hosting.md"),
        ("Reiseplanung Tokio", "travel/Reiseplanung Tokio.md"),
        ("Meeting-Notizen Product Pivot", "work/Meeting-Notizen Product Pivot.md"),
    ]
    y = 608
    mono = _font(13)
    for titel, path in vault:
        draw.text((60, y), titel, fill=TEXT, font=body_f)
        draw.text((420, y), path, fill=MUTED, font=mono)
        y += 28

    return img


def ask_png() -> Image.Image:
    w, h = 1000, 720
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    title_f = _font(26)
    body_f = _font(15)
    small_f = _font(13)
    _nav(draw, w, "ask")

    draw.text((40, 76), "Suchen & Fragen", fill=TEXT, font=title_f)
    draw.text(
        (40, 112),
        "Vault durchsuchen oder dein Brain befragen — wie Telegram /find und /ask.",
        fill=MUTED,
        font=body_f,
    )

    # Search card
    _round(draw, (40, 150, w - 40, 360), SURFACE)
    draw.text((60, 168), "Vault-Suche", fill=TEXT, font=_font(17))
    _round(draw, (60, 205, 760, 245), BG, radius=8)
    draw.text((74, 215), "Mac Mini Hosting", fill=TEXT, font=body_f)
    _round(draw, (780, 205, 920, 245), ACCENT, radius=8, outline=None)
    draw.text((812, 215), "Suchen", fill=BG, font=_font(15))

    draw.text((60, 270), "Ideen für Mac-Mini Hosting", fill=TEXT, font=_font(16))
    draw.text(
        (60, 294),
        "Always-on Box, Long-Polling, Privacy als Verkaufsargument …",
        fill=MUTED,
        font=small_f,
    )
    draw.line((60, 320, w - 60, 320), fill=BORDER, width=1)
    draw.text((60, 332), "Docker Compose Consumer-Edition", fill=TEXT, font=_font(16))

    # Ask card
    _round(draw, (40, 380, w - 40, 680), SURFACE)
    draw.text((60, 398), "Brain fragen", fill=TEXT, font=_font(17))
    _round(draw, (60, 435, w - 60, 500), SURFACE2, radius=8)
    draw.rectangle((60, 435, 63, 500), fill=ACCENT)
    draw.text(
        (78, 455),
        "Was weiß ich schon über Self-Hosting auf dem Mac Mini?",
        fill=TEXT,
        font=body_f,
    )

    _round(draw, (60, 520, w - 60, 620), SURFACE2, radius=8)
    draw.rectangle((60, 520, 63, 620), fill=OK)
    answer = (
        "Du planst eine Always-on-Box mit Long-Polling, Docker Compose für die\n"
        "Consumer-Edition und Privacy als zentrales Argument."
    )
    draw.multiline_text((78, 535), answer, fill=TEXT, font=body_f, spacing=4)
    draw.text((78, 590), "Konfidenz 0.82 · 2 Quellen", fill=MUTED, font=small_f)

    _round(draw, (60, 640, 780, 678), BG, radius=8)
    draw.text((74, 650), "Was weiß ich schon über …?", fill=MUTED, font=body_f)
    _round(draw, (800, 640, 940, 678), ACCENT, radius=8, outline=None)
    draw.text((832, 650), "Fragen", fill=BG, font=_font(15))

    return img


def flow_gif() -> None:
    w, h = 880, 420

    def frame(title: str, lines: list[str], step: int, total: int = 3) -> Image.Image:
        img = Image.new("RGB", (w, h), BG)
        draw = ImageDraw.Draw(img)
        title_f = _font(28)
        body_f = _font(20)
        small_f = _font(16)
        draw.text((40, 28), "Seiton Brain", fill=TEXT, font=title_f)
        draw.text((40, 68), title, fill=ACCENT, font=body_f)
        _round(draw, (40, 110, w - 40, h - 70), SURFACE, radius=14)
        y = 140
        for line in lines:
            draw.text((70, y), line, fill=TEXT, font=body_f)
            y += 36
        for i in range(total):
            cx = w // 2 - (total - 1) * 18 + i * 36
            color = ACCENT if i == step else BORDER
            draw.ellipse((cx - 6, h - 42, cx + 6, h - 30), fill=color)
        draw.text((40, h - 48), "Capture → Classify → Vault", fill=MUTED, font=small_f)
        if step == total - 1:
            draw.text((w - 160, h - 48), "fertig", fill=OK, font=small_f)
        return img

    frames = [
        frame(
            "1 · Capture",
            [
                "Telegram: „Idee: Mac Mini als Always-on Host“",
                "oder REST /v1/capture · Web-UI · Voice",
            ],
            0,
        ),
        frame(
            "2 · Classify",
            [
                "LLM: Kategorie work · Tags · Append/Create",
                "OpenAI oder lokal Ollama — gleiches Schema",
            ],
            1,
        ),
        frame(
            "3 · Vault + Retrieve",
            [
                "Markdown in Obsidian (optional) · [[Links]]",
                "RAG /ask · Digest · REST · MCP",
            ],
            2,
        ),
    ]
    path = OUT / "flow.gif"
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=False,
    )
    print(f"wrote {path}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dash = OUT / "dashboard.png"
    ask = OUT / "ask.png"
    dashboard_png().save(dash, optimize=True)
    ask_png().save(ask, optimize=True)
    print(f"wrote {dash}")
    print(f"wrote {ask}")
    flow_gif()


if __name__ == "__main__":
    main()
