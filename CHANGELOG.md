# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt landen hier.

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased]

### Added
- **Epic E46 Production Operations & Maintenance.** Lebenszyklus nach Release
  (Releases, Hotfixes, Monitoring, Incidents, Rollback, Backups, Migrationen,
  Wartung) in [`docs/production-ops.md`](docs/production-ops.md); Phase Q in
  [`ROADMAP.md`](ROADMAP.md).
- **Epic E45 Solo-Developer Engineering (AI-Safe).** Ist-Analyse, Zielworkflow
  und kostenbewusste Tool-Roadmap in [`docs/engineering.md`](docs/engineering.md);
  Stories E45-1–E45-12 in [`ROADMAP.md`](ROADMAP.md) (parallel zu Phase L).
- **E30-3 Post-Setup-Onboarding.** Abschluss-Screen mit Neustart-Checkliste und
  CTA „Erste Notiz erfassen“ (`/dashboard#capture-card`); Setup-Link in der
  Nav nur bei unvollständiger Konfiguration; lesbare Formular-Labels im Wizard
  und Settings (statt Env-Namen).

---

## [0.3.0] — 2026-08-27 — Phase G–L Kern: Consumer, Knowledge, Launch-Härtung

Erster Release-Schnitt seit 0.2.0: Packaging/Web-UI, Retrieval/RAG, Offline-
Lizenz, Security-/Integritäts-Fixes und Ops-Grundlage (CI + Release-Prozess).
Siehe [`docs/release.md`](docs/release.md).

### Added
- **E29-2 CI-Härtung.** Docker-Build-Job; Alembic `upgrade head` gegen
  Service-Container `pgvector/pgvector:pg16`; Smoke-Insert/kNN über
  `scripts/ci_vector_smoke.py`.
- **E29-3 Release-Prozess.** Leichte Checkliste in `docs/release.md`
  (CHANGELOG schneiden → Tag → GitHub Release).
- **E28-1 Inkrementeller Index-Sync.** mtime-basierter Sync (periodischer
  Celery-Beat-Task, Intervall via `SEITON_INDEX_SYNC_INTERVAL_SECONDS`);
  Compose-Service `beat`; Settings-Button „Neu indexieren“
  (`POST /api/ui/reindex`). Obsidian-/Fremd-Edits landen damit im Such-/RAG-
  Index ohne Full-Rescan bei jedem Tick.
- **E30-1 Klickbare Suchtreffer/Quellen.** Suche, Ask- und Digest-Quellen
  verlinken auf `/notes?path=…`; die Notiz-Seite öffnet den Deep-Link und
  hält die URL beim Auswählen synchron.

### Fixed
- **E28-2/E28-3 Capture-Konsistenz.** `flock` bei Create/Append gegen Lost
  Updates; bei `telegram_update_id` UNIQUE-Claim per `flush` *vor* Vault-Write;
  neu angelegte Dateien werden bei DB-Fehler wieder gelöscht (keine Orphans).

### Security
- **Dependabot gebündelt.** Wöchentliche Updates als wenige Gruppen-PRs
  (Patch/Minor zusammen); Major-Updates einzeln; `ruff>=0.16` ignoriert
  (bewusst auf 0.15.x gepinnt wegen neuer Lint-Regeln).
- **E29-1 Dependency-Pins + Supply-Chain.** `requirements.txt`/`requirements-dev.txt`
  und MCP-Requirements mit exakten Versionen; Dependabot (pip + Actions);
  `pip-audit` in CI; Dockerfile auf `python:3.14-slim-bookworm`.
- **E28-5 Retry-/Status-Semantik.** Celery retryt nur noch wirklich
  transiente Fehler (`RateLimit`/`Timeout`/`Connection`/`InternalServerError`,
  `httpx.RequestError`) — kein Retry mehr bei `APIError`/4xx/Auth.
  Permanente Capture-Fehler setzen `entries.status=failed` (Dashboard-
  sichtbar).
- **E27-3 Sichere Remote-Defaults.** Compose bindet `127.0.0.1:8000`
  (statt `0.0.0.0`); Session-Cookie `Secure`-Flag via `UI_COOKIE_SECURE`;
  Logout per POST (GET löscht Cookie nicht mehr); Setup-Wizard warnt bei
  Telegram ohne Allowlist.
- **E27-4 Frontmatter-/Pfad-Härtung.** Titel/Tags werden vor YAML-Schreiben
  bereinigt (Newlines/`---`/Steuerzeichen); `resolve_vault_file` nutzt
  `Path.is_relative_to`; Append läuft über denselben Resolver.
- **E27-2 XSS-Fix (P0).** Alle `innerHTML`-Zuweisungen in `dashboard.js`,
  `login.js`, `setup.js` nutzen jetzt `escapeHtml()` — schließt Stored-XSS
  via Notiz-Titel, Ordner, Pfade, Server-Fehlermeldungen. Regressionstest
  prüft alle JS-Dateien auf rohe Interpolationen in `innerHTML`-Kontexten.

### Changed
- **Team-Collaboration-Audit 2026-08 + Phase O.** Strategie-Analyse
  (`docs/audit-2026-08-team-collaboration.md`): Eignung für kleine Teams/
  professionelle Nutzung — Einstufung **PERSONAL + SMALL TEAM** über das
  Modell **Shared Instance** (ein Team = eine Instanz = ein Vault, kein
  Multi-Tenant; konsistent mit ADR 0004/0007). Neue Phase **O — Shared
  Knowledge & Small Teams** in der ROADMAP: **E41** Identity & Accounts,
  **E42** Rollen & Sichtbarkeit (Owner/Editor/Viewer + `visibility` nach
  `ai_access`-Muster), **E43** Team-Gedächtnis & Wiki-Qualitäten (git-basierte
  Version History, Recently Changed, Template-Paket, Aufgaben-light,
  Konflikt-Erkennung), **E44** Team-AI & Administration (Admin-AI-Policy,
  permission-aware Team-RAG, Security-Audit-Log). E33-1 um `actor`
  (Attribution-Vorstufe) erweitert. Bewusst nicht: Realtime-Editing,
  Kommentare/Mentions, Kanban, Share-Links, Multi-Tenant, SSO/Enterprise-IAM.
- **Private-Knowledge-AI-Audit 2026-08 + Phase N.** Analyse
  (`docs/audit-2026-08-private-knowledge-ai.md`): Kann Seiton Brain ein
  privates Wissenssystem mit kontrolliertem AI-Zugriff werden? Ist-Inventar
  (RAG/Suche/Embeddings/Parsing), RAG-Architektur-Empfehlung (Hybrid Search +
  RRF), Local-AI-Machbarkeit (Lücke: lokale Embeddings), Permission-Modell
  (`ai_access` pro Ordner/Notiz, Filter vor Retrieval), Threat Model, Kosten,
  Wettbewerb. Bestätigte Strategie **D — Privacy-First Knowledge AI**
  (inkrementell B→C→D) als neue Phase **N** in der ROADMAP: **E37**
  Retrieval-Fundament (Hybrid Search/RRF, Index-Hygiene, Eval-Harness,
  Similar Notes), **E38** Permission-Layer `ai_access` (fail-closed, Filter
  vor Retrieval, Provider-/Kanal-Trust), **E39** Local AI komplett (lokale
  Embeddings, OpenAI-kompatibler Generik-Provider), **E40** Knowledge Chat
  (Verlauf, Scope-Selector, Transparenz, Injection-Härtung, read-only).
