# Roadmap

Lebendes Dokument — **was machen wir als Nächstes?**  
Kurzstand für Agents: [`docs/current-state.md`](./docs/current-state.md) ·  
Historie Phasen A–H: [`docs/archive/roadmap-phases-a-h.md`](./docs/archive/roadmap-phases-a-h.md) ·  
Phasen M–O (Detail): [`docs/roadmap-phases-m-o.md`](./docs/roadmap-phases-m-o.md)

Status-Legende: 🟢 Done · 🟡 In Progress · 🔵 Ready · ⚪ Backlog · ⚫ Aufgegangen

---

## Vision (kurz)

Persönliches AI-Second-Brain: Capture (Telegram/UI/API/MCP) → LLM-Klassifikation
→ Markdown im Obsidian-kompatiblen Vault; Retrieve via Suche, RAG (`/ask`), Digest,
REST, MCP. Obsidian = Default-Vault, Telegram = optionaler Eingang.

**Produktstrategie (ADR 0004):** Buy-once, Kunde hostet selbst, BYO-LLM-Key.
UI-first als lokale Web-UI (kein Native-Desktop-Nahziel). Privacy = Verkaufsargument.
n8n-Custom-Node entfällt; REST + `examples/n8n/` für Power-User.

**Deployment (ADR 0008 — normativ):** Self-hosting ist ein **Deployment-Modell**,
nicht die Produktidentität. **Self-hosted zuerst** (V1 / private Beta); eine
**Managed Seiton Cloud** ist Teil der Produktvision, aber später (Phase I / E24,
gated auf ADR 0007) und **kein V1-Blocker**. Der Product Core bleibt
deployment-neutral — Unterschiede nur in Provisionierung, Deployment, Identity,
Billing, Secrets, Backup-Ops, Monitoring, Updates, Support. **Keine
Cloud-Abstraktionen, kein Multi-Tenant-Datenmodell, kein Billing auf Vorrat.**
Isolationsgrenze ist heute die Instanz (nicht irreversibel).

ADRs: [0004](./docs/adr/0004-commercial-consumer-product.md),
[0005](./docs/adr/0005-repo-and-license-strategy.md),
[0006](./docs/adr/0006-consumer-stack-no-sqlite-fork.md),
[**0008**](./docs/adr/0008-deployment-models-self-hosted-first.md).

---

## Phasen

| Phase | Ziel | Status |
|---|---|---|
| **A–F** | MVP → Public → Integrations → Retrieval | 🟢 done — [Archiv](./docs/archive/roadmap-phases-a-h.md) |
| **G — Produktisierung** | UI, Packaging, Lizenz; offen: **E21-2**, E20-3/5 | 🔵 Kern done |
| **H — Capture & Mobile** | UI-Capture, PWA, Templates; Rest-Stories offen | 🔵 Kern done |
| **I — Managed Cloud** | Hosted + Managed LLM. Positionierung geklärt (**ADR 0008**), Betrieb/Abo gated auf **ADR 0007**. **E24** — nach V1.5, kein V1-Blocker | ⚪ |
| **L — Launch-Härtung** | Security, Integrität, Release, UX, Privacy, Designsystem (**E27–E31, E47**) | 🔵 **aktiv** |
| **P — Engineering** | Solo+AI Quality (**E45**) — parallel | 🔵 |
| **Q — Production Ops** | Betrieb nach Release (**E46**) | ⚪ |
| **M / N / O** | Ecosystem · Knowledge AI · Small Teams | ⚪ geplant — [Detail](./docs/roadmap-phases-m-o.md) |
| **E48 — Backup Guardian** | Data Protection (3-2-1) als Produktfähigkeit — nach V1.5 | ⚪ Idee |
| **E49 — Physical Companion** | Reachy Mini als Sprach-Frontend via REST — Beispiel, kein Core | ⚪ Idee |

---

## Offen aus G / H (Rest)

Vollständige Epic-Tabellen inkl. erledigter Stories: [Archiv A–H](./docs/archive/roadmap-phases-a-h.md).

