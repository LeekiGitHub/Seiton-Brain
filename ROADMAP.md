# Roadmap

Lebendes Dokument. Status-Updates per PR. Detaillierte Tickets liegen in **GitHub Issues** (Labels `epic:*`, `phase:*`, `priority:*`).

Status-Legende: 🟢 Done · 🟡 In Progress · 🔵 Ready (nächster Sprint) · ⚪ Backlog

---

## Vision

Ich schicke dem Bot per Telegram (Text oder Sprache) einen Gedanken — eine halbe Idee, eine Aufgabe, einen Ausschnitt. Das System entscheidet selbständig:

- **Neue Notiz oder bestehende ergänzen?**
- **Welche Kategorie / welches Vault-Verzeichnis?**
- **Welche bestehenden Notizen sind verwandt → `[[Links]]`?**
- **Titel, Zusammenfassung, Tags?**

Ergebnis: eine gepflegte Markdown-Datei in meinem Obsidian-Vault, ohne dass ich Obsidian dafür öffne. Langfristig public-ready, sodass andere mit eigenem OpenAI-Key selbst hosten können.

---

## Phasen

| Phase | Ziel | Status |
|---|---|---|
| **A — MVP-Härtung** | Ich nutze es zuverlässig allein. Auth, saubere Datenhygiene, keine Überschreibung von Notizen. | 🟢 done |
| **B — Produktfunktionen** | Echtes Second-Brain-Verhalten: „bestehende Notiz ergänzen", Telegram-Commands, Tags. | ⚪ |
| **C — Robustheit & Self-Hosting** | Retries, Logging, Mac Mini als 24/7-Host (Cloudflare Tunnel statt ngrok). | ⚪ |
| **D — Public Release v1.0** | LICENSE, Setup-Doku für Selfhoster, optionaler Ollama-Provider. | ⚪ |

---

## Epics

Jedes Epic ist ein GitHub-Label (`epic:<key>`). Stories darunter sind Issue-Titel-Vorlagen.

Bewertung pro Story: **N**utzen / **S**chwierigkeit / **R**isiko / **L**ernwert / **P**riorität · jeweils 1–5 (5 = hoch).

---

### E1 — Telegram Input & Webhook-Härtung · `epic:telegram`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E1-1 | Allowlist: nur konfigurierte Telegram-User-IDs dürfen Nachrichten senden (`TELEGRAM_ALLOWED_USER_IDS`). | 5 | 1 | 1 | 2 | 5 | 🟢 | A |
| E1-2 | Update-Idempotenz: gleiche `update_id` wird nur einmal verarbeitet (DB-Unique). | 4 | 2 | 2 | 4 | 4 | 🟢 | A |
| E1-3 | Telegram-Commands: `/start`, `/help`, `/recent`, `/find <q>`, `/undo`. | 4 | 2 | 1 | 3 | 4 | ⚪ | B |
| E1-4 | Webhook-Body-Size-Limit + Ignore unbekannter Update-Typen. | 2 | 1 | 2 | 2 | 2 | ⚪ | A |

---

### E2 — Datenmodell & Persistenz · `epic:db`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E2-1 | `Entry` erweitern: `telegram_chat_id`, `telegram_message_id`, `telegram_update_id` (unique), `raw_input`, `vault_path`, `status`, `kind` (text/voice). | 5 | 2 | 2 | 4 | 5 | 🟢 | A |
| E2-2 | Alembic-Migration für E2-1, backfill-tauglich. | 3 | 2 | 2 | 4 | 4 | 🟢 | A |
| E2-3 | Dev-Endpunkte `POST/GET /entries` aus `main.py` entfernen (oder hinter `DEBUG=1`). | 3 | 1 | 1 | 2 | 4 | 🟢 | A |

---