- **Integrations-Audit 2026-08 + Phase M.** Ökosystem-/Interoperabilitäts-
  Analyse (`docs/audit-2026-08-integrations.md`): Ist-Inventar der
  Integrationsflächen, Markt-/Community-Recherche, Jobs-to-be-Done,
  Integration Matrix (Tier 1–4), Architektur-Empfehlungen. Alle 5 vom
  Product Owner bestätigten Initiativen als neue Phase **M — Ecosystem &
  Interoperability** in der ROADMAP: **E32** Vault-Interop & Migration,
  **E33** Universal Capture (inkl. URL-Capture + Provenance), **E34**
  Git-Backup & Data Ownership, **E35** Automation-Fundament, **E36**
  Kontrollierter AI-Access; E22-5/E23-4 werden mit Phase M priorisiert.
- **Product Readiness Audit 2026-08.** Vollständiger Review (Architektur,
  Security, UX, Tests/Ops, Privacy, Markt) vor Monetarisierung/Cloud:
  Bericht [`docs/audit-2026-08-product-readiness.md`](docs/audit-2026-08-product-readiness.md),
  Gesamturteil **GO WITH CONDITIONS**. Neue Phase **L — Launch-Härtung** mit
  Epics **E27** Security-Härtung (P0: Localhost-Guard hinter Proxy, XSS),
  **E28** Datenintegrität & Index-Sync, **E29** Release-/Ops-Readiness,
  **E30** UX Consumer-Pass, **E31** Privacy/DSGVO-Basis; E25-3 aufgegangen
  in E27-5; neuer Sprint-Vorschlag in der ROADMAP.
- **Planung: E15-5 Notion-Evaluation.** Standalone + Obsidian sind per Design
  abgedeckt (E15-1/2, E19); Notion als offene Lücke jetzt als
  Evaluations-Story festgehalten (Export/Sync vs. API-Backend).
- **Planung: Epic E26 Notiz-Templates.** Nutzerdefinierte Vorlagen, wie die KI
  Notizen ablegt: Markdown-Template mit Platzhaltern, KI-Felder, visueller
  Builder für Nicht-Markdown-Nutzer; 6 Stories in der ROADMAP.
- **Planung 2026-08-08:** Bestandsaufnahme → neue Phasen **H** (Capture überall
  & Mobile) und **I** (Cloud-Edition); neue Epics **E22** Capture Everywhere,
  **E23** Mobile Companion (PWA-first), **E24** Cloud & Abo (gated auf
  [ADR 0007](docs/adr/0007-cloud-edition-subscription.md), Proposed),
  **E25** Betrieb & Polish; Sprint-Vorschlag in der ROADMAP.
- **Roadmap-Hygiene:** E12-1/2/4 → 🟢; Phasen A–F als done; Phase G auf
  verbleibenden Backlog (**E21-2**, deferred **E20-3/5**) fokussiert.

### Security
- **E27-1: Proxy-sicherer Localhost-Guard (P0 aus Audit 2026-08).** Hinter
  einem lokalen Reverse-Proxy war `request.client.host` immer `127.0.0.1` —
  `/setup`, UI ohne Passwort und `/docs` waren auf dem dokumentierten
  VPS-Setup remote erreichbar. Der Guard wertet jetzt fail-closed
  `X-Forwarded-For`/`X-Real-IP`/`Forwarded` aus (alle Hops müssen localhost
  sein); Caddy-/nginx-Beispiele blocken `/setup` + API-Doku zusätzlich im
  Proxy. Doku: `SECURITY.md`, `docs/remote-access.md`. 17 neue Tests.

### Added
- **E26-1/E26-2: Notiz-Templates.** Eigene Markdown-Vorlage für den Body
  neuer Notizen: `_seiton/templates/note.md` im Vault mit `{{title}}`,
  `{{summary}}`, `{{tags}}`, `{{date}}`, `{{category}}`, `{{related}}`.
  Frontmatter bleibt fix (Append/Index kompatibel); kaputte Templates →
  Default-Layout + Log-Warnung, Status in Settings sichtbar; `_seiton/`
  vom Index ausgenommen. Doku `docs/note-templates.md`. 15 neue Tests
  (505 gesamt).
- **E22-4: MCP `capture_note` + `digest`.** Der MCP-Server (Cursor/Claude)
  kann jetzt ins Brain schreiben (`POST /v1/capture`) und Themen-Digests
  abrufen (`POST /v1/digest`) — bisher nur Retrieval. 2 neue Client-Tests,
  Doku-Tabellen aktualisiert.
- **E23-2: PWA — UI installierbar.** Web-App-Manifest (`/manifest.webmanifest`),
  Service Worker mit Root-Scope (`/sw.js`, cached nur `/ui/static/*` —
  HTML/API bewusst nie), generierte Icons inkl. maskable + Apple-Touch
  (`scripts/generate_pwa_icons.py`). 6 neue Tests (490 gesamt).
- **E23-1: UI-Auth (Login/Session).** Optionales `UI_PASSWORD`: Web-UI und
  `/api/ui/*` verlangen dann Login (HMAC-signiertes Session-Cookie, 7 Tage,
  stateless; Passwortwechsel invalidiert Sessions). Brute-Force-Lockout
  (5 Versuche/60 s pro IP), Login-Seite `/login`, Logout in der Nav.
  `/setup` bleibt localhost-only. Ohne Passwort: Status quo (localhost-Guard).
  17 neue Tests (484 gesamt).
- **E22-2: Telegram Foto-/Dokument-Capture.** Der Bot nimmt jetzt Dokumente
  (PDF/Word/PowerPoint/Text/Markdown) und Fotos an: Download → Text via
  E18-Extractors (OCR/Vision für Bilder) → normale Capture-Pipeline
  (`kind=document|photo`, Caption wird vorangestellt). Größenlimit
  `TELEGRAM_DOCUMENT_MAX_BYTES` (Default 20 MB). 13 neue Tests (467 gesamt).
- **E25-1: One-Click-Backup in der Settings-UI.** „Backup jetzt erstellen"
  (`POST /api/ui/backup`): `pg_dump` + Vault-tar.gz + Manifest wie
  `scripts/backup.sh`; Backup-Liste mit Größen und geführten
  Restore-Befehlen (`GET /api/ui/backups`). Docker: `postgresql-client` im
  Image, `./backups`-Mount für die API. 7 neue Tests (454 gesamt).
- **E22-3: Digest in der Web-UI.** Themen-Digest-Card auf „Suchen & Fragen"
  (Thema + Zeitraum 7/30/90 Tage/alle) + `POST /api/ui/digest` — gleiche
  Pipeline wie Telegram `/digest` und REST. 4 neue Tests (447 gesamt).
- **E22-1: Capture in der Web-UI.** Erfassen-Formular im Dashboard +
  `POST /api/ui/capture` — gleiche Pipeline wie Telegram/REST (classify →
  Vault + DB, Webhook-Event), mit Status-Feedback (Titel, Kategorie,
  create/append, Pfad, Tags). 5 neue Tests (443 gesamt).
- **E6-4: Lokaler Whisper (whisper.cpp).** `WHISPER_PROVIDER=whisper.cpp` mit
  Soft-Probe Binary/Modell, optionalem OpenAI-Fallback; Config
  `WHISPER_CPP_*`. Doku `docs/whisper-cpp.md`. 7 neue Tests (438 gesamt).
- **E16-5: OS-Keystore für Secrets.** Optional `keyring` (MIT):
  `seiton init --keyring`, `seiton keyring-export`, Launcher
  `./scripts/seiton-up.sh` + `deploy/compose.keyring.yml`. Doku
  `docs/keyring.md`. 8 neue Tests (431 gesamt).
- **E16-3: `seiton init`.** Interaktives CLI (`python -m app.cli init` /
  `./scripts/seiton init`) schreibt lokale `.env` (Vault, Keys, Embeddings);
  `--non-interactive` für Skripte. Kein Netzwerk-Upload. 7 neue Tests
  (423 gesamt).