| ID | Story | Status | Hinweis |
|----|-------|--------|---------|
| E15-5 | Notion-Anbindung evaluieren (ADR/Doku zuerst) | ⚪ | H+ |
| E20-3 / E20-5 | Native Desktop-App / Code-Signing | ⚪ | kein Nahziel |
| E21-2 | Verkaufskanal + Lizenz-Ausgabe | ⚪ | vor Monetarisierung; mit E24-4 denken |
| E21-4 | Produktwebsite / Landing Page | ⚪ | **Voraussetzung für E21-2**; bewusst klein, siehe unten |
| E22-5 | E-Mail-Ingestion (IMAP → capture) | ⚪ | nach Phase L; Synergie Beat/E28-1 |
| E22-6 | `/ask`-Antwort als Notiz speichern | ⚪ | |
| E23-3 | Offline-Capture-Queue (PWA) | ⚪ | H+ |
| E23-4 | Share-Target Android + iOS-Shortcuts | ⚪ | Phase M mitdenken |
| E23-5 | Nativer Wrapper (Capacitor) | ⚪ | nur bei Bedarf |
| E25-2 | `seiton doctor` CLI-Subcommand | ⚪ | |
| E25-4 | Dashboard „System-Gesundheit“ | ⚪ | H+; Basis E29-6 |
| E26-3 | KI-Felder in Templates | ⚪ | |
| E26-4 | Template-Editor in Settings | ⚪ | |
| E26-5 | Visueller Template-Builder | ⚪ | H+ |
| E26-6 | Template pro Kategorie | ⚪ | H+ |

**Zu E21-4 (Produktwebsite):** Ohne Seite kein Verkauf — deshalb Story unter E21
und **kein eigenes Epic**; als eigenständiges Projekt geplant verdrängt sie
erfahrungsgemäß Produktarbeit. Scope bewusst klein: **statische** Seite
(Positionierung, Screenshots, Preis, Download/Kauf, Doku-Link, Impressum +
Datenschutz), **kein CMS**, kein Blog-System, keine zweite Anwendung.
**Getrennt vom Product Core** — eigenes Repo/Deployment, nichts davon in `app/`.
Was wir verkaufen, muss die Seite selbst einhalten: keine Third-Party-Tracker,
keine CDN-Fonts, kein Analytics ohne Einwilligung — eine Privacy-Marketingseite,
die Daten abgreift, entwertet das Verkaufsargument. Zeitfenster: vor Beta,
jedenfalls vor E21-2. Ein eigener Abschnitt für **E49** (Reachy Mini) ist dort
später vorgesehen, sobald die Integration existiert.

---

## Phase I — Managed Cloud · E24 · `epic:cloud` · ⚠️ ADR 0007

Die **Positionierung** ist entschieden ([ADR 0008](./docs/adr/0008-deployment-models-self-hosted-first.md)):
Die Cloud gehört zur Produktvision und setzt auf demselben Product Core auf.
Offen bleibt die **Geschäfts-/Betriebsentscheidung** (Abo, Preis, DSGVO-AVV,
Betriebsbereitschaft) — dafür bleibt **E24 gesperrt** bis E24-1. Start frühestens
nach V1.5. Bis dahin wird **nichts** davon vorsorglich gebaut.

| ID | Story | Status |
|----|-------|--------|
| E24-1 | ADR 0007 entscheiden (Betrieb/Abo/Preis/DSGVO; Single-Tenant als Startpunkt) | ⚪ |
| E24-2 | Managed-LLM-Proxy + Quotas | ⚪ |
| E24-3 | Provisioning-Blaupause (EU) | ⚪ |
| E24-4 | Abo-Billing + Entitlements (mit E21-2) | ⚪ |
| E24-5 | DSGVO-Paket (AVV, Export, Löschung, Region) | ⚪ |

---

## Phase L — Launch-Härtung

Audit: [`docs/audit-2026-08-product-readiness.md`](./docs/audit-2026-08-product-readiness.md) — **GO WITH CONDITIONS**. Vor E21-2 / E24.

### E27 — Security · `epic:security`

| ID | Story | Status |
|----|-------|--------|
| E27-1 | P0 Proxy-sichere Zugriffskontrolle (`/setup`, Forwarded-Header) | 🟢 |
| E27-2 | XSS-Fix Dashboard/Login/Setup + Regression | 🟢 |
| E27-3 | Sichere Remote-Defaults (Cookie Secure, Bind 127.0.0.1, Logout POST) | 🟢 |
| E27-4 | Frontmatter-/Pfad-Härtung | 🟢 |
| E27-5 | **Rate-Limits & Brute-Force** (Login, `/v1`, LLM; Redis-Lockout; timing-safe Webhook) | ⚪ |

