# Designsystem — Seiton Brain (E47-3)

Verbindliche Designsprache für die Web-UI. Abgeleitet aus
[`ui-inventory.md`](ui-inventory.md) (Ist) und
[`ui-reference-request.md`](ui-reference-request.md) (Soll) — **kein Klon**
fremder Produkte.

**Geltung:** Alle UI-Änderungen (Templates, CSS, JS) folgen diesem Dokument.
Umsetzung der Tokens in Code: **E47-4** (`app.css` / `setup.css`); visuelle
Ausarbeitung Screen für Screen in den Stories, die den Screen ohnehin anfassen
(E30-2/4/5/6, E40, …).

**Stack bleibt:** Jinja2 + Vanilla JS + CSS-Variablen — kein React/Tailwind in
dieser Phase.

---

## 1. Design-Prinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **Lokal & ruhig** | Second Brain auf der eigenen Maschine — dunkle, ruhige Flächen, wenig Visuelles Rauschen |
| **Capture first** | Erfassen ist jederzeit erreichbar (globaler Trigger); Friction niedrig |
| **Markdown ist Wahrheit** | Vault-Dateien bleiben Markdown; UI-Toolbar schreibt Syntax, kein paralleles WYSIWYG-Format |
| **Eine Entscheidung pro Schritt** | Onboarding/Wizards: nicht überladene Formulare |
| **Chat-first Retrieve** | Suche, Digest und RAG über einen Chat; Panel, nicht Pflicht-Vollbild |
| **Skip erlaubt** | Tutorials, Integrations-Kacheln, optionale Setup-Schritte — immer überspringbar |
| **Kein Archiv-Overhead** | Keine persistente Chat-History; optional Export. Gedächtnis = Vault |

---

## 2. Visuelle Basis (Dark-only)

**Kein Light-Theme** in V1. Bestehende Tokens in `app/ui/static/app.css` sind die
Ausgangsbasis; E47-4 vereinheitlicht Doppelungen mit `setup.css`.

### Farben (Semantik)

| Token | Ist-Wert | Verwendung |
|-------|----------|------------|
| `--bg` | `#0f1419` | Seitenhintergrund, PWA `theme-color` |
| `--surface` | `#1a2332` | Cards, Modals, Panels |
| `--surface-2` | `#243044` | KPI-Kacheln, Code-Hintergrund, Hover-Flächen |
| `--border` | `#2d3a4d` | Rahmen, Trennlinien |
| `--text` | `#e8eef7` | Primärtext |
| `--muted` | `#8b9cb3` | Labels, Hints, Meta |
| `--accent` | `#5b9fd4` | Links, Primary-Buttons, Fokus, aktiver Nav-Zustand |
| `--accent-hover` | `#7ab3e0` | Hover auf Accent |
| `--ok` | `#3d9a6a` | Erfolg |
| `--warn` | `#c9a227` | Warnung |
| `--err` | `#c75c5c` | Fehler |

**Nicht:** Fremde Akzente 1:1 übernehmen (Twitch-Lila, Make-Lila, Anam-Orange) —
Akzent bleibt Seiton-Blau. Charts dürfen denselben Accent oder dezente Varianten
nutzen, keine zweite Markenfarbe.

### Typografie

| Stufe | Größe | Gewicht | Einsatz |
|-------|-------|---------|---------|
| Display / Page | ~1.5rem | 600 | `.page-header h1` |
| Section | ~1.05–1.15rem | 600 | Card-Titel `h2` |
| Body | 0.95–1rem | 400 | Fließtext, Inputs |
| Meta / Label | 0.8–0.9rem | 400–500 | Labels, Hints, Tabellen-Header |
| Code / Editor | 0.85rem | 400 | Monospace (`ui-monospace`, Menlo, …) |

**Font-Stack:** `system-ui, -apple-system, "Segoe UI", sans-serif` — keine
eigenen Webfonts bis E47-5 / Verkaufsreife anders entscheidet.

### Spacing, Radius, Surfaces