- **E9-5: Consumer-Stack-Eval.** [ADR 0006](docs/adr/0006-consumer-stack-no-sqlite-fork.md):
  kein SQLite-/in-process-Fork; ein Stack (Postgres + Redis + Celery),
  Vereinfachung über Packaging. ADR 0004 Open-Items aktualisiert.
  2 neue Tests (416 gesamt).
- **E9-3: Remote-Zugang VPS.** Hub-Doku `docs/remote-access.md` (Caddy, nginx,
  Cloudflare Tunnel, SSH, Tailscale) + Beispiele
  `deploy/nginx-seiton.conf.example`, `deploy/cloudflared-config.example.yml`.
  4 neue Tests (414 gesamt).
- **E7-4: Multi-LLM in n8n.** Doku `docs/integrations/n8n-multi-llm.md` + Workflow
  `examples/n8n/05-multi-llm-enrich-then-capture.json` (Ollama anreichern →
  Seiton Capture). 1 neuer Test (410 gesamt).
- **E18-6: Vision für Fotos.** Optionaler OpenAI-Vision-Pfad (`SEITON_VISION_ENABLED`,
  Default aus): Bildbeschreibung + Tags als Index-Text (`doc_type=image_vision`);
  OCR hat Vorrang. Prompt `vision.v1.txt`, Doku `docs/vision.md`. 13 neue Tests
  (409 gesamt).
- **E7-3: Spezialisierte LLM-Rollen.** Classify läuft als Router → Writer →
  Linker (max. 3 Steps, Linker nur bei Vault-Inhalt); Aggregate bleibt
  `ClassificationResult`. Config `SEITON_LLM_ROLES_ENABLED` (Default true;
  false = Ein-Shot `classify`). Prompts `router`/`writer`/`linker`.v1.
  9 neue Tests (396 gesamt).
- **E18-5: OCR (optional).** Tesseract-Adapter für gescannte PDFs (`pdf_ocr`) und
  Bilder (`image_ocr`); Soft-Import + `requirements-ocr.txt`, Config
  `SEITON_OCR_ENABLED` / `SEITON_OCR_LANG`. Doku `docs/ocr.md`. 12 neue Tests
  (387 gesamt).
- **E15-3: Git-backed Vault.** `GitVaultBackend` ergänzt das Filesystem-Backend
  um einen Commit pro Note und optionalen Push (`VAULT_GIT_PUSH`,
  `VAULT_GIT_REMOTE`, `VAULT_GIT_BRANCH`). 4 neue Tests (375 gesamt).
- **E18-4: Dokument-Chunking.** Tabelle `vault_chunk` (N Chunks/Dokument);
  Keyword- und semantische Suche laufen über Chunks; Config
  `SEITON_CHUNK_SIZE` / `SEITON_CHUNK_OVERLAP`. Parent bleibt
  `vault_note_index`. 4 neue Tests (371 gesamt).
- **E15-1: VaultBackend-Protocol.** `get_vault_backend()` +
  `FilesystemVaultBackend` (Markdown unter `OBSIDIAN_VAULT_PATH`);
  `process_message` spricht das Protocol; `writer.py` bleibt
  Kompatibilitäts-Wrapper. Config `VAULT_BACKEND`. 5 neue Tests (367 gesamt).
- **E11-4: README-Visuals & Repo-Topics.** Flow-GIF + Dashboard-/Ask-Screenshots
  unter `docs/assets/`, Generator `scripts/generate-readme-assets.py`, GitHub-
  Topics/Description. 2 neue Doc-Tests (362 gesamt).
- **E7-2: Ollama-Provider.** `LLM_PROVIDER=ollama` mit `OLLAMA_BASE_URL` /
  `OLLAMA_MODEL`; OpenAI-kompatibles `/v1`, gleiches Classify-/Answer-/Digest-
  Schema. Doku `docs/llm-providers.md`. 7 neue Tests (360 gesamt).
- **E4-4: Prompt-Versionierung.** `prompts/classify.v1.txt` + Config
  `SEITON_PROMPT_VERSION` (Default `v1`); Version landet in `entries.prompt_version`
  (Alembic-Migration). Loader `app/llm/prompts.py`. 7 neue Tests (353 gesamt).
- **E5-2: Vault-Prefilter vor LLM.** Token-Overlap (Titel/Snippet) wählt max.
  `SEITON_LLM_NOTE_LIMIT` (Default 30) Notizen für den Classify-Prompt aus einem
  größeren Index-Pool. Modul `app/vault/prefilter.py`. 7 neue Tests (346 gesamt).
- **E4-3: Konfigurierbare Kategorien.** `vault_config.yaml` (Vault-Root oder
  `SEITON_VAULT_CONFIG`) mappt Kategorie→Ordner; Classify-Prompt nutzt die
  aktive Liste. Vorlage `vault_config.example.yaml`. Modul
  `app/vault/categories.py`. 5 neue Tests (339 gesamt).
- **E6-2: Voice-Cache.** Audio wird unter `TELEGRAM_VOICE_CACHE_DIR` (Default
  `temp/voice`) bis zur erfolgreichen Verarbeitung gehalten — Celery-Retry ohne
  erneuten Telegram-Download. Docker-Volume `seiton-voice-cache` am Worker.
  4 neue Tests (334 gesamt).
- **E6-1: Voice-Dateigroesse.** Env `TELEGRAM_VOICE_MAX_BYTES` (Default 10 MB);
  fruehe Ablehnung im Webhook (wenn `file_size` bekannt) und nach Download im
  Worker; freundliche Telegram-Antwort ohne Admin-Alarm. 6 neue Tests (330 gesamt).
- **E6-3: Whisper language-Hint.** Env `WHISPER_LANGUAGE` (ISO-639-1, z. B.
  `de`) wird an die Whisper-API durchgereicht; leer = Auto-Detect. Ungültige
  Werte werden ignoriert (Warn-Log). 4 neue Tests (324 gesamt).
- **E16-1: Init-Skript.** `scripts/init.sh` und `make init` — idempotent `.env`
  + Vault aus `vault.example/`, Docker-Hinweise, keine Secrets. Gemeinsame Lib
  `scripts/lib/init.sh` (auch `install.sh`). 1 neuer Funktionstest (313 gesamt).
- **E15-2: Vault-Doku (Obsidian optional).** `docs/vault.md` — Markdown-Ordner
  ohne Obsidian, `vault.example/`, Kategorien, Editoren, Web-UI `/notes`.
  Verlinkt aus README, setup, packaging, vault-backends. 2 neue Doc-Tests
  (312 gesamt).
- **E12-3: Troubleshooting.** Ausführliche Doku `docs/troubleshooting.md`
  (Docker, Telegram Webhook/Polling, ngrok, Migrationen, Vault, API, UI).
  Kurzreferenz in `docs/setup.md`; Verlinkung aus `self-hosting.md`. 2 neue
  Doc-Tests (310 gesamt). ROADMAP: E16-2 (doctor) und E16-4 (Setup-Wizard) 🟢.
- **E11-3: Contributing.** `CONTRIBUTING.md` (Dev-Setup, PR-Checkliste, Konventionen),
  GitHub Issue-Templates (Bug, Feature) + PR-Template. Verlinkung aus README.
  4 neue Doc-Tests (308 gesamt).
- **E11-2: SECURITY.md.** Meldeweg (GitHub Security Advisory), Threat Model,
  Betreiber-Empfehlungen; Verlinkung aus README. 2 neue Doc-Tests (304 gesamt).
- **E13-4: OpenAPI/Swagger.** `/docs`, `/redoc`, `/openapi.json` wenn
  `SEITON_API_KEY` gesetzt oder `SEITON_DEBUG=true` — nur localhost erreichbar.
  API-Key-Schema fuer `/v1/*`. Config `SEITON_DEBUG`. 6 neue Tests (302 gesamt).