### E28 — Datenintegrität · `epic:data-integrity`

| ID | Story | Status |
|----|-------|--------|
| E28-1 | Inkrementeller Index-Sync + Celery Beat + Reindex-Button | 🟢 |
| E28-2 | File-Locks Create/Append | 🟢 |
| E28-3 | Capture-Kompensation (Orphan-Cleanup) | 🟢 |
| E28-4 | **Idempotency-Key** REST/UI-Capture | ⚪ |
| E28-5 | Retry-/Status-Semantik (`failed`, nur transiente Retries) | 🟢 |

### E29 — Release & Ops · `epic:release-ops`

| ID | Story | Status |
|----|-------|--------|
| E29-1 | Dependencies pinnen + Dependabot / pip-audit | 🟢 |
| E29-2 | CI: Docker-Build + Alembic + pgvector-Smoke | 🟢 |
| E29-3 | Release v0.3.0 + Release-Doku | 🟢 |
| E29-4 | **Backup-Retention + Restore-Verifikation** | ⚪ |
| E29-5 | **Doku-Sync** README + ARCHITECTURE.md + KIND/STATUS | ⚪ |
| E29-6 | **Betriebs-Robustheit** Log-Rotation, Health-Erweiterung | ⚪ |

### E30 — UX Consumer-Pass · `epic:ux-polish`

Reihenfolge offen: E30-4 → E30-2 → E30-5 → E30-6 → E30-7 → E30-8 (nach **E47**).

| ID | Story | Status |
|----|-------|--------|
| E30-1 | Klickbare Suchtreffer/Quellen → `/notes?path=` | 🟢 |
| E30-2 | **Notiz-Lesemodus** (Markdown-Preview, Wikilinks, Save-Feedback) | ⚪ |
| E30-3 | Post-Setup-Onboarding | 🟢 |
| E30-4 | **Feedback-Layer** (Toasts/Modals, DE-Fehlertexte, Undo) | ⚪ |
| E30-5 | Terminologie- & Status-Pass + Empty-States | ⚪ |
| E30-6 | Mobile-Politur / A11y-AA-Basis | ⚪ |
| E30-7 | Ask-Verlauf persistieren | ⚪ |
| E30-8 | Integrations-Karte in Settings | ⚪ |

### E31 — Privacy/DSGVO · `epic:privacy`

| ID | Story | Status |
|----|-------|--------|
| E31-1 | **Voll-Löschung** (Settings + CLI) | ⚪ |
| E31-2 | Strukturierter Export (JSON/ZIP) | ⚪ |
| E31-3 | **Log- & Retention-Hygiene** | ⚪ |
| E31-4 | Datenfluss-Doku `docs/privacy.md` | ⚪ |

### E45 — Solo-Developer Engineering · `epic:engineering`

Zielbild: [`docs/engineering.md`](./docs/engineering.md). Budget: keine neuen laufenden Kosten bis 31.10.2026.

| ID | Story | Status | Zeitfenster |
|----|-------|--------|-------------|
| E45-1 | Branch Protection `main` (PR + required CI) | 🟢 | jetzt |
| E45-2 | Solo-Workflow in engineering.md + ADR-Lesen vor großen Änderungen | 🟡 | jetzt |
| E45-3 | Issue-Templates: Acceptance Criteria | ⚪ | jetzt |
| E45-4 | GitHub Security Rest (Dependabot Security Updates, optional CodeQL) | 🟢 | jetzt |
| E45-5 | CodeRabbit evaluieren (OSS-Plan) | 🟢 | `.coderabbit.yaml`; manueller Trigger bis ≥10 Stars |
| E45-6 | Typ-Checking schrittweise (mypy/pyright) | ⚪ | später |
| E45-7 | CI Integration-Smoke (Redis/API) | ⚪ | später |
| E45-8 | Staging-Strategie (manuell; Preview erst E24) | ⚪ | vor Release |
| E45-9 | Production Monitoring (eine Lösung, Free) | ⚪ | vor Verkauf |
| E45-10 | Product Analytics evaluieren | ⚪ | Beta/Launch |
| E45-11 | Linear evaluieren | ⚪ | zurückgestellt |
| E45-12 | Dependabot-Prozess / Merge-Policy | 🟡 | jetzt |
| E45-13 | **Roadmap-/Agent-Kontext-Hygiene** (Archiv, current-state, Cursor-Rule) | 🟢 | — |
| E45-14 | Risikobasierte Definition of Done + Mini-Handcheck | 🟢 | Matrix in `docs/engineering.md`; CONTRIBUTING + PR-Template |
| E45-15 | Visual-Smoke-PoC (`pytest-playwright`, ein Happy-Path) | 🟢 | opt-in `SEITON_VISUAL=1`; Screenshots in `docs/ui-screenshots/` |