| Token / Regel | Wert | Hinweis |
|---------------|------|---------|
| `--radius` | `10px` | Cards, große Panels |
| Control-Radius | `6–8px` | Buttons, Inputs, kleinere Flächen |
| Badge-Radius | `999px` | Pills |
| Spacing-Schritt | 0.25 / 0.5 / 0.75 / 1 / 1.25 / 1.5 rem | Keine Magic Numbers außerhalb der Skala (E47-4) |
| Shadows | dezent oder keine | Dark UI: eher Border als Schatten; Modals: leichter Drop-Shadow ok |
| Fokus | `outline: 2px solid var(--accent)` | Pflicht für Inputs **und** Buttons/Links |

### Breakpoints

| Name | Breite | Verhalten |
|------|--------|-----------|
| Mobile | ≤640px | Truncate enger; Topbar/Sidebar kompakt |
| Tablet | ≤800px | Notes: eine Spalte; Chat-Panel ggf. Vollbreite |
| Desktop | >800px | Sidebar + Topbar + optional Chat-Panel |

---

## 3. App-Shell & Navigation

Zielbild (Bereich 1):

```
[Vorher: Vault/Brain-Picker — Obsidian-Style]
              ↓
┌──────────┬──────────────────────────────────────┐
│ Sidebar  │  Topbar (Suche · Aktionen · User)    │
│ (Nav)    ├──────────────────────────────────────┤
│          │  Hauptinhalt     │ Chat-Panel (opt.) │
└──────────┴──────────────────────────────────────┘
```

| Element | Regel |
|---------|-------|
| **Sidebar** | Hauptmenü (Dashboard, Notizen, Chat-Trigger, Einstellungen); aktiver Zustand mit Accent; einklappbar (Icon-only) erlaubt |
| **Topbar** | Keine Duplikation der Hauptlinks; globale Suche / Shortcut-Hinweis, Primary Actions, Logout |
| **Vault-Picker** | Vor dem Projektkontext; Solo vs. Team (später) greift hier an |
| **Heute** | Horizontale Topnav — Migration schrittweise in Shell-Stories, nicht Big-Bang |

---

## 4. Komponenten-Regeln

### Buttons

| Variante | Verwendung |
|----------|------------|
| `primary` | Eine Hauptaktion pro Kontext (Speichern, Absenden, Weiter) |
| `secondary` | Abbrechen, Testen, Zurück, Nebenaktionen |
| Disabled | `opacity: 0.5`, `cursor: not-allowed` — während Loading |

Keine dritte „ghost“-Variante ohne Bedarf. Links als Button: `a.button.primary|secondary`.

### Inputs & Forms

- Labels über dem Feld (`span` + Input), muted Farbe
- Passwort/Secret-Felder: leer = unverändert (bestehende Settings-Konvention)
- Eine Entscheidung pro Wizard-Schritt, wo möglich
- Optionale Felder klar kennzeichnen

### Cards & Surfaces

- Inhaltliche Sektionen in `.card` (surface + border + radius)
- KPI: `.stats-grid` / `.stat` — große Zahl, kleines Label
- Charts optional auf dem Dashboard — Layout-Platz vorsehen, nicht V1-Pflicht für alle Metriken

### Badges & Status

- `.badge.ok` / `.warn` / `.err` / `.muted` für Instanz-/Komponentenstatus
- Info-Banner (Refero-Settings-Pattern) für Hinweise wie „Neustart nötig“

### Modals & Overlays

| Use Case | Pattern |
|----------|---------|
| Quicknote | Schwebendes Modal, global auslösbar (Button / Nav / Shortcut) |
| Bestätigen / Testen / Verbinden | Fokus-Modal statt `alert()` / `confirm()` |
| Tutorial | Spotlight-Tooltip (Hauptfläche abdunkeln), **skipbar**, nur relevante Features; einmalig nach erstem Brain |
| Settings-Unterflows | Modal mit Sektionen + Primary/Secondary unten |

### Chat-Panel

- Clean wie ChatGPT innen: Verlauf + Input unten mit Platz für Tools/Modell
- **Einbettung:** Side-Panel (Cursor/VS Code Copilot) bevorzugt — andockbar, einklappbar
- Alternativen: Floating; Vollbild nur mobil oder bewusst
- **Keine** persistente Chat-History-Sidebar; optional Export (Markdown)
- Suche/Digest über Intent oder Commands (`/find`, `/digest`)

### Notizen-Editor

