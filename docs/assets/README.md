# README-Assets (E11-4)

Visuelle Assets für das Root-`README.md`:

| Datei | Inhalt |
|-------|--------|
| `flow.gif` | Animierter Capture → Classify → Vault-Flow |
| `dashboard.png` | Web-UI Dashboard (Dark Theme, Demo-Daten) |
| `ask.png` | Web-UI Suchen & Fragen (Demo) |
| `_mockups/` | HTML-Mockups + CSS der echten UI (für spätere Live-Screenshots) |

Neu generieren (Pillow nötig, z. B. `pip install pillow`):

```bash
python scripts/generate-readme-assets.py
```

Die PNGs/GIF sind **illustrativ** (Demo-Daten), nicht Live-Captures aus einer
laufenden Instanz. `_mockups/*.html` kann lokal im Browser geöffnet und
manuell ersetzt werden.