### E46 — Production Operations · `epic:production-ops`

Runbooks: [`docs/production-ops.md`](./docs/production-ops.md). Gates: vor Beta / Launch / Verkauf.

| ID | Story | Status | Zeitfenster |
|----|-------|--------|-------------|
| E46-1 | Release- & Update-Prozess dokumentieren | 🟡 | vor Beta |
| E46-2 | Hotfix-Prozess | ⚪ | vor Launch |
| E46-3 | Monitoring & Alerting (Minimum) | ⚪ | vor öff. Launch |
| E46-4 | Incident Management (Solo-Runbook) | ⚪ | vor Launch |
| E46-5 | Rollback & Recovery | ⚪ | vor Launch |
| E46-6 | Backup & Restore-Verifikation | ⚪ | vor E21-2 |
| E46-7 | Sicherer DB-Migrations-Prozess | ⚪ | vor Launch |
| E46-8 | Security-/Dependency-Wartung (Cadence) | 🟡 | laufend |
| E46-9 | Production-Bug-Flow | ⚪ | vor Beta |
| E46-10 | Post-Incident Learning | ⚪ | vor Launch |

### E47 — Designsystem & UI/UX · `epic:design-system`

Vor E30-2/4/5. Referenzen in [`docs/ui-reference-request.md`](docs/ui-reference-request.md) — **E47-2 🟢**.

| ID | Story | Status |
|----|-------|--------|
| E47-1 | UI-Inventar & Ist-Aufnahme → `docs/ui-inventory.md` | 🟢 |
| E47-2 | **STOP — UI-Referenzen vom Entwickler** (~6 Bereiche) | 🟢 |
| E47-3 | Designsystem ableiten → `docs/design-system.md` + Cursor-Rule | 🟢 |
| E47-4 | Token-Angleichung `app.css` / `setup.css` (schrittweise) | ⚪ |
| E47-5 | Design-Reifegrad vor E21-2 | ⚪ |

### Bewusst NICHT (Auswahl)

Breites E2E-Netz · Desktop-UI-Testing · Linear/CodeRabbit/Analytics paid vor Nov 2026 ·
zwei Monitoring-Tools · 100 %-Coverage · Scrum · Feature-Flags als Self-Host-Standard ·
React/Tailwind-Migration (Neubewertung bei E40). Details: Audit + `docs/engineering.md`.

**Produkt/Deployment (ADR 0008):** allgemeiner Dateisync mit bidirektionaler
Konfliktauflösung · eigene APIs für Storage-Anbieter statt etablierter
Backup-Backends · eigene Backup-Kryptografie · Local Agent für Cloud→USB ·
Kubernetes, Multi-Tenant-Datenmodell, Billing oder Cloud-Provisionierung auf Vorrat.

---

## Phasen M / N / O (Kurz)

Vollständige Stories: [`docs/roadmap-phases-m-o.md`](./docs/roadmap-phases-m-o.md).

| Phase | Epics | Start |
|-------|-------|-------|
| **M** Ecosystem | E32 Vault-Interop · E33 Universal Capture · E34 Git-Backup · E35 Automation · E36 AI-Access | nach Phase-L-Kern |
| **N** Knowledge AI | E37 Retrieval (Hybrid/RRF) · E38 `ai_access` · E39 Local AI · E40 Knowledge Chat | nach M-Fundament |
| **O** Small Teams | E41 Identity · E42 Rollen · E43 Team-Gedächtnis · E44 Team-AI | nach N-Kern; Shared Instance |

