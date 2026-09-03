# UI-Inventar — Seiton Brain (E47-1)

Ist-Aufnahme der Web-UI zum Start von Epic **E47** (Designsystem & UI/UX).
Stand **2026-09-02**, Release **v0.3.0**.

**Zweck:** Gemeinsame Faktenbasis vor E47-3 (`docs/design-system.md`). Kein Redesign,
keine Stilentscheidungen — nur was heute existiert, wo es bricht und was fehlt.

**Designsystem (E47-3):** [`design-system.md`](design-system.md) — verbindlich.
Referenzen: [`ui-reference-request.md`](ui-reference-request.md).

---

## 1. Stack & Architektur

| Aspekt | Ist-Stand |
|--------|-----------|
| Rendering | Jinja2-Server-Templates (`app/ui/templates/`) |
| Interaktion | Vanilla JS pro Screen (`app/ui/static/*.js`) |
| Styling | `app.css` (609 Zeilen) + `setup.css` (198 Zeilen, nur Setup) |
| Framework | Kein React/Vue/Tailwind/Component-Library |
| Auth | Optional `UI_PASSWORD` → Session-Cookie; sonst localhost-only |
| PWA | `manifest.webmanifest`, Service Worker `/sw.js`, Icons 192/512/maskable |
| Sprache UI | Deutsch (`lang="de"` in `base.html`, Manifest `lang: de`) |
| Tests | 7× `tests/test_ui_*.py` — FastAPI TestClient, kein Browser |

```
Browser → FastAPI (app/ui/router.py)
            ├── HTML: /login, /setup, /dashboard, /ask, /notes, /settings
            ├── API:  /api/ui/*
            └── Static: /ui/static/*, /manifest.webmanifest, /sw.js
```

---

## 2. Screens & Routen

| Route | Template | JS | Guard | Zweck |
|-------|----------|-----|-------|-------|
| `/` | Redirect | — | — | → `/setup` oder `/dashboard` |
| `/login` | `login.html` | `login.js` | Nur wenn Auth aktiv | Passwort-Login |
| `/setup` | `setup.html` | `setup.js` | localhost-only | Erstkonfiguration (6 Schritte) |
| `/dashboard` | `dashboard.html` | `dashboard.js` | Session / localhost | Capture + Übersicht |
| `/ask` | `ask.html` | `ask.js` | Session / localhost | Suche, Digest, RAG-Chat |
| `/notes` | `notes.html` | `notes.js` | Session / localhost | Notizen lesen/bearbeiten |
| `/settings` | `settings.html` | `settings.js` | Session / localhost | `.env`, Backup, Lizenz |

**Layout-Varianten** (`base.html` → `.wrap`):

- Standard: `max-width: 920px`
- `narrow`: Setup, Login — `560px`
- `wide`: Notes, Settings — `1100px`

**Navigation** (`topnav` in `base.html`): Brand, Dashboard, Suchen & Fragen, Notizen,
Einstellungen; Setup-Link nur wenn `is_setup_complete()` false; Abmelden wenn Auth aktiv.

---

## 3. Komponenten-Katalog (faktisch genutzt)

Kein formaler Katalog im Code — diese Liste beschreibt die wiederkehrenden Bausteine.

### Shell

| Klasse / Element | Verwendung |
|------------------|------------|
| `.topnav`, `.brand` | Globale Navigation |
| `.page-header` | Titel + Unterzeile pro Screen |
| `.wrap` / `.narrow` / `.wide` | Seitenbreite |

### Flächen & Inhalt

| Klasse | Verwendung |
|--------|------------|
| `.card` | Hauptcontainer pro Sektion |
| `.card-hint` | Erklärtext unter Card-Titel |
| `.stats-grid` + `.stat` | Dashboard- und Settings-KPIs |
| `table.data` | Dashboard-Tabellen (Entries, Vault) |
| `.result-list`, `.hit-*` | Suchtreffer |
| `.chat-log`, `.chat-msg` | RAG-Antworten (user/assistant/pending) |
| `.notes-layout` | Master-Detail (Liste + Editor) |
| `.note-item` | Eintrag in Notizen-Liste |
| `.notes-editor` | Monospace-Textarea |
| `.backup-item` | `<details>` pro Backup |
| `.onboarding-checklist` | Setup-Abschluss |
| `.trust` | Setup-Vertrauensblock |

### Formulare & Aktionen

| Klasse | Verwendung |
|--------|------------|
| `.inline-form` | Suche, Filter, Digest |
| `.ask-form` | Textarea + Submit (Capture, Ask, Login) |
| `button.primary` / `button.secondary` | Haupt- und Sekundäraktionen |
| `a.button.primary` | Setup-Abschluss-Links |
| `label`, `.checkbox`, `.checkbox-inline` | Felder (Setup + Settings) |
| `#settings-form label` | Settings-spezifische Feldstyles |