- **E9-2: Multi-Plattform-Self-Hosting.** Zentraler Einstieg `docs/self-hosting.md`
  (Entscheidungstabelle Mac/Windows/Linux/VPS, Compose-Profile, Plattform-Tipps,
  Troubleshooting). Verlinkt aus README, `packaging.md`, `vps-deployment.md`.
  Doctor-Skripte verweisen auf die Doku. 2 neue Doc-Tests (296 gesamt).
- **E21-1: Offline-Lizenzierung.** Ed25519-signierte Lizenzschlüssel (`SEITON1.…`),
  Modul `app/licensing/`, Startup-Enforcement via `SEITON_LICENSE_REQUIRED`,
  Issuer `scripts/issue-license.py`, Settings-UI (Lizenzstatus + Speichern),
  Doku `docs/licensing.md` (E21-3). Dependency `cryptography`. 12 neue Tests (294 gesamt).
- **E20-4: Auto-Update.** `scripts/update.sh` (git pull, Rebuild, Migrationen,
  optionales Backup, `--check`/`--no-backup`), gemeinsame Hilfen `scripts/lib/deploy.sh`,
  systemd-Timer-Beispiel `deploy/seiton-update.{service,timer}`. Doctor nutzt
  deploy-Lib. 1 neuer Shell-Syntax-Test (282 gesamt).
- **E20-2: VPS-Deployment.** Skript `scripts/deploy-vps.sh` fuer Linux-VPS
  (Webhook-Modus, kein Poller), `docker-compose.vps.yml` (localhost-Bind +
  Restart), `scripts/register-telegram-webhook.sh`, Caddy-Beispiel
  `deploy/Caddyfile.example`, Doku `docs/vps-deployment.md`. Doctor erkennt
  `SEITON_DEPLOY_MODE=vps`. 2 neue Shell-Syntax-Tests (282 gesamt).
- **E20-1: Consumer-Installer.** Skripte `scripts/install.sh` (macOS/Linux) und
  `scripts/install.ps1` (Windows) fuer vereinfachtes Heim-Box-Setup: Vault anlegen,
  `.env` vorbereiten, Docker Compose im Consumer-Modus (`docker-compose.consumer.yml`
  + Long-Polling), Migrationen, Browser-Setup-Wizard. Diagnose via `scripts/doctor.sh`
  / `doctor.ps1`. Doku `docs/packaging.md`. 2 neue Shell-Syntax-Tests (282 gesamt).
- **E19-5: Settings-UI.** Neue Seite `/settings` (localhost-only) für laufende
  Konfiguration: Keys/Provider, Telegram, API-Key, Webhook, Kategorie-Mapping,
  Backup-Hinweise und Edition-Info (ADR 0005). API `GET/POST /api/ui/settings`,
  `POST /api/ui/settings/test`. Gemeinsame Speicherlogik `app/setup/config_save.py`.
  10 neue Tests (282 gesamt). **Epic E19 abgeschlossen.**
- **E19-4: Notizen verwalten (Web-UI).** Neue Seite `/notes` (localhost-only) mit
  Index-Liste, Markdown-Editor (öffnen/speichern/löschen), Ordner-Filter und
  Vault-Konfiguration (Kategorie→Ordner-Mapping). API `GET/PUT/DELETE /api/ui/notes`,
  `GET /api/ui/vault-config`. `save_note_content()` im Vault-Writer; gemeinsamer
  Pfad-Helper `app/vault/paths.py`. 14 neue Tests (272 gesamt).
- **E19-3: Suche & Ask (Web-UI).** Neue Seite `/ask` (localhost-only) mit
  Vault-Suche (Keyword/semantisch) und RAG-Chat — gleiche Pipeline wie Telegram
  `/find` und `/ask`. API `GET /api/ui/search`, `POST /api/ui/ask`. Navigation
  erweitert. 3 neue Tests (258 gesamt).
- **E19-2: Dashboard (Web-UI).** Neue Seite `/dashboard` (localhost-only) mit
  Statistik (Entries, Status, Vault-Index), Tabelle letzter Captures und zuletzt
  geänderter Vault-Notizen. API `GET /api/ui/dashboard`. Gemeinsames Layout
  (`base.html`, `app.css`) mit Setup-Navigation. `/` leitet nach Setup bzw.
  Dashboard weiter. 3 neue Tests (255 gesamt).
- **E19-1: Setup-Wizard (Web-UI).** Neuer Assistent unter `/setup` (nur
  localhost): Vault-Pfad, OpenAI-Key, optional Telegram, Verbindungstests,
  sicheres Schreiben in `.env`. Module `app/setup/`, `app/ui/`. Telegram-
  Felder in der Config optional (leer = deaktiviert). 8 neue Tests (252 gesamt).
- **ADR 0005 + Doku-Konsistenz (Portfolio jetzt, Produkt später).** Repo bleibt
  vorerst public (MIT); README, Integrations-Docs und Cursor-Rules kommunizieren
  die geplante kommerzielle Edition (ADR 0004). n8n-Doku bereinigt (kein Custom
  Node; Beispiel-Workflows bleiben). ROADMAP E14 reframed.
- **E17-8: Digest-Synthese.** Service `build_digest` sammelt Notizen zu einem
  Thema (Ordner/Kategorie/Keyword, optional letzte N Tage) und erzeugt eine
  LLM-Zusammenfassung mit Quellen und Highlights. Telegram `/digest <thema>`
  (async Worker), `POST /v1/digest`. Prompt `prompts/digest.txt`. 11 neue Tests
  (244 gesamt).
- **E17-7: Outbound-Event `note.indexed` + Knowledge-Backend-Doku.** Neues
  Webhook-Event nach erfolgreicher Embedding-Berechnung in
  `upsert_vault_note_index` (nur bei `EMBEDDINGS_ENABLED`, kein Event beim
  Bulk-Sync). Payload: `vault_path`, `title`, `category`, `folder`, `doc_type`.
  n8n-Workflow **02** um `note.indexed`-Zweig erweitert; neuer Beispiel-Workflow
  **04** (semantische Suche nach indexiertem Wissen). Doku in
  `knowledge-retrieval.md`, `setup.md`, `examples/n8n/README.md`. 3 neue Tests
  (233 gesamt).
- **E17-6: MCP-Server (`examples/mcp/seiton-brain-mcp`).** stdio-MCP-Server
  für Cursor / Claude Desktop mit drei Tools: `search_notes`, `ask_brain`,
  `get_note` — dünner httpx-Wrapper um die REST-API (E17-5), keine Engine-
  Logik im MCP-Prozess. Auth via `SEITON_API_KEY` im Server-Env. Ergänzende
  API-Endpunkte: `GET /v1/entries/{id}`, `GET /v1/notes/content?vault_path=`
  (read-only, Path-Traversal-Schutz). Setup-Doku in `examples/mcp/`. CI-Step
  für MCP-Client-Tests. 9 neue Tests (230 gesamt).
- **E17-5: Retrieval-API.** `POST /v1/ask` liefert `AnswerResult` (RAG über
  E17-3, gleiche API-Key-Auth wie `/v1/capture`). `GET /v1/notes/search` um
  Query-Parameter `semantic=true` erweitert (semantische Suche mit Keyword-
  Fallback, analog zur RAG-Pipeline). Gemeinsame Retrieval-Funktion
  `retrieve_vault_notes` in `app/vault/index.py` (von API und RAG-Service
  geteilt). Response enthält `semantic`-Flag. 7 neue Tests.
- **E17-4: Telegram-Command `/ask <frage>`.** Macht den RAG-Service (E17-3) im
  Chat nutzbar: `/ask` wird — anders als die schnellen Slash-Commands — in den
  **Worker** eingereiht (LLM-Call), mit Sofort-Ack „Ich durchsuche dein Brain…"
  und asynchroner Antwort inkl. anklickbarer `[[Quellen]]`. Leeres `/ask` zeigt
  einen Nutzungshinweis; `/ask@BotName` wird unterstützt. Neuer Celery-Task
  `process_ask_message_task` (gleiches Retry-/Fehler-Muster wie Capture,
  `kind="qa"`). `/ask` in `/help` ergänzt. 7 neue Tests.
