# Roadmap

Lebendes Dokument — **was machen wir als Nächstes?**  
Kurzstand für Agents: [`docs/current-state.md`](./docs/current-state.md) ·  
Historie Phasen A–H: [`docs/archive/roadmap-phases-a-h.md`](./docs/archive/roadmap-phases-a-h.md) ·  
Phasen M–O (Detail): [`docs/roadmap-phases-m-o.md`](./docs/roadmap-phases-m-o.md)

Status-Legende: 🟢 Done · 🟡 In Progress · 🔵 Ready · ⚪ Backlog · ⚫ Aufgegangen

---

## Vision (kurz)

Self-hosted Second-Brain-Engine: Capture (Telegram/UI/API/MCP) → LLM-Klassifikation
→ Markdown im Obsidian-kompatiblen Vault; Retrieve via Suche, RAG (`/ask`), Digest,
REST, MCP. Obsidian = Default-Vault, Telegram = optionaler Eingang.

**Produktstrategie (ADR 0004):** Buy-once, Kunde hostet selbst, BYO-LLM-Key.
UI-first als lokale Web-UI (kein Native-Desktop-Nahziel). Privacy = Verkaufsargument.
n8n-Custom-Node entfällt; REST + `examples/n8n/` für Power-User.
ADRs: [0004](./docs/adr/0004-commercial-consumer-product.md),
[0005](./docs/adr/0005-repo-and-license-strategy.md),
[0006](./docs/adr/0006-consumer-stack-no-sqlite-fork.md).

---

## Phasen

| Phase | Ziel | Status |
|---|---|---|
| **A–F** | MVP → Public → Integrations → Retrieval | 🟢 done — [Archiv](./docs/archive/roadmap-phases-a-h.md) |
| **G — Produktisierung** | UI, Packaging, Lizenz; offen: **E21-2**, E20-3/5 | 🔵 Kern done |
| **H — Capture & Mobile** | UI-Capture, PWA, Templates; Rest-Stories offen | 🔵 Kern done |
| **I — Cloud-Edition** | Hosted + Managed LLM (Abo). Gated **ADR 0007**. **E24** | ⚪ |
| **L — Launch-Härtung** | Security, Integrität, Release, UX, Privacy, Designsystem (**E27–E31, E47**) | 🔵 **aktiv** |
| **P — Engineering** | Solo+AI Quality (**E45**) — parallel | 🔵 |
| **Q — Production Ops** | Betrieb nach Release (**E46**) | ⚪ |
| **M / N / O** | Ecosystem · Knowledge AI · Small Teams | ⚪ geplant — [Detail](./docs/roadmap-phases-m-o.md) |

---

## Offen aus G / H (Rest)

Vollständige Epic-Tabellen inkl. erledigter Stories: [Archiv A–H](./docs/archive/roadmap-phases-a-h.md).

| ID | Story | Status | Hinweis |
|----|-------|--------|---------|
| E15-5 | Notion-Anbindung evaluieren (ADR/Doku zuerst) | ⚪ | H+ |
| E20-3 / E20-5 | Native Desktop-App / Code-Signing | ⚪ | kein Nahziel |
| E21-2 | Verkaufskanal + Lizenz-Ausgabe | ⚪ | vor Monetarisierung; mit E24-4 denken |
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

---

## Phase I — Cloud-Edition · E24 · `epic:cloud` · ⚠️ ADR 0007

| ID | Story | Status |
|----|-------|--------|
| E24-1 | ADR 0007 entscheiden (Single-/Multi-Tenant, Preis, DSGVO) | ⚪ |
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
| E45-1 | Branch Protection `main` (PR + required CI) | ⚪ | jetzt |
| E45-2 | Solo-Workflow in engineering.md + ADR-Lesen vor großen Änderungen | 🟡 | jetzt |
| E45-3 | Issue-Templates: Acceptance Criteria | ⚪ | jetzt |
| E45-4 | GitHub Security Rest (Dependabot Security Updates, optional CodeQL) | ⚪ | jetzt |
| E45-5 | CodeRabbit evaluieren (OSS-Plan) | ⚪ | nach E45-1 |
| E45-6 | Typ-Checking schrittweise (mypy/pyright) | ⚪ | später |
| E45-7 | CI Integration-Smoke (Redis/API) | ⚪ | später |
| E45-8 | Staging-Strategie (manuell; Preview erst E24) | ⚪ | vor Release |
| E45-9 | Production Monitoring (eine Lösung, Free) | ⚪ | vor Verkauf |
| E45-10 | Product Analytics evaluieren | ⚪ | Beta/Launch |
| E45-11 | Linear evaluieren | ⚪ | zurückgestellt |
| E45-12 | Dependabot-Prozess / Merge-Policy | 🟡 | jetzt |
| E45-13 | **Roadmap-/Agent-Kontext-Hygiene** (Archiv, current-state, Cursor-Rule) | 🟢 | — |
| E45-14 | Risikobasierte Definition of Done + Mini-Handcheck | ⚪ | nach E45-15 |
| E45-15 | Visual-Smoke-PoC (`pytest-playwright`, ein Happy-Path) | ⚪ | nach E47-2 |

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