### Feedback & Status

| Klasse | Verwendung |
|--------|------------|
| `.empty` | Leerzustände, Platzhalter, Ladehinweise |
| `.result.ok` / `.result.err` | Setup-/Test-Ergebnisse |
| `.capture-ok` / `.capture-err` | Capture-Ergebnis |
| `.badge` (+ `.ok`, `.warn`, `.err`, `.muted`) | Status in Settings |
| `.status-pill` | Setup-Fortschritt (in `setup.css`) |
| `.hidden` | Ausgeblendete Panels |

### Setup-spezifisch (`setup.css`)

| Klasse | Verwendung |
|--------|------------|
| `.steps`, `.step-dot` | Fortschrittsbalken (6 Schritte) |
| `.step-panel` | Wizard-Seiten |

**Fehlende Komponenten** (geplant u. a. in E30-4): Toasts, Modals, einheitliche
Bestätigungsdialoge, Skeleton-Loader, dedizierte Error-Pages.

---

## 4. CSS-Design-Tokens (`:root` in `app.css`)

| Token | Wert | Semantik (faktisch) |
|-------|------|---------------------|
| `--bg` | `#0f1419` | Seitenhintergrund |
| `--surface` | `#1a2332` | Cards |
| `--surface-2` | `#243044` | Stat-Kacheln, Code-Hintergrund |
| `--border` | `#2d3a4d` | Rahmen, Trennlinien |
| `--text` | `#e8eef7` | Primärtext |
| `--muted` | `#8b9cb3` | Sekundärtext, Labels |
| `--accent` | `#5b9fd4` | Links, Primary-Buttons, Fokus |
| `--accent-hover` | `#7ab3e0` | Link-Hover |
| `--ok` | `#3d9a6a` | Erfolg |
| `--warn` | `#c9a227` | Warnung |
| `--err` | `#c75c5c` | Fehler |
| `--radius` | `10px` | Cards |
| `font-family` | `system-ui, …` | Keine eigene Font-Datei |

**Hardcodierte Werte** (nicht als Token): viele `border-radius: 6px`/`8px`,
Badge-/Chat-Hintergründe als `rgba(...)`, feste `max-height` in `.chat-log` (360px)
und `.notes-list` (480px).

**Doppelte Definitionen:** `button`, `.result`, `.hidden`, Label/Input-Basics existieren
parallel in `app.css` und `setup.css` mit leicht abweichenden Werten (Padding, Font-Size).

**Keine dokumentierte Skala** für: Typografie-Stufen, Spacing-Scale, Shadows, Z-Index,
Breakpoints (nur zwei `@media`-Blöcke: 640px, 800px).

---

## 5. Zustände pro Screen

Legende: ✅ vorhanden · ⚠️ minimal · ❌ fehlt

### `/login`

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty | — | N/A |
| Loading | ⚠️ | Button `disabled` während Request |
| Success | ✅ | Redirect via Cookie |
| Error | ✅ | `#login-result` Text |

### `/setup` (6 Schritte)

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty | — | N/A |
| Loading | ⚠️ | Button disabled beim Speichern |
| Success | ✅ | Schritt 5 „Fertig", `.status-pill.ok` |
| Error | ✅ | `.result.err` pro Test/Save |
| Warnung | ✅ | Allowlist-Hinweis, `window.confirm` |

### `/dashboard`

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty (Entries) | ✅ | `.empty` in Tabelle |
| Empty (Vault) | ✅ | `.empty` in Tabelle |
| Loading | ⚠️ | „Lade…" initial, „Klassifiziere…" bei Capture |
| Error | ⚠️ | `.empty` mit Fehltext oder `alert()` |

### `/ask`

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty (Suche) | ✅ | Platzhaltertext |
| Empty (Treffer) | ✅ | „Keine Treffer …" |
| Loading | ✅ | „Suche …", Chat `.pending` |
| Error | ✅ | `.empty` / `.chat-error` |

### `/notes`

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty (Liste) | ✅ | „Keine Notizen gefunden." |
| Empty (Editor) | ✅ | Disabled Textarea + Platzhalter |
| Loading | ⚠️ | „Lade …" im Editor |
| Error | ⚠️ | `.empty` oder `alert()` |
| Dirty guard | ⚠️ | `window.confirm` beim Wechsel |

### `/settings`