- **E17-3: RAG-Antwort-Service.** Neuer Service `app/services/answer.py`
  (`answer_question`) verbindet Retrieval (Keyword E17-1 / semantisch E17-2) mit
  LLM-Generierung: Frage → relevanteste Vault-Notizen als Kontext → geerdete
  Antwort mit **Quellen**. Neue Pydantic-Schemas `AnswerResult`
  (`answer`, `sources: list[NoteRef]`, `confidence`), `NoteRef` und interne
  `LLMAnswer`; neuer Prompt `prompts/answer.txt`; `LLMProvider.answer()` +
  OpenAI-Implementierung (JSON-Mode, gleiches Retry-Muster wie `classify`).
  Quellen werden auf real existierende Treffer aufgelöst (Halluzinationen
  verworfen), `confidence` auf 0–1 geklemmt. Ohne Treffer: ehrliche
  „nichts gefunden"-Antwort **ohne** LLM-Call (spart Kosten). Semantik wird
  bevorzugt, wenn `EMBEDDINGS_ENABLED`, sonst Keyword-Fallback. Chat-Formatter
  `format_answer_for_chat` rendert `[[Wiki-Links]]`. 15 neue Tests. Konsumenten
  `/ask` (E17-4) und `POST /v1/ask` (E17-5) folgen.
- **E17-2 / E5-3: Semantische Suche via pgvector.** Neuer Embedding-Provider
  `app/llm/embeddings.py` (`EmbeddingProvider`-Interface + `OpenAIEmbeddingProvider`,
  analog zu `LLMProvider`). Der Vault-Index bekommt eine nullable
  `embedding`-Spalte (pgvector `Vector(1536)`, Alembic-Migration + `CREATE
  EXTENSION vector`); Notizen werden beim Schreiben/Append/Sync embedded.
  Neue Engine-Funktion `semantic_search_vault_notes` (kNN per Cosine-Distanz).
  Opt-in über `EMBEDDINGS_ENABLED` (Default aus → keine Embedding-Kosten);
  Embeddings sind best-effort (Fehler brechen das Indexieren nicht ab, Keyword-
  Suche bleibt). Postgres-Image auf `pgvector/pgvector:pg16`. Neue Dependency
  `pgvector`. 11 neue Tests. Konsumenten (`/find semantic`, `/v1/notes/search`,
  RAG) folgen in E17-3/E17-5.
- **E1-5: Telegram Long-Polling als Webhook-Alternative.** Neuer Poller
  `app/telegram/polling.py` (`python -m app.telegram.polling` bzw. Compose-Profil
  `polling`) holt Updates aktiv per `getUpdates` — keine öffentliche HTTPS-URL,
  kein Reverse-Proxy/Tunnel nötig. Passt zum Deployment-Leitbild „Always-on-Box"
  (Mini-PC/Mac Mini/Heimserver, ADR 0004). Die Update-Verarbeitung ist jetzt
  transport-agnostisch in `process_update` gekapselt und wird von Webhook **und**
  Poller geteilt (Allowlist, Idempotenz, Slash-Commands, Worker-Enqueue
  unverändert). Poller ruft beim Start `deleteWebhook` (Telegram erlaubt nur
  Webhook *oder* Polling); ein einzelnes kaputtes Update killt den Loop nicht.
  Neue Client-Funktionen `get_updates`/`delete_webhook`, Setting
  `TELEGRAM_POLLING_TIMEOUT` (Default 25 s). 7 neue Tests.
- **Produkt-Pivot in der Planung (ADR 0004).** Neue Architekturentscheidung
  [ADR 0004](./docs/adr/0004-commercial-consumer-product.md): Seiton Brain wird
  ein **kommerzielles, self-hosted Consumer-Produkt** (einmal kaufen, Kunde
  hostet selbst, eigener LLM-Key; wir liefern Produkt + Updates). ROADMAP-Vision
  um Produktstrategie ergänzt, neue **Phase G (Produktisierung)** und drei neue
  Epics: **E19 UI/Dashboard**, **E20 Packaging & Distribution**, **E21
  Commercial/Licensing**; neue Story **E1-5 (Telegram Long-Polling)**. Reine
  Planungs-/Doku-Änderung, kein Code.
- **E18-3: Office-Formate (Word & PowerPoint).** Neue Extractoren `DocxExtractor`
  (via `python-docx`, `.docx`) und `PptxExtractor` (via `python-pptx`, `.pptx`)
  speisen Office-Dokumente in den Vault-Index. Word: Absätze plus Tabellentext
  (Zeugnisse/Rechnungen liegen oft in Tabellen). PowerPoint: Folientext plus
  Sprechernotizen. Titel kommt aus den Office-Core-Properties, sonst Dateiname.
  Defekte Dateien brechen den Vault-Scan nicht ab (geloggt, leerer Text). Altes
  `.doc`-Binärformat bleibt bewusst unsupported. Neue Dependencies `python-docx`,
  `python-pptx` (beide MIT). 7 neue Tests.
- **E18-2: PDF-Text-Extraktion.** Neuer `PdfExtractor` (via `pypdf`) liest den
  Text-Layer von `.pdf`-Dateien in den Vault-Index. PDFs ohne Text-Layer (Scans)
  werden als `doc_type=pdf_no_text` markiert — Aufhänger für späteres OCR (E18-5).
  Defekte PDFs brechen den Vault-Scan nicht ab (werden geloggt und übersprungen).
  Neue Dependency `pypdf`. 4 neue Tests.
- **E18-1: Multi-Format-Ingestion — Fundament.** Neues Modul
  `app/vault/extractors.py` mit `DocumentExtractor`-Interface (Engine+Adapter)
  und Adaptern für Markdown (`.md`, `.markdown`) und Plain-Text (`.txt`, `.text`,
  `.log`). Der Vault-Index (E5-1) erfasst jetzt **alle** unterstützten Formate
  statt nur Markdown; neue Spalte `doc_type` (`markdown`/`text`/…) plus Alembic-
  Migration. Vollscan überspringt versteckte Ordner (z. B. `.obsidian`) und nicht
  unterstützte Typen (z. B. `.pdf`). Damit docken PDF (E18-2), Office (E18-3),
  OCR (E18-5) und Vision (E18-6) ohne Index-Änderung an. 6 neue Tests.
- **E5-1 + E17-1: Vault-Index und Keyword-Suche.** Neue Tabelle
  `vault_note_index` (Pfad, Titel, Kategorie, Ordner, Body-Snippet, mtime).
  Index wird bei Capture/Append aktualisiert, `/undo`-Löschung entfernt Einträge,
  leerer Index bootstrappt per Vault-Scan. LLM-Kontext liest aus DB statt
  `rglob`. `/find` durchsucht Titel + Inhalt im gesamten Vault;
  `GET /v1/notes/search?q=...`. Modul `app/vault/index.py`. Alembic-Migration.
- **E14-1: n8n-Beispiel-Workflows.** Neuer Ordner `examples/n8n/` mit drei
  importierbaren JSON-Workflows: Capture via `POST /v1/capture`, Webhook-Event-Router
  (`note.created` / `note.appended` / `entry.failed`), Todoist → Capture.
  Setup-Anleitung in `examples/n8n/README.md`. 3 JSON-Validierungstests.