### E3 — Vault: Konflikte & Updates · `epic:vault`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E3-1 | Filename-Kollision verhindern: keine stillschweigende Überschreibung. | 5 | 2 | 3 | 3 | 5 | 🟢 | A |
| E3-2 | „Bestehende Notiz ergänzen": LLM-`action: create\|append`, Writer hängt unter `## Update YYYY-MM-DD` an. | 5 | 4 | 3 | 5 | 5 | ⚪ | B |
| E3-3 | Frontmatter-Updates bei Append (`updated:`, Tag-Merge). | 3 | 2 | 2 | 3 | 3 | ⚪ | B |
| E3-4 | Atomares Schreiben (Tempfile + `os.replace`), damit Obsidian-Sync keine halben Dateien sieht. | 3 | 1 | 2 | 4 | 3 | ⚪ | B |

---

### E4 — Classification & Routing · `epic:llm`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E4-1 | Prompt um `action` + `target_title` ergänzen (Append vs. Create). | 5 | 2 | 3 | 4 | 5 | ⚪ | B |
| E4-2 | Tags als strukturiertes Feld in `ClassificationResult` + Frontmatter. | 4 | 1 | 1 | 3 | 4 | ⚪ | B |
| E4-3 | Konfigurierbare Kategorien (`vault_config.yaml`) statt hardcoded `CATEGORY_FOLDERS`. | 3 | 2 | 2 | 3 | 3 | ⚪ | B |
| E4-4 | Prompt-Versionierung (`classify.v1.txt`, `classify.v2.txt`, `PROMPT_VERSION` in DB). | 2 | 1 | 1 | 4 | 2 | ⚪ | C |

---

### E5 — Existing-Notes Lookup · `epic:vault`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E5-1 | Vault-Index in Postgres spiegeln (Titel, Pfad, mtime); statt jedes Mal `rglob`. | 3 | 3 | 3 | 4 | 3 | ⚪ | B |
| E5-2 | Heuristisches Pre-Filtering vor LLM (Token-Match, max. 30 Notizen). | 3 | 2 | 1 | 3 | 3 | ⚪ | B |
| E5-3 | (Optional v2) pgvector-Embeddings für semantische Ähnlichkeit. | 4 | 4 | 3 | 5 | 2 | ⚪ | später |

---

### E6 — Voice Support · `epic:voice`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E6-1 | Voice-File-Size-Limit + freundliche Fehlermeldung. | 3 | 1 | 1 | 2 | 3 | ⚪ | C |
| E6-2 | Audio temporär persistieren bis Erfolg (Replay bei Crash). | 2 | 2 | 2 | 3 | 2 | ⚪ | C |
| E6-3 | `language`-Hint für Whisper (env-konfigurierbar). | 2 | 1 | 1 | 2 | 2 | ⚪ | C |
| E6-4 | (Optional) Lokaler Whisper via `whisper.cpp` auf Mac Mini → Cost-Ersparnis. | 3 | 3 | 2 | 4 | 2 | ⚪ | D-Bonus |

---

### E7 — LLM Provider Abstraktion · `epic:llm`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E7-1 | Provider-unabhängige JSON-Validierung + Retry bei `JSONDecodeError`. | 3 | 2 | 2 | 4 | 3 | ⚪ | C |
| E7-2 | Ollama-Provider implementieren (gleiches Pydantic-Schema). | 3 | 3 | 3 | 5 | 3 | ⚪ | D-Bonus |

---

### E8 — Config & Environment · `epic:infra`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E8-1 | Zentrale `Settings`-Klasse (pydantic-settings) statt verstreuter `os.environ[...]`. | 4 | 2 | 1 | 4 | 4 | 🟢 | A |
| E8-2 | Klare Fehlermeldung beim Start, wenn Env fehlt. | 3 | 1 | 1 | 2 | 3 | ⚪ | A |

---

### E9 — Hosting / Deployment · `epic:infra`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E9-1 | Dockerfile härten: non-root user, multi-stage, `HEALTHCHECK`. | 3 | 2 | 2 | 4 | 3 | ⚪ | C |
| E9-2 | Mac Mini M4 als 24/7-Host: Anleitung + Compose-Override. | 4 | 2 | 2 | 4 | 4 | ⚪ | C |
| E9-3 | Cloudflare Tunnel statt ngrok (stabile öffentliche URL). | 4 | 2 | 2 | 4 | 4 | ⚪ | C |
| E9-4 | Backups: Postgres-Dump + Vault-Snapshot (lokal). | 3 | 2 | 2 | 3 | 3 | ⚪ | C |

