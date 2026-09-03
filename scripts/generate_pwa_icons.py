#!/usr/bin/env python3
"""Generate PWA icons (E23-2) into app/ui/static/icons/.

Run once; result is checked in. Re-run when colors/design change:
.venv/bin/python scripts/generate_pwa_icons.py

Motif: second-brain graph — three linked nodes on a dark ground,
colors from app.css (--bg, --accent, --accent-hover).
"""

from pathlib import Path

from PIL import Image, ImageDraw

BG = "#0f1419"
SURFACE = "#1a2332"
ACCENT = "#5b9fd4"
ACCENT_LIGHT = "#7ab3e0"

OUT_DIR = Path(__file__).resolve().parents[1] / "app" / "ui" / "static" / "icons"

# Supersampling factor for smooth edges.
SS = 4


def _draw_icon(size: int, *, maskable: bool) -> Image.Image:
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Maskable: full-bleed background (OS crops) and motif in the safe
    # zone (inner 80%). Else: rounded square.
    if maskable:
        draw.rectangle([0, 0, s, s], fill=BG)
        scale = 0.72
    else:
        radius = int(s * 0.22)
        draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=BG)
        scale = 0.92

    # Node positions (relative, triangle layout), scaled around center.
    def pt(rx: float, ry: float) -> tuple[float, float]:
        cx, cy = s / 2, s / 2
        return (cx + (rx - 0.5) * s * scale, cy + (ry - 0.5) * s * scale)

    nodes = [
        (pt(0.30, 0.70), int(s * 0.105), ACCENT),        # unten links
        (pt(0.72, 0.62), int(s * 0.085), ACCENT),        # unten rechts
        (pt(0.52, 0.28), int(s * 0.135), ACCENT_LIGHT),  # oben (Hauptknoten)
    ]

    # Edges first (under the nodes).
    width = max(2, int(s * 0.035))
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            draw.line([nodes[i][0], nodes[j][0]], fill=SURFACE, width=width * 2)
            draw.line([nodes[i][0], nodes[j][0]], fill=ACCENT, width=width)

    for (x, y), r, color in nodes:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
        # Inner dark ring for a bit of depth.
        r2 = int(r * 0.45)
        draw.ellipse([x - r2, y - r2, x + r2, y + r2], fill=BG)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, True),
    ]
    for name, size, maskable in targets:
        icon = _draw_icon(size, maskable=maskable)
        if name == "apple-touch-icon.png":
            # iOS dislikes alpha on home-screen icons.
            icon = icon.convert("RGB")
        icon.save(OUT_DIR / name)
        print(f"wrote {OUT_DIR / name}")


if __name__ == "__main__":
    main()
