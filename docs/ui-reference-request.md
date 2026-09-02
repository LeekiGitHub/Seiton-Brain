# UI-Referenz-Anfrage — STOP (E47-2)

**Status: ⛔ STOP — wartet auf Input vom Entwickler**

Bis die sechs Bereiche unten mit Referenzen befüllt sind, gilt:

- **Kein** eigenmächtiges Redesign durch Agents oder CI-Tools
- **Kein** `docs/design-system.md` (E47-3)
- **Keine** Token-Umstellung in `app.css` / `setup.css` (E47-4)
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
| **Zweck** | Orientierung zwischen Dashboard, Suche, Notizen, Einstellungen; Vertrauen („lokale Instanz") |
| **Screens heute** | `base.html` — Topnav, Brand, aktiver Link, Logout |
| **Elemente** | Horizontale Nav, Seitenbreite (920/1100px), PWA-Titelzeile |
| **Interaktionen** | Aktiver Zustand, Logout, Setup-Link bei incomplete |
| **Plattform** | Desktop-Browser primär; PWA `standalone` ohne eigene Tab-Bar |
| **Suchbegriffe** | `settings app navigation`, `dark sidebar minimal`, `knowledge base nav`, `PWA shell` |

### Deine Referenzen

- [ ] *(noch offen)*

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

- [x] Sieben Referenzen abgelegt unter `docs/ui-references/03-capture-dashboard/` — **Notizen ausstehend**
- **Richtung (Entwickler):** Schnellnotizen/Capture sollen per **Button** (oder Shortcut) getriggert werden können — nicht nur als feste Textarea auf dem Dashboard.

### Capture (Quick Note / Erfassen)

#### C1. Refero — schwebendes Quick-Note-Fenster

![Refero Quick Note Modal](../ui-references/03-capture-dashboard/capture/01-refero-quick-note-modal.jpg)

| | |
|---|---|
| **Quelle** | Refero |
| **Relevant für Seiton** | Modal über abgedunkeltem Hintergrund; „Untitled note“, minimaler Editor |

**Was gefällt / was übernehmen:** *(ausstehend)*

#### C2. HR/Refero — Note-Modal mit Toolbar

![Note mit Toolbar](../ui-references/03-capture-dashboard/capture/02-note-editor-toolbar.jpg)

| | |
|---|---|
| **Quelle** | Refero (HR-Kontext) |
| **Relevant für Seiton** | Richer Capture mit Formatierung; „Changes saved“; Privat-Hinweis |

**Was gefällt / was übernehmen:** *(ausstehend)*

#### C3. Create Tag — Keywords für KI

![Create tag Keywords](../ui-references/03-capture-dashboard/capture/03-create-tag-keywords.jpg)

| | |
|---|---|
| **Quelle** | Refero |
| **Relevant für Seiton** | Tags/Keywords beim Erfassen oder kurz danach; KI-Auto-Tagging |

**Was gefällt / was übernehmen:** *(ausstehend)*

#### C4. Task — Dateien nach Typ filtern

![Files in task](../ui-references/03-capture-dashboard/capture/04-task-files-filter.jpg)

| | |
|---|---|
| **Quelle** | Refero (Task-Kontext) |
| **Relevant für Seiton** | Anhänge/Links/Docs gebündelt; Filter-Pills; leerer Zustand |

**Was gefällt / was übernehmen:** *(ausstehend)*

### Dashboard (Übersicht & Aktivität)

#### D1. Refero Supercuts — Sidebar + Metriken

![Supercuts Dashboard](../ui-references/03-capture-dashboard/dashboard/01-refero-supercuts-analytics.jpg)

| | |
|---|---|
| **Quelle** | Refero / Supercuts |
| **Relevant für Seiton** | Linke Sidebar, KPI-Zeile, Tabellen/Charts, leere Zustände, Primary CTA oben |

**Was gefällt / was übernehmen:** *(ausstehend)*

#### D2. Anam — Sessions-Analytics

![Anam Sessions](../ui-references/03-capture-dashboard/dashboard/02-anam-sessions-dashboard.jpg)

| | |
|---|---|
| **Quelle** | Anam |
| **Relevant für Seiton** | KPI-Karten, Performance-Zeile, Aktivitäts-Charts, kompakte Sidebar |

**Was gefällt / was übernehmen:** *(ausstehend)*

#### D3. Twitch — Creator Discovery Dashboard

![Twitch Discovery](../ui-references/03-capture-dashboard/dashboard/03-twitch-discovery-analytics.jpg)

| | |
|---|---|
| **Quelle** | Twitch Creator Dashboard |
| **Relevant für Seiton** | Breite Sidebar-Navigation, Karten-Grid, Zeitraum-Filter, Empty States mit Icon |

**Was gefällt / was übernehmen:** *(ausstehend)*


| | |
|---|---|
| **Zweck** | Wissen wiederfinden — Stichwort, semantisch, Frage-Antwort, Themensynthese |
| **Screens heute** | `/ask` — Suchformular, Trefferliste, Digest, Chat-Log |
| **Elemente** | Search hits, Chat-Bubbles (user/assistant), Ladezustand, Quellenliste |
| **Interaktionen** | Semantik-Toggle, Digest-Zeitraum, scrollendes Chat-Log |
| **Plattform** | Chat muss auf schmalen Viewports lesbar sein (E40-Vorläufer) |
| **Suchbegriffe** | `AI chat sources`, `search results list dark`, `RAG citations UI`, `knowledge digest` |

### Deine Referenzen

- [ ] *(noch offen)*

---

## Bereich 5 — Notizen-Editor (Master-Detail)

| | |
|---|---|
| **Zweck** | Vault-Notizen durchsuchen, Markdown bearbeiten, löschen |
| **Screens heute** | `/notes` — Filter, Liste links, Editor rechts (stapelt mobil) |
| **Elemente** | Filterzeile, klickbare Liste, Monospace-Editor, Speichern/Löschen |
| **Interaktionen** | Auswahl, Dirty-State, Confirm beim Verwerfen/Löschen |
| **Plattform** | Zwei-Spalten desktop; eine Spalte &lt;800px — Vorbild für E30-2 Lesemodus |
| **Suchbegriffe** | `split view notes`, `markdown editor dark`, `file list sidebar`, `obsidian-like web` |

### Deine Referenzen

- [ ] *(noch offen)*

---

## Bereich 6 — Einstellungen, Status & System-Feedback

| | |
|---|---|
| **Zweck** | Konfiguration, Gesundheit der Instanz, Backup, Lizenz — ohne CLI |
| **Screens heute** | `/settings` — langes Formular, Badges, Backup-Liste, Reindex |
| **Elemente** | Status-Badges, Passwort-Felder, `.result` ok/err, `<details>` Restore-Befehle |
| **Interaktionen** | Test-Buttons, Speichern, Backup/Reindex mit Warte-Feedback |
| **Plattform** | Breite Formulare; Vorbild für künftige Toasts/Modals (E30-4) |
| **Suchbegriffe** | `settings page dark`, `system status badges`, `backup list UI`, `toast notification dark` |

### Deine Referenzen

- [ ] *(noch offen)*

---

## Checkliste für den Entwickler

- [ ] App einmal lokal gestartet und alle Screens angesehen (siehe Inventar §9)
- [ ] Bereich 1 — Referenzen
- [x] Bereich 2 — Referenzen (4 Bilder + Notizen, 2026-09-02)
- [ ] Bereich 3 — Referenzen
- [ ] Bereich 4 — Referenzen
- [ ] Bereich 5 — Referenzen
- [ ] Bereich 6 — Referenzen
- [ ] PR oder Commit mit ausgefüllten Referenzen → **E47-2 erledigt** → E47-3 freigeben

---

## Für Agents (nach Befüllung)

Wenn alle Checkboxen oben erledigt sind:

1. Status-Zeile oben auf **✅ Input vorhanden** ändern
2. ROADMAP E47-2 auf 🟢 setzen
3. E47-3 starten: `docs/design-system.md` aus Referenzen + Inventar ableiten
4. Cursor-Rule aktualisieren (Verweis auf `design-system.md`)