| Aspekt | Regel |
|--------|-------|
| Layout | Master-Detail (Liste links, Editor rechts) — Obsidian-Feeling |
| Toolbar | **Fest oben** (Word-Style, schlank) — Aktionen → Markdown-Syntax |
| Preview | **Default:** Tabs Edit \| Preview; **Optional:** Split Live-Preview (Xcode) |
| Auto-Save | Ja für Vault-Notizen; **nein** für Quicknotes |
| Notion | Nur Look & Feel — kein Block-Datenmodell |

### Settings

- Linke Kategorie-Sidebar + Detailbereich (Refero)
- Bei Listen (Backups, …): optional dritte Spalte Liste → Detail + Tabs
- Save sichtbar; Tests in Modals

### Empty / Loading / Error

| Zustand | Regel |
|---------|-------|
| Empty | `.empty` + kurze Erklärung + optional CTA |
| Loading | Button disabled + Inline-Hinweis; kein blockierendes Alert |
| Error | Inline `.result.err` / Banner; kritische Flows: Modal |
| Pending Chat | `.chat-msg.pending` |

---

## 5. Flows (Kurz)

### Onboarding / Setup

1. Welcome + optionales Profil (wenige Felder, viele optional)
2. Step-Labels (Seiton-spezifisch), eine Entscheidung pro Screen wo sinnvoll
3. Vault → Provider → optional Telegram → Speichern
4. Optional: Integrations-Kacheln (skippbar)
5. Nach erstem Brain: skipbares Feature-Tutorial (Spotlight)

### Capture

| | Quicknote | Vault-Notiz |
|---|-----------|-------------|
| UI | Globales Modal | Dashboard / `/notes` |
| Speichern | Explizit absenden | Auto-Save |
| Tags | Nach Erstellung (manuell + LLM-Vorschlag) | Frontmatter |
| Medien | PDF/Foto nice-to-have | Pipeline vorhanden |

### Dashboard

- KPI-Zeile, Aktivitätstabellen, optional Charts
- Zeitraum-Filter sinnvoll
- Projektbezogene Sidebar (Vault-Struktur) ergänzend zur App-Sidebar möglich

---

## 6. Responsive & PWA

- PWA `standalone` behält Shell; Chat-Panel auf schmalen Viewports Vollbreite oder Bottom-Sheet-ähnlich (später spezifizieren)
- Capture-Trigger auf Mobile erreichbar (FAB oder Topbar-Icon)
- Touch-Ziele ≥ ~44px wo Primäraktionen

---

## 7. Sprache & Ton

- UI-Texte **Deutsch** (Ist); öffentliche GitHub-Docs teils EN
- Kurz, konkret, ohne Marketing-Floskeln
- Fehler: was passiert ist + was der Nutzer tun kann
- Secrets nie im Klartext in UI-Logs anzeigen

---

## 8. Für Agents (verbindlich)

1. Vor UI-Arbeit: dieses Dokument + betroffene Stelle in [`ui-inventory.md`](ui-inventory.md) lesen.
2. Referenzen in [`ui-reference-request.md`](ui-reference-request.md) sind **Richtung**, keine Pixel-Vorlage.
3. **Kein** eigenmächtiges Redesign außerhalb der Story; Token-Angleichung → E47-4.
4. Neue Farben/Fonts nur mit Begründung und ROADMAP/Issue; Standard = Tokens oben.
5. `alert()` / `confirm()` nicht neu einführen — Modal/Inline-Feedback.
6. Nach E47-3: Cursor-Rule verweist hierher.

---

## 9. Abgrenzung / nächste Stories

| Story | Inhalt |
|-------|--------|
| **E47-4** | `app.css` / `setup.css` auf Tokens ziehen, Doppelungen entfernen |
| **E47-5** | Design-Reife vor Verkauf (E21-2) |
| **E30-2** | Lesemodus / Preview umsetzen |
| **E30-4** | Toasts, Modals, zentrales Feedback |
| **E30-5/6** | Empty States, UX-Pass |
| **E40** | Knowledge Chat als Panel |

---

## Referenzen

- Ist: [`ui-inventory.md`](ui-inventory.md)
- Soll-Input: [`ui-reference-request.md`](ui-reference-request.md)
- Screenshots: `docs/ui-references/`
- CSS heute: `app/ui/static/app.css`, `app/ui/static/setup.css`