Vor E30-2/4/5. **E47-2 = STOP** — kein Agent wählt Stil ohne Entwickler-Referenzen.

| ID | Story | Status |
|----|-------|--------|
| E47-1 | UI-Inventar & Ist-Aufnahme → `docs/ui-inventory.md` | ⚪ |
| E47-2 | **STOP — UI-Referenzen vom Entwickler** (~6 Bereiche) | ⚪ |
| E47-3 | Designsystem ableiten → `docs/design-system.md` + Cursor-Rule | ⚪ |
| E47-4 | Token-Angleichung `app.css` / `setup.css` (schrittweise) | ⚪ |
| E47-5 | Design-Reifegrad vor E21-2 | ⚪ |

### Bewusst NICHT (Auswahl)

Breites E2E-Netz · Desktop-UI-Testing · Linear/CodeRabbit/Analytics paid vor Nov 2026 ·
zwei Monitoring-Tools · 100 %-Coverage · Scrum · Feature-Flags als Self-Host-Standard ·
React/Tailwind-Migration (Neubewertung bei E40). Details: Audit + `docs/engineering.md`.

---

## Phasen M / N / O (Kurz)

Vollständige Stories: [`docs/roadmap-phases-m-o.md`](./docs/roadmap-phases-m-o.md).

| Phase | Epics | Start |
|-------|-------|-------|
| **M** Ecosystem | E32 Vault-Interop · E33 Universal Capture · E34 Git-Backup · E35 Automation · E36 AI-Access | nach Phase-L-Kern |
| **N** Knowledge AI | E37 Retrieval (Hybrid/RRF) · E38 `ai_access` · E39 Local AI · E40 Knowledge Chat | nach M-Fundament |
| **O** Small Teams | E41 Identity · E42 Rollen · E43 Team-Gedächtnis · E44 Team-AI | nach N-Kern; Shared Instance |

---

## Nächste Arbeitspakete (≈ 1 Tag)

Stand 2026-08-29. Engineering unterbricht Produktarbeit gezielt.

| # | Paket | Warum jetzt |
|---|-------|-------------|
| 1 | ~~**E45-13**~~ Roadmap-Hygiene | 🟢 erledigt |
| 2 | **E45-1 + E45-4** Branch Protection + GitHub-Security-Rest | `main` ungeschützt; Secret Scanning schon aktiv |
| 3 | **E45-5** CodeRabbit (OSS, kostenlos) | braucht PR-Pflicht aus #2 |
| 4 | **E47-1 + E47-2** UI-Inventar + **STOP: Referenzen** | vor E30-2/4/5; asynchrone Input-Sammlung |
| 5 | **E45-15** Visual-Smoke-PoC | parallel zu Referenz-Sammlung |
| 6 | **E45-14** Risikobasierte DoD | nach Smoke-Klarheit |
| 7 | **E31-3 (+ E31-1)** Log-Hygiene / Voll-Löschung | Puffer ohne UI-Abhängigkeit |
| 8 | **E47-3** Designsystem ableiten | sobald Referenzen da |
| 9 | **E30-4 → E30-2 → E30-5/6** | UX auf gemeinsamer Sprache |

Danach: E29-4/5/6, E27-5, E46 vor E21-2, dann Phase M → N → O; parallel E24-1 / E21-2.

---

## Definition of Done (pro Story)

- [ ] Code-Änderung klein und fokussiert
- [ ] Tests vorhanden (oder bewusste Begründung warum nicht)
- [ ] `ruff check` und `pytest` grün
- [ ] CHANGELOG-Eintrag unter `[Unreleased]`
- [ ] ROADMAP-Status aktualisiert
- [ ] Manuell getestet, wenn sich sichtbares Verhalten ändert (Telegram → Vault, UI, API)

Risikobasierte DoD (Gates je Change-Typ + Mini-Handcheck): **E45-14**.