---

## E48 — Backup Guardian (Data Protection) · `epic:backup` · ⚪ Idee

**Start: nach V1.5.** Nicht in V1, kein Beta-Blocker. Bewusst **ein** Epic-Eintrag
ohne Story-Aufteilung — detailliert wird erst, wenn es dran ist.

**Ziel:** Nutzer sollen ihre persönlichen Wissensdaten zuverlässig sichern können,
orientiert an **3-2-1** (mehrere Kopien · unterschiedliche Medien/Ziele ·
mindestens ein Offsite-Ziel).

**Backup ist nicht Sync.** Seiton wird **kein** allgemeiner Dateisynchronisations-
dienst und baut keine bidirektionale Konfliktauflösung zwischen Drive/Dropbox/NAS/
iCloud. Backup heißt: historische Zustände, Wiederherstellbarkeit,
Integritätsprüfung — nicht Spiegelung des aktuellen Zustands.

```
definierte Seiton-/Vault-Daten
           │
           ├── versioniertes Backup → Ziel A
           ├── versioniertes Backup → Ziel B
           └── versioniertes Backup → Offsite
```

**Mögliche Fähigkeiten (self-hosted):** lokaler Pfad, externe Festplatte,
NAS/Network Mount, SFTP, S3-kompatibler Object Storage. **Build vs. Buy ist die
erste offene Frage** — etablierte Backends (restic, rclone, borg o. Ä.) statt
eigener Storage-APIs und **keine eigene Kryptografie**; Offsite-/Cloud-Ziele
sollen verschlüsselt sein, sodass der Ziel-Anbieter den Klartext nicht braucht.
Heute wird **keine Dependency** hinzugefügt.

**Backup Health** als sichtbare Fähigkeit: letztes erfolgreiches Backup je Ziel,
Backup-Alter, offline/fehlendes Ziel, Integritätsprüfung, 3-2-1-Status,
Restore-Verifikation, Erinnerung an eine wieder anzuschließende Offline-Platte.
**Restore gehört dazu** — ein Backup gilt nicht als gesund, nur weil Dateien
geschrieben wurden.

**Managed Cloud (viel später):** Betriebsverantwortung bei uns — automatisierte
verschlüsselte Backups, versionierte Snapshots, Restore, optionaler Export auf
kundeneigene Ziele. Ein lokales USB-/NAS-Ziel ist aus der Cloud **nicht**
erreichbar; ein optionaler Local Agent wird heute **nicht** geplant.

**Baut auf vorhandenen Stories auf — ersetzt sie nicht:** E29-4
(Backup-Retention + Restore-Verifikation), E46-6 (Backup & Restore-Verifikation),
E34-3 (Offsite-Rezept), E31-2 (Export). Diese bleiben die V1-Grundlage; E48
verallgemeinert sie später zu mehreren Zielen mit Health-Sicht. **Keine zweite
parallele Backup-Strategie anlegen.**

**Monetarisierung: Hypothese, nicht entschieden.** Self-hosted mit eigenen Zielen ·
Cloud mit Backup als Teil des Betriebs · optional Managed Offsite Storage. Heute
**keine** Preis- oder Free/Premium-Grenze — und die Architektur wird nicht
künstlich verschlechtert, um ein Premium-Feature zu erzeugen.

---

## E49 — Physical Companion (Reachy Mini) · `epic:companion` · ⚪ Idee

**Start: frühestens nach V1.5, und nur mit Hardware vor Ort.** Kein V1-Thema,
kein Beta-Blocker, kein Verkaufsversprechen.

[Reachy Mini](https://huggingface.co/docs/reachy_mini/main/index) (Pollen
Robotics / Hugging Face) ist ein Desktop-Roboter mit 4er-Mikrofonarray,
Lautsprecher, Kamera und expressiver Bewegung. SDK Apache-2.0, Python + JS/WebRTC,
lokaler REST/WebSocket-Daemon. Wireless-Variante rechnet auf einem RPi CM4 an
Bord, Lite hängt am PC.

