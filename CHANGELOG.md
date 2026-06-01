# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt landen hier.

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/), Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased]

### Added
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

[Unreleased]: https://github.com/LeekiGitHub/Seiton-Brain/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LeekiGitHub/Seiton-Brain/releases/tag/v0.1.0