---

### E10 — Logging, Error Handling, Reliability · `epic:infra`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E10-1 | Strukturiertes Logging (JSON, Task-ID-Korrelation). | 3 | 2 | 1 | 4 | 4 | ⚪ | C |
| E10-2 | Celery-Retries mit Backoff für OpenAI/Whisper (`autoretry_for`). | 4 | 2 | 2 | 4 | 4 | ⚪ | B |
| E10-3 | Error-Forward via Telegram-DM an Admin (statt nur Log). | 3 | 2 | 1 | 3 | 3 | ⚪ | C |
| E10-4 | Health-Endpunkt prüft DB + Redis. | 2 | 1 | 1 | 2 | 2 | ⚪ | C |

---

### E11 — Public Repo Readiness · `epic:public-ready`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E11-1 | `LICENSE` (MIT). | 5 | 1 | 1 | 1 | 5 | 🔵 | A |
| E11-2 | `SECURITY.md` (wo melden) + Threat-Model-Notiz. | 2 | 1 | 1 | 2 | 2 | ⚪ | D |
| E11-3 | `CONTRIBUTING.md` + Issue-/PR-Templates. | 2 | 1 | 1 | 2 | 2 | ⚪ | D |
| E11-4 | Repo-Topics, Screenshots, GIF im README. | 2 | 1 | 1 | 1 | 2 | ⚪ | D |

---

### E12 — Documentation & Onboarding · `epic:docs`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E12-1 | `docs/setup.md`: Bot-Token holen, Webhook setzen, Vault mounten. | 4 | 2 | 1 | 2 | 4 | 🟡 | A |
| E12-2 | `ARCHITECTURE.md`: Diagramm + Modul-Map. | 3 | 1 | 1 | 2 | 4 | 🟡 | A |
| E12-3 | Troubleshooting-Sektion (ngrok-Restart, Migration-Fehler etc.). | 3 | 1 | 1 | 2 | 3 | ⚪ | D |
| E12-4 | ADR-Verzeichnis (`docs/adr/`) + Template. | 3 | 1 | 1 | 3 | 4 | 🟡 | A |

---

## Aktueller Sprint (Phase A — MVP-Härtung) ✅ abgeschlossen

1. 🟢 **Doku-Fundament**: ROADMAP, ARCHITECTURE, CHANGELOG, ADR-Struktur, LICENSE, setup-Doku
2. 🟢 **E1-1** — Allowlist
3. 🟢 **E2-3** — Dev-Endpunkte entfernen
4. 🟢 **E2-1 + E2-2** — Entry-Modell erweitern + Migration
5. 🟢 **E1-2** — Update-Idempotenz
6. 🟢 **E3-1** — Filename-Kollision verhindern
7. 🟢 **E8-1** — Settings-Klasse (pydantic-settings)

## Nächster Sprint (Phase B — Produktfunktionen)

Killer-Feature steht an. Reihenfolge:

1. 🔵 **E4-1** — Prompt erweitern um `action: create | append` + `target_title`
2. 🔵 **E3-2** — Vault-Writer: bei `action=append` an bestehende Notiz unter `## Update YYYY-MM-DD` anhängen (nutzt `vault_path` aus E3-1)
3. ⚪ **E3-3** — Frontmatter-Updates bei Append (`updated:`-Datum, Tag-Merge)
4. ⚪ **E4-2** — Tags als strukturiertes Feld
5. ⚪ **E10-2** — Celery-Retries für OpenAI/Whisper (Reliability-Boost)

---

## Definition of Done (pro Story)

- [ ] Code-Änderung klein und fokussiert
- [ ] Tests vorhanden (oder bewusste Begründung warum nicht)
- [ ] `ruff check` und `pytest` grün
- [ ] CHANGELOG-Eintrag unter `[Unreleased]`
- [ ] ROADMAP-Status aktualisiert
- [ ] Manuell getestet: Telegram → Vault → Datei sichtbar