**Die Idee:** Der Roboter ist ein **Ein-/Ausgabekanal**, kein neuer Baustein im
Product Core. Sprache rein → `POST /v1/capture`, Frage → `/v1/ask`, Antwort
gesprochen zurück, Bewegung als Statusfeedback (nickt beim Erfassen, schaut
suchend beim Retrieval). Damit ist es exakt das Muster aus ADR 0004 —
**REST + Beispielordner statt Integration im Core**, wie `examples/mcp/` und
`examples/n8n/`. Erwartete Form: `examples/reachy-mini/` mit einem REST-Client;
STT/TTS/Wake-Word bleiben auf der Roboterseite.

**Grenzen (jetzt schon festgehalten):** keine `reachy-mini`-Dependency in
`requirements.txt` · kein Robotik-/Realtime-Stack im Core · keine
Hardware in CI · kein Always-On-Mikrofon oder -Kamera als Default (Kamera-Feed
verlässt die Instanz nie, Aktivierung explizit) · keine Abhängigkeit von
Hugging-Face-Spaces-Hosting · Support-Status = Beispiel/Community, nicht
Produktfeature.

**Anschlussfähig, ohne heute etwas zu bauen:** ein Gerät im Raum ist ein
**Kanal mit eigener Trust-Klasse** — genau die zweite Dimension aus **E38-3**
(wie Telegram = `external`); Provenance über **E33-1** (`source`/`actor`);
Sprache rein über **E33-4** (Binär-Capture via REST, ohnehin für PWA und
iOS-Shortcut nötig); gesprochene Fragen sind derselbe Answer-Pfad wie **E40**
(read-only). Solange diese Stories sauber gebaut werden, kostet E49 **null
zusätzlichen Core-Code**.

**Kein TTS im Core.** Sprachausgabe bleibt Sache des Clients — der Roboter
bringt eigenes TTS mit, und ein Sprachsynthese-Stack im Product Core hätte ohne
das Gerät keinen Nutzen. Falls Vorlesen später breiter gewünscht wird, ist die
Web-Speech-API im Browser der erste Kandidat, nicht eine Server-Dependency.

---

## Nächste Arbeitspakete (≈ 1 Tag)

Stand 2026-08-30. Engineering unterbricht Produktarbeit gezielt.
Produkt-/Deployment-Konsolidierung ist abgeschlossen (ADR 0008) — **keine weitere
Meta-Planung**; ab hier wieder ein Paket pro Tag: Branch → Code → Tests → PR → Merge.

| # | Paket | Warum jetzt |
|---|-------|-------------|
| 1 | **E31-3 (+ E31-1)** Log-Hygiene / Voll-Löschung | Puffer ohne UI-Abhängigkeit |
| 2 | **E47-4** Token-Angleichung `app.css` / `setup.css` | nach Designsystem |
| 3 | **E30-4 → E30-2 → E30-5/6** | UX auf gemeinsamer Sprache |

Erledigt: ~~E45-13~~ · ~~E45-1/4~~ · ~~E45-5~~ · ~~E45-14~~ · ~~E45-15~~ · ~~E47-1~~ · ~~E47-2~~ · ~~E47-3~~ Designsystem.

Danach: E29-4/5/6, E27-5, E46 vor E21-2, dann Phase M → N → O; parallel E21-2.
**Nicht** in dieser Reihe: E24 (Managed Cloud, nach V1.5 und nach E24-1), E48
(Backup Guardian, nach V1.5) und E49 (Physical Companion, nur mit Hardware).

---

## Definition of Done (pro Story) · E45-14

Gates hängen am **Change-Typ** (Doku · Backend/API · UI · Migration · Security).
Vollständige Matrix + Mini-Handcheck-Beispiel:
[`docs/engineering.md`](./docs/engineering.md) (Abschnitt „Definition of Done").

**Immer:** Acceptance Criteria · `ruff` · `pytest` · CI · CHANGELOG/ROADMAP bei
Story-Abschluss.

**Zusätzlich nach Typ:** neue Tests (Backend/UI/Migration/Security) · Visual-Smoke
bei UI-Shell-Änderungen (opt-in, kein CI-Gate) · **Mini-Handcheck** (3 konkrete
Schritte in der PR) bei UI, Security, Migration und sichtbarem Backend-Verhalten ·
CodeRabbit bei Code-PRs (beratend) · ADR erwägen bei Architektur-/Schemawirkung.

**Chore / reine Doku:** kein Handcheck.