- **E13-3: Outbound Webhooks.** Optionales Setting `SEITON_WEBHOOK_URL`.
  Nach erfolgreichem Capture (Telegram-Worker und `POST /v1/capture`) POST
  mit `note.created` bzw. `note.appended`; bei dauerhaft fehlgeschlagenen
  Worker-Tasks `entry.failed`. Event im JSON-Feld `event` und Header
  `X-Seiton-Event`. Best-effort — Fehler beim Versand nur im Log.
  Modul `app/webhooks/outbound.py`. 9 neue Tests.
- **E9-4: Lokale Backups.** Neues Skript `scripts/backup.sh` erstellt einen
  Zeitstempel-Ordner mit `postgres.sql` (via `docker compose exec db pg_dump`),
  `vault.tar.gz` (Archiv von `OBSIDIAN_VAULT_HOST_PATH`) und `manifest.txt`.
  `backups/` ist gitignored. Restore-Anleitung in `docs/setup.md`. Shell-Syntax-Test.
- **E10-3: Admin-Fehler-DM per Telegram.** Neues optionales Setting
  `TELEGRAM_ADMIN_CHAT_ID`. Bei dauerhaft fehlgeschlagenen Worker-Tasks
  (nach allen Celery-Retries) erhält der Admin eine DM mit Task-Name,
  Task-ID, Chat/Update-Kontext und gekürztem Traceback — zusätzlich zur
  generischen User-Meldung und zum Log. Modul `app/telegram/admin_notify.py`.
  5 neue Tests.
- **E9-1: Dockerfile härten.** Multi-Stage-Build (venv in separater Builder-Stage),
  Runtime-Image ohne Build-Artefakte. Container läuft als non-root User `seiton`
  (UID/GID 1000). `HEALTHCHECK` prüft `GET /health` (nutzt E10-4). `worker` in
  Compose deaktiviert den API-Healthcheck. Troubleshooting-Hinweis zu Vault-Rechten.
- **E7-1: Provider-unabhängige JSON-Validierung + LLM-Retry.** Neues Modul
  `app/llm/parser.py` mit `parse_classification_json()` — zentrales
  `json.loads` + `ClassificationResult.model_validate` für alle Provider.
  `OpenAIProvider.classify()` wiederholt den LLM-Aufruf bis zu 3× bei
  `JSONDecodeError` oder Pydantic-`ValidationError` (kaputtes Schema).
  Nach allen Versuchen: `ClassificationParseError`. 5 neue Tests.
- **E13-2: API-Key-Auth für REST-API v1.** Neues Setting `SEITON_API_KEY`
  (optional, Default leer). Ohne Key sind alle `/v1/*`-Endpunkte deaktiviert
  (HTTP 503 mit Hinweis). Mit gesetztem Key muss jeder Request den Header
  `X-Seiton-Api-Key` senden — timing-safe Vergleich via `secrets.compare_digest`.
  Fehlender/falscher Key → 401. Startup-Log warnt bzw. bestätigt API-Status.
  `.env.example` ergänzt. 3 neue Auth-Tests.
- **E13-1: REST-API v1.** Neue Endpunkte unter `/v1/` (ohne Auth — `E13-2`
  folgt): `POST /v1/capture` (gleiche Pipeline wie Telegram: klassifizieren,
  Vault schreiben, Entry in DB), `POST /v1/classify` (nur LLM, ohne
  Persistenz), `GET /v1/entries` (paginierte Liste, `limit`/`offset`).
  `process_text_message` liefert jetzt `ProcessMessageResult` mit
  `classification`, `entry_id`, `vault_path` und `status` — Worker und API
  teilen sich dieselbe Pipeline. Modul `app/api/v1/`. 5 neue API-Tests.
- **E8-2: Klare Fehlermeldungen bei fehlender Konfiguration.** `load_settings()`
  fängt pydantic `ValidationError` ab und gibt pro fehlendem Pflichtfeld
  ENV-Name + Kurzhilfe auf stderr aus (Verweis auf `.env.example` und
  `docs/setup.md`), dann `SystemExit(1)`.
- **E10-1: Strukturiertes Logging mit Korrelation.** Neues Modul
  `app/logging_config.py`: JSON-Logformat (Default, `LOG_JSON=true`) oder
  lesbares Text-Format (`LOG_JSON=false` für lokale Entwicklung). Jede Zeile
  kann `task_id` (Celery), `request_id` (HTTP-Middleware, auch als
  `X-Request-ID`-Response-Header) und `telegram_update_id` (Worker) enthalten.
  Kontext via `contextvars` — async-/thread-sicher. API und Celery-Worker
  konfigurieren Logging beim Start; Celery `task_prerun`/`task_postrun` setzen
  bzw. leeren `task_id`. Settings: `LOG_LEVEL`, `LOG_JSON`. 6 neue Tests.
- **E10-4: Health-Endpunkt prüft DB + Redis.** `GET /health` führt jetzt echte
  Connectivity-Checks aus (`SELECT 1` gegen Postgres, `PING` gegen Redis).
  Antwort enthält `status` und `checks`-Objekt pro Dependency. Bei Fehler:
  HTTP 503 mit `status: "unhealthy"` — für Docker-Compose, Uptime-Monitore
  und späteres Hosting. Checks in neuem Modul `app/health.py`, Fehlerdetails
  nur im Log (kein Leak von Connection-Strings). 7 neue Tests.

### Changed
- **Roadmap-Umpriorisierung durch Produkt-Pivot (ADR 0004).** **E14 (n8n-
  Ökosystem) gestrichen** — kein Eigenbau/keine Custom-Node mehr (REST-API bleibt
  für Power-User). **E9 (Hosting)** von „Mac Mini 24/7" zu **Multi-Plattform-
  Self-Hosting + VPS** (Mac/Win/Linux/IONOS) verallgemeinert. **E16 (Setup)**
  verschiebt sich Richtung UI-Wizard; **E15-4 (read-only Web-UI)** geht in das
  UI-Epic E19 auf. Integrations-Docs (`n8n.md`, `README.md`, `setup-onboarding.md`,
  `vault-backends.md`) und `ARCHITECTURE.md` entsprechend angepasst (Telegram
  optional/Long-Polling, UI als Hauptadapter, Produkt-Editionen).