| Zustand | Status | Umsetzung |
|---------|--------|-----------|
| Empty (Backups) | ✅ | `.empty` |
| Loading | ⚠️ | „Lade …", Button disabled bei Backup/Reindex |
| Success | ✅ | `.result.ok`, Capture-ähnliche Meldungen |
| Error | ⚠️ | `.result.err`, `alert()` bei Tests |

---

## 6. Interaktions- & UX-Lücken

| Thema | Befund |
|-------|--------|
| **Native Dialoge** | `alert()` / `confirm()` in `dashboard.js`, `notes.js`, `settings.js`, `setup.js` — kein eigenes Modal-System |
| **Toasts** | Keine; Erfolg/Fehler oft inline oder blockierend |
| **Fokus** | Inputs/Textareas: `outline: 2px solid var(--accent)`; Buttons/Links ohne sichtbaren Fokus-Ring |
| **Keyboard** | Keine dokumentierten Shortcuts; Tab-Reihenfolge nicht geprüft |
| **Mobile** | Topnav wrappt nicht explizit; Notes-Layout stapelt ab 800px; Tabellen können horizontal scrollen |
| **Lesemodus** | Kein Markdown-Preview (E30-2 offen) |
| **i18n** | Nur DE in UI; öffentliche GitHub-Docs teils EN |
| **Barrierefreiheit** | Teilweise `aria-live`; keine Landmark-Rollen, keine Skip-Links |
| **Konsistenz** | Setup nutzt eigene CSS-Datei; Radius/Padding weichen ab |

---

## 7. API-Oberfläche (`/api/ui/*`)

Relevant für UI-Zustände und spätere Screens:

| Endpoint | Screen(s) |
|----------|-----------|
| `POST /api/ui/login` | Login |
| `GET /api/ui/dashboard` | Dashboard |
| `POST /api/ui/capture` | Dashboard |
| `GET /api/ui/search` | Ask |
| `POST /api/ui/ask` | Ask |
| `POST /api/ui/digest` | Ask |
| `GET/PUT/DELETE /api/ui/notes*` | Notes |
| `GET /api/ui/vault-config` | Notes |
| `GET/POST /api/ui/settings` | Settings |
| `POST /api/ui/settings/test` | Settings, Setup |
| `POST /api/ui/backup`, `GET …/backups` | Settings |
| `POST /api/ui/reindex` | Settings |
| `GET/POST /api/ui/license` | Settings |

Setup-Wizard nutzt zusätzlich `/api/setup/*` (nicht unter `/api/ui`).

---

## 8. PWA & Offline

| Element | Datei | Anmerkung |
|---------|-------|-----------|
| Manifest | `manifest.webmanifest` | `standalone`, `start_url: /dashboard`, DE |
| Service Worker | `sw.js` | Cache-First für statische Assets |
| Icons | `app/ui/static/icons/` | 192, 512, maskable, apple-touch |
| Theme | `theme-color` `#0f1419` | Entspricht `--bg` |

Kein Offline-Capture, kein Background-Sync — PWA = installierbare Shell.

---

## 9. Screenshot-Satz (manuell, für E45-15 / E47-Abgleich)

Noch **nicht** im Repo. Empfohlene Aufnahmen nach `docker compose up` + abgeschlossenem Setup:

| # | URL | Notiz |
|---|-----|-------|
| 1 | `/setup` (Schritt 0 + 2) | Wizard + Formular |
| 2 | `/dashboard` | Mit mindestens 1 Entry |
| 3 | `/ask` | Suche mit Treffern + Chat-Antwort |
| 4 | `/notes` | Liste + geöffnete Notiz |
| 5 | `/settings` | Status-Grid + Backup-Liste |
| 6 | `/login` | Nur wenn `UI_PASSWORD` gesetzt |
| 7 | Mobile (375px) | Dashboard oder Ask |

Ablage (Vorschlag): `docs/ui-screenshots/` — wird in **E45-15** oder manuell befüllt.

---

## 10. Inkonsistenzen & Priorität für E47-3+

1. **Zwei Stylesheets** — `setup.css` vs. `app.css` (E47-4)
2. **Kein Feedback-System** — blockiert E30-4 sinnvoll
3. **Uneinheitliche Fehler-UX** — inline vs. `alert()`
4. **Keine Typo-/Spacing-Tokens** — erschwert konsistenten Ausbau (E30-2 Lesemodus, E40 Chat)
5. **Dark-only** — kein Light-Theme (bewusst offen lassen bis Referenzen da sind)

---

## Referenzen

- Code: `app/ui/`
- Router: `app/ui/router.py`
- Roadmap: E47 in [`ROADMAP.md`](../ROADMAP.md)
- Nächster Schritt: [`ui-reference-request.md`](ui-reference-request.md) (E47-2 **STOP**)
