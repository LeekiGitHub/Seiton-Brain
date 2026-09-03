# UI-Referenz-Anfrage — STOP (E47-2)

**Status: ✅ Input vorhanden — E47-2 abgeschlossen (2026-09-02). E47-3 freigegeben.**

Bis zum Abschluss von E47-2 (2026-09-02) galt:

- **Kein** eigenmächtiges Redesign durch Agents oder CI-Tools
- Kein `docs/design-system.md` (E47-3) — **jetzt erlaubt**
- Keine Token-Umstellung in `app.css` / `setup.css` (E47-4) — weiterhin erst nach E47-3
- **Keine** visuellen Stilentscheidungen in UI-Stories (E30-2/4/5/6)

Erlaubt bleiben: Bugfixes, Funktionalität, Textkorrekturen, Tests, Doku ohne Stilvorgaben.

**Ist-Aufnahme:** [`ui-inventory.md`](ui-inventory.md) · **Nach Input:** E47-3 ableiten.

---

## So lieferst du Referenzen

Pro Bereich **2–4 Screenshots oder Links** (Mobbin, Dribbble, Live-Apps, eigene Skizzen).
Kurz notieren, **was** dir daran gefällt (nicht nur „sieht gut aus").

| Feld | Inhalt |
|------|--------|
| **Zweck** | Was der Bereich im Produkt leisten soll |
| **Elemente** | Welche UI-Bausteine relevant sind |
| **Interaktionen** | Klicks, Flows, Feedback |
| **Plattform** | Desktop-Browser, schmales Fenster, PWA/Home-Screen |
| **Suchbegriffe** | Stichworte für Referenzsuche |
| **Deine Referenzen** | *← hier eintragen oder Dateien verlinken* |

Referenzen können als:

- Links in dieser Datei (Abschnitt „Deine Referenzen")
- Bilder unter `docs/ui-references/<bereich>/` (PNG/WebP, keine Secrets)
- Kommentar im zugehörigen PR

**Fertig-Kriterium E47-2:** Alle sechs Bereiche haben mindestens zwei Referenzen **oder**
eine bewusste Entscheidung „am Ist-Stand orientieren" mit Begründung.

---

## Bereich 1 — App-Shell & Navigation

| | |
|---|---|
| **Zweck** | Wechsel zwischen Hauptbereichen; Orientierung **im Projekt/Brain** |
| **Screens heute** | `base.html` — nur **horizontale Topnav** (Dashboard, Ask, Notes, Settings) |
| **Zielbild** | **Sidebar + Topbar**; vor Projekt-Einstieg: **Brain/Vault-Auswahl** (Obsidian-Style) |
| **Plattform** | Desktop/PWA; Chat-Panel (Bereich 4) dockt an Shell an, ersetzt sie nicht |
| **Quelle Referenzen** | Überwiegend [Refero](https://refero.design) |

### Deine Referenzen

- [x] Richtung + zwei Refero-Screenshots (2026-09-02)

**Produkt-Richtung (Entwickler):**

| Ebene | Pattern | Vorbild |
|-------|---------|---------|
| **Vor dem Projekt** | Auswahl des Second Brain / Vault / Workspace | **Obsidian** Vault-Picker |
| **Sidebar** | Hauptnavigation zwischen Menüpunkten (Dashboard, Notizen, …) | **Twitch Creator Dashboard**, **ChatGPT** (Icon + Label, aktiv hervorgehoben) |
| **Topbar** | Kontext, Suche, Aktionen, ggf. Breadcrumbs | **VS Code / Cursor** (schlanke Command-Leiste) |
| **Im Projekt** | Sidebar + Topbar gemeinsam — Orientierung wie in IDE/Dashboard-Tools | Make-Beispiel: globale Icon-Leiste + kontextuelle Sektionen |

**Heute → Soll:** Topnav-only wird durch **Sidebar (Navigation)** + **Topbar (Werkzeuge/Kontext)** ersetzt; passt zu Bereich 3 (projektbezogene Sidebar für Vault-Struktur kann ergänzend kommen).

#### N1. Twitch Creator Dashboard — Sidebar + Top-Suche

![Twitch Sidebar und Topbar](../ui-references/01-app-shell-nav/01-twitch-creator-sidebar-topbar.jpg)

| | |
|---|---|
| **Quelle** | Twitch Creator Dashboard (Refero) |
| **Relevant für Seiton** | Linke Sidebar mit Sektionen, Collapse; Topbar mit Suche (⌘/), Profil, Aktionen |

**Was gefällt / was übernehmen:**

- **Sidebar** für Haupt-Menüpunkte — klarer aktiver Zustand (lila Highlight → Seiton-Akzent).
- **Topbar** für globale Suche und Utility (Hilfe, Notifications, User) — nicht alle Menülinks oben.
- Sidebar **einklappbar** (Icon-only) denkbar.
- Drei-Spalten-Layout (Varianten-Liste + Preview) **nicht** 1:1 — nur Shell-Pattern Sidebar+Top.

#### N2. Make — Organisation: Icon-Sidebar + Sektions-Nav

![Make Dual-Sidebar](../ui-references/01-app-shell-nav/02-make-org-dual-sidebar.png)

| | |
|---|---|
| **Quelle** | Make (Refero) |
| **Relevant für Seiton** | Schmale Icon-Leiste (Org/Module) + zweite Spalte mit Detail-Navigation |

**Was gefällt / was übernehmen:**

- **Zwei Ebenen:** Icon-Rail (Wechsel grober Bereiche) + Text-Sidebar (Untermenü) —
  analog: **Brain/Vault-Wahl** vs. **Navigation innerhalb des Brains**.
- Topbar rechts: **Primary Actions** (+ Create …), Settings, User — Cursor/IDE-Feeling.
- Farben (lila Make) **nicht** übernehmen — Layout in Seiton-Dark.

#### N3. Obsidian — Vault-Auswahl (konzeptionell)

| | |
|---|---|
| **Quelle** | Obsidian (kein Screenshot) |
| **Relevant für Seiton** | Screen **vor** Projekt-UI: welches Brain/Vault ist aktiv |

**Was gefällt / was übernehmen:**

- Beim Start bzw. Wechsel: **Vault/Brain-Picker** statt sofort voller App-Shell.
- Erst nach Auswahl: Sidebar+Topbar für Dashboard, Notizen, Chat, Einstellungen.
- An Solo/Team-Start aus Bereich 2 (Setup) anschlussfähig.

#### N4. ChatGPT / VS Code — Ergänzung zu N1/N2

| | |
|---|---|
| **Quelle** | ChatGPT (Sidebar-Stil), VS Code/Cursor (Topbar) — teils bereits Bereich 4 |
| **Relevant für Seiton** | ChatGPT-ähnliche Sidebar-Gruppierung; IDE-Topbar für Befehle/Suche |

**Was gefällt / was übernehmen:**

- **ChatGPT:** Sidebar als Nav-Container (nicht Chat-History-Pflicht — siehe Bereich 4).
- **VS Code/Cursor:** Topbar = schmale Aktionszeile; Chat-Panel dockt seitlich (Bereich 4).

---

## Bereich 2 — Setup & Onboarding

| | |
|---|---|
| **Zweck** | Erstkonfiguration ohne Angst (Keys lokal, Schritt für Schritt) |
| **Screens heute** | `/setup` — 6-Schritt-Wizard, Step-Dots, Trust-Block |
| **Elemente** | Fortschrittsanzeige, Formular-Cards, Test-Buttons, Status-Pills, Checkliste am Ende |
| **Interaktionen** | Vor/Zurück, Verbindung testen, Speichern, Warnung bei leerer Telegram-Allowlist |
| **Plattform** | Schmale Spalte (`narrow`), oft erstes Kontakt-Erlebnis nach Install |
| **Suchbegriffe** | `setup wizard dark`, `self-hosted onboarding`, `step indicator`, `API key setup` |

### Deine Referenzen

- [x] Vier Referenzen mit Entwickler-Notizen (2026-09-02)

#### 1. Bezi — Walkthrough + Onboarding-Checkliste

![Bezi: Tooltip + Checkliste](../ui-references/02-setup-onboarding/01-bezi-walkthrough-checklist.jpg)

| | |
|---|---|
| **Quelle** | Bezi (Design-Tool) |
| **Relevant für Seiton** | Kontextuelle Feature-Tooltips mit Spotlight (Hauptfläche abgedunkelt) |

**Was gefällt / was übernehmen:**

- **Tooltips am UI-Element** — Hauptseite leicht abgedunkeln, erklärten Bereich
  hervorheben, Tooltip passend zum Seiton-Design. Nur **relevante** Features erklären,
  nicht alles.
- **Skip** ist Pflicht — jederzeit überspringbar.
- **Checkliste** (wie unten rechts bei Bezi) ist nett, aber **kein Muss**.
- **Timing:** Tutorial/Walkthrough **nach dem ersten Anlegen** eines Second Brains /
  Projekts — **nicht** bei jedem neu erstellten Brain erneut.
- Nicht übernehmen: aufdringliche Wiederholung bei jedem neuen Vault/Projekt.

#### 2. Plattform-Auswahl — Kachel-Grid (Drittanbieter-Vorkonfiguration)

![Plattform-Kacheln mit Progress](../ui-references/02-setup-onboarding/02-platform-tile-selector.jpg)

| | |
|---|---|
| **Quelle** | Referenz-Screenshot (App unbekannt) — nur Layout-Pattern |
| **Relevant für Seiton** | Minimales Kachel-Grid zur optionalen Vorkonfiguration von Integrationen |

**Was gefällt / was übernehmen:**

- **Einfaches Kachel-Grid** — Nutzer wählt z. B. Google Kalender, Google Sheets, …;
  im Second Brain wird die Verbindung **vorbereitet** (spätere Integrations-Stories).
- Schritt muss **komplett skippbar** sein, wenn jemand alles manuell konfigurieren will.
- Welche Kacheln sinnvoll sind, ist **produktseitig noch offen** (nicht alles auf einmal).
- Referenz ist das **Pattern** (Kachel-Auswahl, minimalistisch), **nicht** das helle
  Farbschema — Umsetzung im Seiton-Dark-Look.
- Progress/Skip/Continue-Struktur aus dem Screenshot ist ok, Fokus liegt auf dem Grid.

#### 3. Doppler — Solo vs. Gruppe (Projekt-Start)

![Doppler: Use-Case-Auswahl](../ui-references/02-setup-onboarding/03-doppler-use-case-step.jpg)

| | |
|---|---|
| **Quelle** | Doppler (Secrets/Config) |
| **Relevant für Seiton** | Eine Entscheidung pro Screen; Projekt-Modus Solo/Team |

**Was gefällt / was übernehmen:**

- **Eine Entscheidung pro Screen** — weniger überladen als lange Formular-Wizards.
- **Kernidee (wichtiger als Doppler-Branding):** Beim Start eines neuen Projekts/
  Second Brains wählen: **„Ich alleine“** vs. **„Gruppe/Team“**.
- Bei **Gruppe:** Folgeschritt **Einladung** — andere einladen; Kooperation beeinflusst
  Konfiguration im Brain (z. B. **Rechte**) — Anbindung an spätere Phase-O-Stories.
- **Aufbau** (große Auswahl-Buttons, eine Frage) übernehmen; **Gradient-Hintergrund**
  optional, kein Muss — Seiton-Design hat Vorrang.
- Heutiger `/setup` ist instanzweit; Solo/Team ist **Produktvision** (nicht V1-Blocker),
  aber als Referenz für künftigen Onboarding-Flow festhalten.

#### 4. Lemni — Welcome + grobes Profil

![Lemni: Welcome + Name](../ui-references/02-setup-onboarding/04-lemni-welcome-profile.jpg)

| | |
|---|---|
| **Quelle** | Lemni |
| **Relevant für Seiton** | Welcome-Screen + minimales Profil + Step-Labels |

**Was gefällt / was übernehmen:**

- **Welcome-Screen** am Anfang — klarer Einstieg, nicht sofort technische Keys.
- **Grobes Profil** (z. B. Name) — Felderanzahl **passend zum Thema**; viele Felder
  **optional**, nicht alles Pflicht.
- **Step-Labels** (unten: was noch kommt) — Prinzip übernehmen, **Labels müssen zu
  Seiton passen** (nicht 1:1 „Workplace / Plan“ von Lemni).
- Passt zu `/setup` Schritt 0 („Willkommen“) und ggf. erweitertem Erst-Profil vor
  Vault/OpenAI-Konfiguration.

---

## Bereich 3 — Capture & Dashboard

| | |
|---|---|
| **Zweck** | Schnell erfassen + Überblick über letzte Aktivität |
| **Screens heute** | `/dashboard` — Capture-Textarea, Stats-Grid, zwei Tabellen |
| **Elemente** | Stat-Kacheln, Datentabelle, Primary-CTA „Ins Brain speichern" |
| **Interaktionen** | Capture mit Inline-Ergebnis, Refresh, leere Tabellen |
| **Plattform** | Standardbreite; Capture sollte auf Mobile nutzbar bleiben |
| **Suchbegriffe** | `dashboard stats dark`, `quick capture note`, `activity feed minimal`, `personal CRM home` |

### Deine Referenzen

- [x] Sieben Referenzen + Entwickler-Notizen — **Bereich 3 komplett** (2026-09-02)
- **Richtung (Entwickler):** Schnellnotizen/Capture per **Button**, Navigation oder Shortcut — **global erreichbar**, unabhängig vom aktuellen Screen.

**Produkt-Split (Capture vs. Notizen):**

| | Quicknotes (Capture) | Richtige Notizen |
|---|---------------------|------------------|
| **UI** | Schwebendes Modal/Fenster | Dashboard + `/notes`-Editor |
| **Speichern** | Explizit absenden (kein Auto-Save) | Auto-Save sinnvoll |
| **Format** | Markdown (minimal); Toolbar nur wenn sie Markdown-Syntax erzeugt | Markdown; ggf. Toolbar → `**bold**` etc. |
| **Tags** | Nach Erstellung: manuell, LLM-Vorschlag und/oder rein LLM | wie Vault/Frontmatter heute |
| **Medien** | PDF ablegen, Foto — wünschenswert | über Vault/Capture-Pipeline |

### Capture (Quick Note / Erfassen)

#### C1. Refero — schwebendes Quick-Note-Fenster

![Refero Quick Note Modal](../ui-references/03-capture-dashboard/capture/01-refero-quick-note-modal.jpg)

| | |
|---|---|
| **Quelle** | Refero |
| **Relevant für Seiton** | Modal über abgedunkeltem Hintergrund; „Untitled note“, minimaler Editor |

**Was gefällt / was übernehmen:**

- **Quicknotes:** schwebendes Fenster/Modal (Referenz-Pattern).
- **Richtige Notizen:** bleiben in der **Dashboard-/Notes-UI**, nicht im Modal.
- **Global erreichbar** — Button, Nav-Eintrag, Shortcut (⌘K o. Ä.), je nachdem was sich ergibt;
  von überall auslösbar, nicht nur auf `/dashboard`.

#### C2. HR/Refero — Note-Modal mit Toolbar

![Note mit Toolbar](../ui-references/03-capture-dashboard/capture/02-note-editor-toolbar.jpg)

| | |
|---|---|
| **Quelle** | Refero (HR-Kontext) |
| **Relevant für Seiton** | Richer Capture mit Formatierung; „Changes saved“; Privat-Hinweis |

**Was gefällt / was übernehmen:**

- **Kein Auto-Save bei Quicknotes** — nur bei „echten“ Notizen im Editor sinnvoll.
- **Markdown bevorzugt** für beide Kontexte.
- **Toolbar optional**, nur wenn Buttons die passende **Markdown-Syntax** einfügen
  (z. B. Bold → `**…**`) — kein WYSIWYG/HTML-Zweig.
- „Changes saved“-Pattern nur für den **Notizen-Editor**, nicht Quick-Capture.

#### C3. Create Tag — Keywords für KI

![Create tag Keywords](../ui-references/03-capture-dashboard/capture/03-create-tag-keywords.jpg)

| | |
|---|---|
| **Quelle** | Refero |
| **Relevant für Seiton** | Tags/Keywords beim Erfassen oder kurz danach; KI-Auto-Tagging |

**Was gefällt / was übernehmen:**

- Tags **manuell** setzbar, **LLM schlägt vor** (Kontext) und/oder **rein durch LLM** —
  Kombination aus Nutzer-Kontrolle und Automatik.
- **Timing bei Quicknotes:** Tag-Schritt **nach** dem Erstellen (nicht vor dem Absenden blockieren).

#### C4. Task — Dateien nach Typ filtern

![Files in task](../ui-references/03-capture-dashboard/capture/04-task-files-filter.jpg)

| | |
|---|---|
| **Quelle** | Refero (Task-Kontext) |
| **Relevant für Seiton** | Anhänge/Links/Docs gebündelt; Filter-Pills; leerer Zustand |

**Was gefällt / was übernehmen:**

- **Filter-Pills nicht übernehmen** — Referenz dient nur dem **Quick-Note-/Modal-Pattern**,
  nicht der Datei-Kategorisierung.
- **PDFs schnell ablegen** und **Foto-Capture** wären nice-to-have für Quick-Capture
  (an bestehende Voice/Foto-Pipeline anknüpfbar, nicht V1-Pflicht).

### Dashboard (Übersicht & Aktivität)

#### D1. Refero Supercuts — Sidebar + Metriken

![Supercuts Dashboard](../ui-references/03-capture-dashboard/dashboard/01-refero-supercuts-analytics.jpg)

| | |
|---|---|
| **Quelle** | Refero / Supercuts |
| **Relevant für Seiton** | Linke Sidebar, KPI-Zeile, Tabellen/Charts, leere Zustände, Primary CTA oben |

**Was gefällt / was übernehmen:**

- **Sidebar-Navigation** für Orientierung **innerhalb eines Projekts/Brains** — ähnlich
  **Obsidian** (Vault-Struktur) oder **VS Code** (Projekt-Kontext), nicht zwingend global
  statt Topnav; eher ergänzend zur heutigen Topnav wenn Multi-Projekt/Brain kommt.
- **Charts/Diagramme** als Option sinnvoll (Aktivität, Nutzung) — nicht alles sofort,
  aber Dashboard soll **Platz für Visualisierungen** lassen.
- Langfristig **Obsidian-/Notion-artige** Dashboard-Features wünschenswert; Referenz
  ist Richtung, nicht 1:1 Feature-Parität.
- **Design/Layout** übernehmen (Karten, KPI-Zeile, Tabellen, leere Zustände) — Farben
  an Seiton-Dark anpassen.

#### D2. Anam — Sessions-Analytics

![Anam Sessions](../ui-references/03-capture-dashboard/dashboard/02-anam-sessions-dashboard.jpg)

| | |
|---|---|
| **Quelle** | Anam |
| **Relevant für Seiton** | KPI-Karten, Performance-Zeile, Aktivitäts-Charts, kompakte Sidebar |

**Was gefällt / was übernehmen:**

- **Gleiche Richtung wie D1** — Sidebar, KPI-Karten, Übersicht.
- Konkretes Beispiel hier: **Diagramme/Graphen** (Session Activity, Minutes Used) —
  es geht um **Möglichkeit und Design** solcher Charts, nicht um Session-Metriken
  wie bei Anam.
- KPI-Zeile mit großen Zahlen + Chart-Zeile darunter als Layout-Pattern übernehmen.

#### D3. Twitch — Creator Discovery Dashboard

![Twitch Discovery](../ui-references/03-capture-dashboard/dashboard/03-twitch-discovery-analytics.jpg)

| | |
|---|---|
| **Quelle** | Twitch Creator Dashboard |
| **Relevant für Seiton** | Breite Sidebar-Navigation, Karten-Grid, Zeitraum-Filter, Empty States mit Icon |

**Was gefällt / was übernehmen:**

- Wieder primär **Layout**: Karten-Grid, gruppierte Metrik-Blöcke, Empty States mit Icon.
- **Zeitraum-Filter** (z. B. „letzte 7/30 Tage“) für Dashboard-Daten **sinnvoll** —
  z. B. für „letzte Entries“ / Vault-Aktivität.
- Breite Twitch-Sidebar nicht 1:1 — Topnav + ggf. projektbezogene Sidebar (siehe D1).

---

## Bereich 4 — Suche, RAG-Chat & Digest

| | |
|---|---|
| **Zweck** | Wissen wiederfinden — über **einen Chat** (RAG, Digest, Suche als Intent) |
| **Screens heute** | `/ask` — drei getrennte Karten (Suche, Digest, Chat) — **Soll: chat-first** |
| **Zielbild** | ChatGPT-ähnlicher, cleaner Chat; **kein Pflicht-Vollbild**; global erreichbar |
| **Plattform** | Desktop: Side-Panel (Cursor/VS Code Copilot) oder Floating; mobil: Vollbild ok |
| **Suchbegriffe** | `AI chat sources`, `copilot side panel`, `RAG citations`, `collapsible chat drawer` |

### Deine Referenzen

- [x] Richtung festgehalten + ChatGPT-Referenz (2026-09-02)

**Produkt-Richtung (Entwickler):**

| Aspekt | Entscheidung |
|--------|--------------|
| **Paradigma** | **Chat-first** — Suche, Digest und `/ask` über denselben Chat (Intent oder Commands wie Telegram) |
| **Chat-UI** | Clean wie **ChatGPT** (Nachrichten, Quellen, Aktionen) — **ohne** ChatGPT-Sidebar Pflicht |
| **Eingabe unten** | Optionen/Modellwahl etc. am **Input-Bereich** (z. B. „Tools“, Modell-Dropdown) |
| **Einbettung** | Chat **füllt nicht zwingend eine ganze Seite** — von **überall** auslösbar |
| **Präferenz Layout** | **Side-Panel** (Cursor / VS Code Copilot): rechts/links andockbar, **einklappbar** |
| **Alternativen** | Floating-Fenster oder Popup — Side-Panel ist Haupt-Vorbild |
| **Backend** | Bestehende Pipelines (`/api/ui/search`, `/ask`, `/digest`) bleiben; UI vereinheitlichen |
| **Chat-Historie** | **Keine** persistente, durchsuchbare Chat-History (kein ChatGPT-Sidebar-Archiv) |
| **Export** | Optional: aktuellen Chat **speichern/exportieren** (z. B. Markdown) — kein Muss für V1 |

#### R1. ChatGPT — cleaner Chat (ohne Sidebar-Fokus)

![ChatGPT Chat](../ui-references/04-search-chat/01-chatgpt-chat-clean.png)

| | |
|---|---|
| **Quelle** | ChatGPT (Web) |
| **Relevant für Seiton** | Aufgeräumter Chat-Verlauf, Willkommens-Card, Input unten mit „+“ / Tools |

**Was gefällt / was übernehmen:**

- **Cleaner Chat** — Fokus auf Verlauf + Eingabe, wenig Chrome.
- **Input-Leiste unten** mit Platz für **Optionen** (Anhänge, Tools, später Modellwahl).
- **Nicht übernehmen:** Pflicht-Sidebar mit **persistenter Chat-Historie** — Session reicht;
  optional später **Chat exportieren/speichern** (Markdown o. Ä.), nicht V1-Pflicht.
- Nachrichten-Aktionen (Copy, Feedback) als Pattern ok, nicht zwingend V1.

#### R2. Cursor / VS Code Copilot — Side-Panel (konzeptionell)

| | |
|---|---|
| **Quelle** | Cursor / VS Code Copilot Chat (kein Screenshot — Nutzer-Referenz) |
| **Relevant für Seiton** | Andockbares, einklappbares Chat-Panel neben der Haupt-UI |

**Was gefällt / was übernehmen:**

- Chat als **schmales Panel** links/rechts — Hauptinhalt (Dashboard, Notizen) bleibt sichtbar.
- **Einklappbar** — ein Klick, Chat weg; globaler Trigger (Shortcut/Button) öffnet wieder.
- Passt zu „von überall ausführbar“ ohne eigenen Vollbild-Screen `/ask`.
- Umsetzung in Seiton-Dark; Anbindung an E40 Knowledge Chat langfristig.

**Offen für E47-3:** Exakt Floating vs. Side-Panel vs. beides — Side-Panel ist **Präferenz**.

---

## Bereich 5 — Notizen-Editor (Master-Detail)

| | |
|---|---|
| **Zweck** | Vault-Notizen lesen, bearbeiten, organisieren — **Obsidian/Notion-Feeling** |
| **Screens heute** | `/notes` — Filter, Liste links, plain Monospace-Textarea, Speichern/Löschen |
| **Zielbild** | Master-Detail + **feste Toolbar oben** (Word-Style); Markdown im Vault |
| **Plattform** | Zwei-Spalten desktop; Lesemodus/Preview (E30-2) später |
| **Suchbegriffe** | `obsidian editor`, `notion page`, `word ribbon toolbar`, `markdown preview split` |

### Deine Referenzen

- [x] Richtung festgehalten (2026-09-02) — Screenshots optional nachreichbar

**Produkt-Richtung (Entwickler):**

| Aspekt | Entscheidung |
|--------|--------------|
| **Gesamt-UX** | Wie **Obsidian** + **Notion** — übersichtlich, notiz-zentriert, Split-Ansicht |
| **Layout** | Dateiliste/Navigation links (Obsidian), Editor rechts; Notion-ähnliche Ruhe/Lesbarkeit |
| **Toolbar** | **Fest oben** (nicht schwebend) — Referenz **Microsoft Word**: Bold, Überschriften, Listen, Link, … |
| **Format** | **Markdown** bleibt Source of Truth im Vault (wie heute) |
| **Toolbar-Verhalten** | Wie bei Quicknotes (Bereich 3): Buttons fügen **Markdown-Syntax** ein — kein separates WYSIWYG-Format |
| **Auto-Save** | Ja für „echte Notizen“ im Editor (explizit gewünscht vs. Quicknotes) |
| **Notion-Blöcke** | **Nicht** 1:1 — Notion als Inspiration für Layout/Editor-**Gefühl**, nicht Block-Datenmodell |

#### E1. Obsidian — Vault-Editor (konzeptionell)

| | |
|---|---|
| **Quelle** | Obsidian |
| **Relevant für Seiton** | Split: Dateibaum/Liste + Editor; Markdown; Frontmatter/Metadaten |

**Was gefällt / was übernehmen:**

- **Master-Detail:** Notizliste + geöffnete Datei (bestehendes `/notes`-Layout ausbauen).
- Markdown-Dateien im Vault — Seiton bleibt Obsidian-kompatibel.
- Ordner/Filter in der Liste; später Graph/Backlinks optional (nicht V1).

#### E2. Notion — Seiten-Editor (konzeptionell)

| | |
|---|---|
| **Quelle** | Notion |
| **Relevant für Seiton** | Aufgeräumter Editor-Raum, klare Typografie, wenig Chrome |

**Was gefällt / was übernehmen:**

- **Visuelle Ruhe** und Fokus auf Inhalt — nicht das Block-JSON-Modell.
- Titelzeile + Body klar getrennt (analog „Untitled“ / erste Überschrift).
- Preview/Lesemodus (E30-2) kann Notion-„Page view“ ähneln.

**Preview / Edit (Entwickler, 2026-09-02):**

| Modus | Default | Beschreibung |
|-------|---------|--------------|
| **Tab Edit \| Preview** | ✅ Ja | Umschalter zwischen Markdown-Quelltext und gerenderter Vorschau |
| **Split Live-Preview** | Optional | Wie **Xcode**: Editor links, Vorschau rechts, **live** aktualisiert |
| **Persistenz** | Einstellung | Nutzer wählt Tab-only vs. Split (Preference in Settings oder Editor) |

#### E3. Microsoft Word — feste Toolbar oben (konzeptionell)

| | |
|---|---|
| **Quelle** | Microsoft Word (Ribbon/Toolbar) |
| **Relevant für Seiton** | Immer sichtbare Format-Leiste über dem Editor |

**Was gefällt / was übernehmen:**

- **Fixe Toolbar** am oberen Editor-Rand — Bold, Italic, H1–H3, Liste, Link, Code, …
- Jede Aktion → **Markdown-Markup** im Text (konsistent mit Bereich 3 / C2).
- Kein volles Word-Ribbon mit 50 Tabs — **schlanke** Zeile, Seiton-Dark.

**Preview:** siehe Tabelle oben (Tab default + optional Split live).

---

## Bereich 6 — Einstellungen, Status & System-Feedback

| | |
|---|---|
| **Zweck** | Konfiguration, Instanz-Gesundheit, Backup, Lizenz — an Seiton-Inhalte angepasst |
| **Screens heute** | `/settings` — langes Scroll-Formular, Badges, Backup-Liste |
| **Zielbild** | **Settings-Sidebar** + Detailbereich (Refero); gruppierte Sektionen; Modals für Aktionen |
| **Plattform** | Breite Layouts; Status-Badges + klares Feedback (E30-4-Vorläufer) |
| **Quelle Referenzen** | [Refero](https://refero.design) |

### Deine Referenzen

- [x] Drei Refero-Screenshots + Richtung (2026-09-02)

**Produkt-Richtung (Entwickler):**

| Aspekt | Entscheidung |
|--------|--------------|
| **Layout** | **Linke Settings-Sidebar** (Kategorien) + **Hauptbereich** (Formular/Status) — wie Refero |
| **Inhalte Seiton** | Vault/Provider, Telegram, API/MCP, Backup/Reindex, Lizenz, Kategorien — **nicht** E-Mail-Rules |
| **Mehrstufig** | Bei Bedarf **Liste + Detail** (Org-Pattern) z. B. Backups oder Provider |
| **Modals** | Verbinden/Testen/Speichern in **Fokus-Modal** statt `alert()` |
| **Feedback** | Info-Banner, Toggles, klare Save-Aktion — Seiton-Dark |

#### S1. Rules / Settings — Sidebar + Detailformular

![Settings Sidebar Rules](../ui-references/06-settings/01-rules-settings-sidebar.jpg)

| | |
|---|---|
| **Quelle** | Refero (Rules/Settings) |
| **Relevant für Seiton** | Gruppierte Sidebar-Nav; Detail rechts; Save oben rechts |

**Was gefällt / was übernehmen:**

- **Kategorien in der Sidebar** (Me / Connect / Work → bei Seiton: Vault, Capture, API, Backup, …).
- Detailseite mit **klarem Titel**, großzügigem Formular, **Save**-Aktion fix sichtbar.
- Info-Banner für Hinweise (z. B. „Neustart nötig“ statt Rules-Hinweis).
- Toggle-Zeilen für boolsche Optionen (Embeddings, Telegram, …).

#### S2. Organizations — drei Spalten + Tabs

![Organizations three-pane](../ui-references/06-settings/02-organizations-three-pane.jpg)

| | |
|---|---|
| **Quelle** | Refero (Organizations) |
| **Relevant für Seiton** | Settings-Nav + Listen-Spalte + Detail mit Unter-Tabs |

**Was gefällt / was übernehmen:**

- **Drei Ebenen** wo sinnvoll: Sidebar → Liste (z. B. Backups) → Detail/Tab-Inhalt.
- **Tabs im Detail** (Overview / …) für Unterseiten — z. B. Backup-Liste vs. Restore-Hinweise.
- Nicht überall drei Spalten — nur bei **listenbasierten** Settings (Backups, ggf. Kategorien).

#### S3. Connect account — Modal mit Sektionen

![Connect account modal](../ui-references/06-settings/03-connect-account-modal.jpg)

| | |
|---|---|
| **Quelle** | Refero (Connect account / Custom channel) |
| **Relevant für Seiton** | Modal für „OpenAI testen“, Provider verbinden, strukturierte Gruppen |

**Was gefällt / was übernehmen:**

- **Modal** für fokussierte Flows (Test Key, Telegram testen) — ersetzt blockierende Alerts.
- **Gruppierte Sektionen** mit Überschrift (Incoming/Outgoing → bei Seiton: Provider/Telegram/API).
- Toggles pro Option; Primary/Secondary unten (Back / Connect → Abbrechen / Speichern).
- Provider-Liste (Gmail, …) **nicht** 1:1 — nur Modal-Pattern für Seiton-Integrationen.

---

## Checkliste für den Entwickler

- [ ] App einmal lokal gestartet und alle Screens angesehen (siehe Inventar §9)
- [x] Bereich 1 — Referenzen (Sidebar+Topbar, 2026-09-02)
- [x] Bereich 2 — Referenzen (4 Bilder + Notizen, 2026-09-02)
- [x] Bereich 3 — Referenzen (Capture + Dashboard, 2026-09-02)
- [x] Bereich 4 — Referenzen (Chat-first, Side-Panel, 2026-09-02)
- [x] Bereich 5 — Referenzen (Obsidian/Notion/Word-Toolbar, 2026-09-02)
- [x] Bereich 6 — Referenzen (Refero Settings, 2026-09-02)
- [x] Alle sechs Bereiche befüllt → **E47-2 erledigt** → **E47-3 freigeben**

---

## Für Agents (E47-2 + E47-3)

1. Referenzen: dieses Dokument · Ist: [`ui-inventory.md`](ui-inventory.md)
2. **Designsystem:** [`design-system.md`](design-system.md) — verbindlich
3. Cursor-Rule: `.cursor/rules/ui-design-system.mdc`
4. Token-CSS: E47-4