- **Python 3.12 → 3.14.** Dockerfile (builder + runtime) und CI laufen jetzt auf
  Python 3.14 (neueste stabile Version, Bugfix-Maintenance bis 2030). 3.12 war
  seit Okt 2025 nur noch im Security-Modus. C-Extension-Deps (asyncpg, greenlet,
  lxml, Pillow) haben cp314-Wheels. (#56)

### Removed

---

## [0.2.0] — 2026-06-07 — Phase A+B: robustes Second-Brain-Inbox

Phase A (MVP-Härtung) und Phase B (Produkt-Features) abgeschlossen. Das System ist
jetzt ein zuverlässiges persönliches Second-Brain-Inbox für Obsidian — nicht mehr nur
eine erste Pipeline.

### Added
- **E1-4: Webhook-Hardening (Body-Limit + unsupported Update-Typen).**
  Der Webhook lehnt Bodies > `telegram_webhook_max_body_bytes` (Default
  1 MB, konfigurierbar) mit HTTP 413 ab — echte Telegram-Updates sind
  typischerweise <10 KB, das Limit schützt vor Resource-Exhaustion durch
  fehlgeleitete oder bösartige Requests. Ungültiges JSON wird mit 400
  beantwortet statt zu crashen. Bekannte aber unsupported Update-Typen
  (`edited_message`, `channel_post`, `callback_query`, `inline_query`,
  `chat_member`, `poll`, `business_*`, `chat_boost*`, …) werden mit
  silent 200 OK beantwortet — Telegram retried sonst alle 1s und
  blockiert die Bot-Queue. Statt Warn-Spam landen sie auf DEBUG-Level.
  6 neue Tests (Limit, Invalid-JSON, Edited-Message, Callback-Query,
  Unbekannte-Form).
- **E11-1: LICENSE-Hinweis im README.** Die MIT-LICENSE liegt seit dem
  ersten Doku-Commit im Repo-Root, das README verlinkt jetzt explizit
  darauf. Damit erfüllt das Repo die formale Public-Release-Voraussetzung
  und Forks finden die Lizenz auf den ersten Blick.
- **E3-4: Atomares Schreiben im Vault.** `write_note` und `append_to_note`
  schreiben jetzt in eine versteckte `.tmp`-Datei im Zielverzeichnis und
  ersetzen die Zieldatei dann via `os.replace` — eine atomare Operation auf
  POSIX und Windows (solange Quelle und Ziel im selben Verzeichnis liegen).
  Damit sehen Sync-Clients wie Obsidian Sync, Syncthing oder iCloud nie eine
  halb geschriebene Notiz, und ein Crash zwischen Schreiben und Replace
  hinterlässt höchstens eine `.tmp`-Datei statt korrupten Inhalt am Ziel.
  `fsync` vor dem Replace sorgt zusätzlich dafür, dass der Inhalt physisch
  auf dem Datenträger ist. Failure-Path räumt das Tempfile sauber auf.
  6 neue Tests inkl. simuliertem Disk-Full-Crash.
- **E1-3: Telegram-Slash-Commands.** Der Bot versteht jetzt
  `/start`/`/help` (Hilfe-Text), `/recent [n]` (letzte N Notizen,
  Default 5, max 20), `/find <begriff>` (case-insensitive
  Substring-Suche über Titel via Postgres `ILIKE`, max 10 Treffer) und
  `/undo` (zeigt die letzte Notiz inkl. Status; `/undo confirm` löscht
  sie). Commands gehen synchron im Webhook durch, nicht über den
  Celery-Worker — schnelle DB-Lookups statt LLM-Calls. Bei
  `status="appended"`-Einträgen löscht `/undo confirm` bewusst nur den
  DB-Eintrag, nicht die Vault-Datei (sonst wäre die ganze Notiz mit
  evtl. vielen Update-Blöcken weg); der User wird auf den manuellen
  Cleanup hingewiesen. Alle Queries werden per `telegram_chat_id`
  isoliert, damit ein User nur seine eigenen Notizen sieht. Neuer
  `delete_note()`-Helper im Vault-Writer. 22 neue Tests
  (Command-Handler, Webhook-Dispatch, Vault-Delete).
- **E10-2: Celery-Retries mit Backoff für OpenAI/Whisper.** Beide
  Worker-Tasks (`process_text_message`, `process_voice_message`) sind
  jetzt mit `autoretry_for=(RateLimitError, APITimeoutError,
  APIConnectionError, APIError, httpx.HTTPError, ConnectionError,
  TimeoutError)` konfiguriert: bis zu 3 Retries, exponentieller Backoff
  mit Jitter, gedeckelt bei 60s. Transiente OpenAI-5xx, Rate-Limits oder
  Netzwerk-Hiccups führen damit nicht mehr zum Verlust der Nachricht,
  sondern werden im Hintergrund wiederholt. Celery's `Retry`-Exception
  wird im `except`-Block ausgenommen, damit der User nicht pro Retry eine
  „Etwas ist schiefgelaufen"-Telegram-Meldung bekommt — die kommt nur,
  wenn alle Versuche erschöpft sind.
- **E3-3: Frontmatter-Updates beim Append.** `append_to_note()` pflegt jetzt
  beim Anhängen eines Update-Blocks auch das YAML-Frontmatter: Feld
  `updated: <heute>` wird gesetzt (neu angelegt, falls noch nicht vorhanden),
  und Tags aus dem Update werden mit den bestehenden Tags der Notiz gemergt
  (deduplizierend, Reihenfolge stabil, Normalisierung wie bei Erstanlage).
  Damit sortiert Obsidian „Sort by modified" wieder korrekt und Tag-Listen
  bleiben konsolidiert. Hand-rollter Mini-Frontmatter-Parser in
  `app/vault/writer.py` — bewusst keine PyYAML-Abhängigkeit, weil unser
  Format auf ein paar wohldefinierte Keys beschränkt ist. Tag-Normalisierung
  und -Merge in neues Modul `app/llm/tags.py` extrahiert, vom LLM-Provider
  und Vault-Writer geteilt.
- **Planungsergänzung „Brain als Wissensquelle":** ROADMAP-Vision um die
  zweite Produkthälfte (Retrieve neben Capture) erweitert, neue Phase **F**
  und neues **Epic E17 — Knowledge Retrieval & Q&A** mit acht Stories
  (Keyword-Suche, semantische Suche via pgvector, RAG-Antwort-Service,
  Telegram-`/ask`, Retrieval-API `POST /v1/ask`, MCP-Server in separatem
  Repo für externe LLM-Agenten, `note.indexed`-Event, Digest-Synthese).
  `ARCHITECTURE.md`: Engine+Adapter-Diagramm und -Tabelle um Output-Adapter
  „Retrieval / Q&A" und „MCP-Server" ergänzt; expliziter Abschnitt
  „Capture und Retrieve als gleichwertige Hälften". Neue Integrations-Doc
  [`docs/integrations/knowledge-retrieval.md`](./docs/integrations/knowledge-retrieval.md)
  beschreibt die drei Stufen, MCP-Tools, Szenarien und offene Fragen.
  Keine Code-Änderungen — reine Planungslücke geschlossen.
- **Backlog-Hygiene:** `scripts/bootstrap_github.sh` um neue Labels
  (`epic:retrieval`, `phase:F-knowledge`, `meta:epic-tracker`), Milestone
  „Phase F — Knowledge" und neue Issue-Vorlagen erweitert: konkrete
  Story-Issues für Phase B (E3-3, E3-4, E10-2, E1-3, E1-4) sowie
  Epic-Tracker-Issues mit Story-Checklisten für E13–E17.
- **Konsistenz-Fix in ROADMAP:** E1-3 nicht mehr mit `/ask`-Hinweis
  überladen (`/ask` gehört zu E17-4). E5-1/E5-2 nach Phase C verschoben,
  damit der Vault-Index zeitlich zu seinem Konsumenten E17-1 passt.
- **Tags strukturiert (E4-2):** Das LLM gibt jetzt bis zu 5 kurze, lowercase
  Tags pro Notiz zurueck. Sie landen als YAML-Inline-Liste
  (`tags: [idea, fitness]`) im Frontmatter, sodass Obsidian sie direkt
  indexiert. Sanitizer im OpenAI-Provider erzwingt Lowercase, ersetzt
  Whitespace durch Hyphens, entfernt `#`-Prefixe und dedupliziert.
- **Append-Logik (Killer-Feature von Phase B):** Das LLM entscheidet pro
  Nachricht zwischen `action: "create"` (neue Notiz) und `action: "append"`
  (bestehende Notiz ergaenzen). Bei Append haengt der Vault-Writer einen
  `## Update YYYY-MM-DD`-Block an die vorhandene Markdown-Datei an, statt eine
  neue anzulegen. `ClassificationResult` bekommt dafuer die Felder `action`
  und `target_title`. Das Telegram-Reply ist `Ergänzt: [[Title]]` statt
  `Gespeichert als ...`. (#6, E3-2 + E4-1)
- `_sanitize_action` im OpenAI-Provider: halluziniert das LLM einen
  `target_title`, der nicht im Vault existiert, faellt das System transparent
  auf `action="create"` zurueck (mit Warn-Log) — kein Bot-Crash.
- Service-Layer-Fallback: existiert der DB-Eintrag fuer den Append-Target,
  aber die Vault-Datei wurde manuell geloescht, wird ebenfalls auf `create`
  zurueckgefallen statt einen `FileNotFoundError` zu werfen.
- Neuer Entry-Status `"appended"` und neue Writer-Funktion
  `append_to_note(vault_relative_path, result)`.
- Vision Phase E (Integrations & Ökosystem) in `ROADMAP.md`: Epics E13 (REST API),
  E14 (n8n), E15 (Vault Backends), E16 (Setup CLI); Stories E7-3/E7-4
  (Multi-LLM/Agenten); erweiterte Produktvision „Engine + Adapter".
- [ADR 0003](./docs/adr/0003-engine-and-adapters.md): Architekturentscheidung
  Headless Second-Brain-Engine mit Input/Output-Adaptern; Celery bleibt intern,
  n8n als Integrationsschicht; Keys nur lokal beim Setup.
- `docs/integrations/`: n8n-Anbindung (3 Stufen), Setup/Onboarding (TUI, doctor,
  Key-Handling), Vault-Backends (Obsidian optional, `VaultBackend`-Interface).
- Zentrale `Settings`-Klasse (`app/config.py`) auf Basis von
  `pydantic-settings`: alle Konfigurations-Werte werden typisiert aus
  Env-Variablen (und optional einer `.env`-Datei) gelesen. Pflichtfelder
  ohne Default sorgen für klaren Fail-Fast beim Start statt kryptischer
  `KeyError`-Crashes zur Laufzeit. Alle App-Module nutzen jetzt
  `from app.config import settings` statt verstreuter `os.environ[...]`-
  Lookups. `alembic/env.py` bleibt bewusst eigenständig. (#7)
- Vault-Writer wählt bei Titelkollision den nächsten freien Pfad im
  Obsidian-Stil (`Title.md`, `Title (2).md`, `Title (3).md`, …) statt
  existierende Notizen stillschweigend zu überschreiben. (#6)
- Service-Layer befüllt `entry.vault_path` mit dem relativen Pfad zur
  geschriebenen `.md`-Datei (z.B. `Ideas/Fitness App.md`); Fundament für
  künftige Append-/Update-Logik (E3-2).
- Update-Idempotenz: Webhook prüft `telegram_update_id` per indexed Lookup
  und verwirft Telegram-Retries still (kein doppeltes "Wird verarbeitet…").
  Der Service-Layer hat zusätzlich einen Pre-Check und einen `IntegrityError`-
  Fallback als Race-Schutz. Bei einem als Duplikat erkannten Update geht
  keine zweite Telegram-Bestätigung raus. (#8)
- Service-Layer befüllt jetzt `raw_input`, `telegram_chat_id`,
  `telegram_message_id`, `telegram_update_id` und `kind` (`text`/`voice`)
  bei jedem `Entry`. `vault_path` bleibt der Folge-Story E3-1 vorbehalten.
- `Entry`-Modell um sieben Felder erweitert: `raw_input`, `vault_path`,
  `telegram_chat_id` (Index), `telegram_message_id`, `telegram_update_id`
  (UNIQUE — Fundament für E1-2 Idempotenz), `kind` (Default `text`),
  `status` (Default `processed`). Service-Layer befüllt die neuen Felder noch
  nicht; das übernehmen die Folgestories E1-2 und E3-1. (#4, #5)
- Alembic-Migration `5caa4134853e_extend_entries_table.py`; nutzt
  `server_default` für `kind`/`status`, sodass bestehende Zeilen sauber
  backfilled werden.
- Telegram-Allowlist über `TELEGRAM_ALLOWED_USER_IDS` (komma-separiert).
  Wenn gesetzt, akzeptiert der Webhook nur Nachrichten von diesen Telegram-User-IDs;
  abgelehnte User erhalten "Dieser Bot ist privat." mit `200 OK`, damit Telegram
  keine Retries auslöst. Nicht gesetzt → Allowlist deaktiviert (Default,
  rückwärtskompatibel). (#1)
- `ROADMAP.md` — Vision, Phasen A–D, Epics mit User Stories und Bewertung
- `ARCHITECTURE.md` — High-Level-Diagramm, Modul-Map, Datenfluss, Conventions
- `CHANGELOG.md` — dieses Dokument
- `docs/setup.md` — Setup-Anleitung für lokale Entwicklung und Selfhoster
- `docs/adr/` — Architecture Decision Records inkl. Template
- `docs/adr/0001-async-engine-per-celery-task.md`
- `LICENSE` (MIT)
- `scripts/bootstrap_github.sh` — optionales Bootstrap für Labels, Milestones und Initial-Issues

### Changed
- `requirements.txt`: neue Dependency `pydantic-settings`.
- `tests/conftest.py`: setzt Test-Werte jetzt hart (Assignment statt
  `setdefault`), damit eine lokale `.env`-Datei (die pydantic-settings
  zusätzlich lädt) die Tests nicht verfälscht. Tests sind dadurch
  reproduzierbar unabhängig von der lokalen Entwickler-Umgebung.
- Celery-Tasks `process_text_message_task` und `process_voice_message_task`
  erhalten zwei optionale Parameter (`telegram_update_id`,
  `telegram_message_id`) — Default `None` für Rückwärtskompatibilität.
- `process_text_message` (Service) liefert jetzt `ClassificationResult | None`
  statt `ClassificationResult`. `None` = Duplikat, keine Bestätigung senden.
- `app/telegram/webhook.py`: `print(...)` durch `logger.warning(...)` ersetzt;
  Modul nutzt jetzt einheitliches Logging.

### Removed
- Dev-Endpunkte `POST /entries` und `GET /entries` aus `app/main.py` entfernt;
  ungeschützte Schreib-/Lese-Schnittstellen waren Reste aus Epic 2. (#2)
- `DEVELOPMENT.md` — Inhalt aufgeteilt auf README, ARCHITECTURE, CHANGELOG, ROADMAP und docs/setup.md

---

## [0.1.0] — 2026-05-27 — Initial pipeline

Erste lauffähige Version (Epic 1–7). Persönliches Lern-/Portfolio-Projekt.

### Added
- **Epic 1 — Grundlage**: FastAPI mit `GET /health`, Docker Compose (api), `.env.example`
- **Epic 2 — Datenbank**: SQLAlchemy `Entry`, Alembic-Migration `f153d8ce8963_create_entries_table`, async Postgres via `asyncpg`
- **Epic 3 — Webhook & Auth**: `POST /webhook`, Telegram-Secret-Validierung über Header `X-Telegram-Bot-Api-Secret-Token`, sofortige `200`-Antwort
- **Epic 4 — Text-Pipeline**: OpenAI-Klassifikation mit JSON-Mode (`gpt-4o-mini`), `ClassificationResult` (Pydantic), Vault-Writer mit Frontmatter
- **Epic 5 — Async & Voice**: Celery + Redis als Broker, Whisper-API für Voice, `worker_session()` mit eigener Engine pro Task gegen Event-Loop-Konflikte
- **Epic 6 — Vault-Kontext**: `list_existing_notes` lädt bestehende Notizen aus dem Vault, fließt in den Prompt ein, `related`-Titel werden gegen existierende Notizen validiert (`_sanitize_related`), `[[Links]]`-Sektion in neuen `.md`-Dateien
- **Epic 7 — Tests & CI**: pytest mit 19 Tests (Webhook, Vault Reader/Writer, LLM-Parsing), ruff, GitHub Actions CI

### Infrastructure
- Docker Compose mit 4 Services (`api`, `worker`, `db`, `redis`), Healthchecks für `db` und `redis`
- Vault-Bind-Mount über `OBSIDIAN_VAULT_HOST_PATH`
- `.gitignore` mit Schutz gegen `vault/`- und `models/`-Pattern-Konflikte (Root-Only)

[Unreleased]: https://github.com/LeekiGitHub/Seiton-Brain/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/LeekiGitHub/Seiton-Brain/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/LeekiGitHub/Seiton-Brain/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LeekiGitHub/Seiton-Brain/releases/tag/v0.1.0
