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

Ergebnis: eine gepflegte Markdown-Datei in meinem Obsidian-Vault, ohne dass ich Obsidian dafür öffne.

**Zweite Hälfte der Vision — Brain als Wissensquelle:** Erfasstes Wissen muss
auch wieder *raus*. Ich frage den Bot „Was weiß ich über X?", lasse mir Themen
zusammenfassen, oder lasse andere Systeme (n8n-Workflows, LLM-Agenten via
MCP/Tool-Use, ChatGPT/Claude Desktop) auf meinen Vault als Wissensbasis
zugreifen. Capture **und** Retrieve sind gleichwertige Produkthälften — ein
Second Brain, das man nur befüllen, aber nicht befragen kann, ist ein Archiv,
kein Brain. Siehe Epic **E17**.

Der Vault enthält dabei **nicht nur selbst geschriebene Notizen**, sondern alles,
was ein Second Brain anhäuft — Bewerbungen, Zeugnisse, Rechnungen, PDFs,
Office-Dokumente, Fotos. Seiton liest diese Dateien (read-only), extrahiert Text
und macht ihn über Retrieval & RAG befragbar. Priorisiert nach RAG-Tauglichkeit
(Text-Formate zuerst, Scans/Bilder via OCR/Vision später). Siehe Epic **E18**.

**Langfristige Produktvision:** Seiton Brain ist eine **self-hosted Second-Brain-Engine**.
Obsidian ist ein **Default-Vault-Backend**, Telegram ein **optionaler Eingang** —
nicht das gesamte Produkt. Andere Eingänge (UI, HTTP-API, CLI) und Ausgänge
(andere Vault-Backends, Retrieval/Q&A-API, MCP-Server) docken an, ohne den Kern
neu zu bauen.

### Produktstrategie (ab 2026-06) — kommerzielles Produkt

Seiton Brain wird als **kommerzielles, self-hosted Produkt für Privatpersonen**
weiterentwickelt — **einmal kaufen**, Kunde hostet selbst und verantwortet seine
Daten, nutzt seinen **eigenen LLM-Key** (BYO-Key). Wir betreiben nichts (keine
fremden Daten, keine Inferenzkosten, keine 24/7-Server-Verantwortung) und liefern
**Produkt + Bugfixes + Updates**. Privacy („deine Daten verlassen nie deine
Maschine") ist das zentrale Verkaufsargument.

Daraus folgt eine Schwerpunktverschiebung **von „mehr Features" zu „aus dem
Server-Stack ein konsumierbares Produkt machen"**:

- **UI-first als lokale Web-UI:** Oberfläche im Browser, **serviert vom
  Always-on-Host des Kunden** (nicht von uns) — plattformunabhängig (Mac/Win/
  Linux/Handy) und passend zum 24/7-Betrieb. Native Desktop-App ist **kein
  Nahziel**. Datenschutz: localhost/LAN + Fernzugriff via Tailscale o. Ä.
- **Leitbild Always-on-Box beim Kunden:** Heimserver / Mini-PC / Mac Mini
  (Privacy = Verkaufsargument). **VPS (z. B. IONOS) = spätere Alternative**, kein
  Nahziel. Fernzugriff ohne Router-Konfig via **Telegram Long-Polling** (E1-5).
- **Buy-once-Lizenzierung**, offline-validierbar (kein Server-Zwang) — geparkt,
  bis das Produkt steht.
- **Entfällt:** n8n-Custom-Node (REST-API bleibt für Power-User).

Architektur-Entscheidung: [ADR 0004 — Kommerzielles Produkt](./docs/adr/0004-commercial-consumer-product.md)
(ergänzt/überschreibt Teile von [ADR 0003 — Engine + Adapter](./docs/adr/0003-engine-and-adapters.md)).
**Repo & Lizenz (Portfolio jetzt, Verkauf später):** [ADR 0005](./docs/adr/0005-repo-and-license-strategy.md).
Integrations-Details: [`docs/integrations/`](./docs/integrations/).

---

## Phasen

| Phase | Ziel | Status |
|---|---|---|
| **A — MVP-Härtung** | Ich nutze es zuverlässig allein. Auth, saubere Datenhygiene, keine Überschreibung von Notizen. | 🟢 done |
| **B — Produktfunktionen** | Echtes Second-Brain-Verhalten: „bestehende Notiz ergänzen", Telegram-Commands, Tags. | ⚪ |
| **C — Robustheit & Self-Hosting** | Retries, Logging, Mac Mini als 24/7-Host (Cloudflare Tunnel statt ngrok). | ⚪ |
| **D — Public Release v1.0** | LICENSE, Setup-Doku für Selfhoster, optionaler Ollama-Provider. | ⚪ |
| **E — Integrations & Ökosystem** | REST-API, Vault-Backends, Multi-LLM-Agenten (optional). n8n-Eigenbau gestrichen (→ ADR 0004). | ⚪ |
| **F — Knowledge Retrieval & Q&A** | Brain wird befragbar: semantische Suche, RAG-Antworten, Retrieval-API + MCP-Server für Fremdagents. | ⚪ |
| **G — Produktisierung (kommerziell)** | UI/Dashboard, einfaches Multi-Plattform-Self-Hosting (Mac/Win/Linux/VPS), Packaging/Installer, Lizenzierung. Reduzierte Version → später Desktop-App. | 🔵 |

> **Hinweis (ADR 0004):** Mit dem Pivot zum kommerziellen Produkt verschiebt sich
> der Schwerpunkt Richtung **Phase G**. Die UI (Phase G) ist Voraussetzung dafür,
> dass Privatkunden Retrieval (Phase F) und Verwaltung überhaupt nutzen können —
> Phase F und G greifen daher ineinander.

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
| E1-3 | Telegram-Commands: `/start`, `/help`, `/recent`, `/find <q>`, `/undo`. | 4 | 2 | 1 | 3 | 4 | 🟢 | B |
| E1-4 | Webhook-Body-Size-Limit + Ignore unbekannter Update-Typen. | 2 | 1 | 2 | 2 | 2 | 🟢 | A |
| E1-5 | Long-Polling-Modus als Alternative zum Webhook (kein öffentlicher URL-/Tunnel-Zwang) — Voraussetzung für lokales Consumer-Hosting. | 5 | 2 | 2 | 4 | 4 | 🟢 | G |

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
| E3-2 | „Bestehende Notiz ergänzen": LLM-`action: create\|append`, Writer hängt unter `## Update YYYY-MM-DD` an. | 5 | 4 | 3 | 5 | 5 | 🟢 | B |
| E3-3 | Frontmatter-Updates bei Append (`updated:`, Tag-Merge). | 3 | 2 | 2 | 3 | 3 | 🟢 | B |
| E3-4 | Atomares Schreiben (Tempfile + `os.replace`), damit Obsidian-Sync keine halben Dateien sieht. | 3 | 1 | 2 | 4 | 3 | 🟢 | B |

---

### E4 — Classification & Routing · `epic:llm`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E4-1 | Prompt um `action` + `target_title` ergänzen (Append vs. Create). | 5 | 2 | 3 | 4 | 5 | 🟢 | B |
| E4-2 | Tags als strukturiertes Feld in `ClassificationResult` + Frontmatter. | 4 | 1 | 1 | 3 | 4 | 🟢 | B |
| E4-3 | Konfigurierbare Kategorien (`vault_config.yaml`) statt hardcoded `CATEGORY_FOLDERS`. | 3 | 2 | 2 | 3 | 3 | ⚪ | B |
| E4-4 | Prompt-Versionierung (`classify.v1.txt`, `classify.v2.txt`, `PROMPT_VERSION` in DB). | 2 | 1 | 1 | 4 | 2 | ⚪ | C |

---

### E5 — Existing-Notes Lookup · `epic:vault`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E5-1 | Vault-Index in Postgres spiegeln (Titel, Pfad, mtime); statt jedes Mal `rglob`. Voraussetzung für E17-1 (Keyword-Suche). | 3 | 3 | 3 | 4 | 3 | 🟢 | C |
| E5-2 | Heuristisches Pre-Filtering vor LLM (Token-Match, max. 30 Notizen). | 3 | 2 | 1 | 3 | 3 | ⚪ | C |
| E5-3 | (Optional v2) pgvector-Embeddings für semantische Ähnlichkeit. Geliefert zusammen mit E17-2 (Embedding-Provider + `embedding`-Spalte + pgvector). | 4 | 4 | 3 | 5 | 2 | 🟢 | E/F |

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
| E7-1 | Provider-unabhängige JSON-Validierung + Retry bei `JSONDecodeError`. | 3 | 2 | 2 | 4 | 3 | 🟢 | C |
| E7-2 | Ollama-Provider implementieren (gleiches Pydantic-Schema). | 3 | 3 | 3 | 5 | 3 | ⚪ | D-Bonus |
| E7-3 | Spezialisierte LLM-Rollen: Router (create/append), Writer (Summary/Tags), Linker (related) — je Prompt + Pydantic-Schema, max. 2–3 Steps im Core. | 4 | 3 | 2 | 5 | 3 | ⚪ | C/E |
| E7-4 | (Optional) Multi-LLM-Orchestrierung in n8n statt im Python-Core dokumentieren + Beispiel-Workflow. | 3 | 2 | 1 | 4 | 2 | ⚪ | E |

---

### E8 — Config & Environment · `epic:infra`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E8-1 | Zentrale `Settings`-Klasse (pydantic-settings) statt verstreuter `os.environ[...]`. | 4 | 2 | 1 | 4 | 4 | 🟢 | A |
| E8-2 | Klare Fehlermeldung beim Start, wenn Env fehlt. | 3 | 1 | 1 | 2 | 3 | 🟢 | A |

---

### E9 — Hosting / Deployment · `epic:infra`

> **Reframe (ADR 0004):** Der Mac-Mini-Spezialfall stammt aus der reinen
> Eigennutzungs-Zeit. Für das Produkt geht es um **mehrere Self-Hosting-Wege für
> Privatpersonen**: lokal (Mac/Windows/Linux) und VPS (z. B. IONOS) für
> Dauerbetrieb. Packaging/Installer der Consumer-Edition liegt in Epic **E20**.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E9-1 | Dockerfile härten: non-root user, multi-stage, `HEALTHCHECK`. | 3 | 2 | 2 | 4 | 3 | 🟢 | C |
| E9-2 | Multi-Plattform-Self-Hosting: Anleitungen + Compose-Profile für Mac/Windows/Linux **und** VPS (z. B. IONOS). Verallgemeinert den früheren „Mac Mini 24/7"-Plan. | 4 | 2 | 2 | 4 | 4 | 🟢 | G |
| E9-3 | Optionaler Remote-Zugang für VPS-Betrieb (Reverse-Proxy/Tunnel, TLS). Für lokales Consumer-Hosting **nicht** nötig (Long-Polling, E1-5). | 3 | 2 | 2 | 3 | 3 | ⚪ | G |
| E9-4 | Backups: Postgres-Dump + Vault-Snapshot (lokal). | 3 | 2 | 2 | 3 | 3 | 🟢 | C |
| E9-5 | (Eval) Vereinfachter Stack für Consumer-Edition: SQLite statt Postgres, in-process Worker statt Redis/Celery — weniger bewegliche Teile beim Endnutzer. Server-/VPS-Edition behält vollen Stack. Offen: eine vs. zwei Editionen (ADR 0004). | 4 | 4 | 4 | 5 | 3 | ⚪ | G |

---

### E10 — Logging, Error Handling, Reliability · `epic:infra`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E10-1 | Strukturiertes Logging (JSON, Task-ID-Korrelation). | 3 | 2 | 1 | 4 | 4 | 🟢 | C |
| E10-2 | Celery-Retries mit Backoff für OpenAI/Whisper (`autoretry_for`). | 4 | 2 | 2 | 4 | 4 | 🟢 | B |
| E10-3 | Error-Forward via Telegram-DM an Admin (statt nur Log). | 3 | 2 | 1 | 3 | 3 | 🟢 | C |
| E10-4 | Health-Endpunkt prüft DB + Redis. | 2 | 1 | 1 | 2 | 2 | 🟢 | C |

---

### E11 — Public Repo Readiness · `epic:public-ready`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E11-1 | `LICENSE` (MIT). | 5 | 1 | 1 | 1 | 5 | 🟢 | A |
| E11-2 | `SECURITY.md` (wo melden) + Threat-Model-Notiz. | 2 | 1 | 1 | 2 | 2 | 🟢 | D |
| E11-3 | `CONTRIBUTING.md` + Issue-/PR-Templates. | 2 | 1 | 1 | 2 | 2 | 🟢 | D |
| E11-4 | Repo-Topics, Screenshots, GIF im README. | 2 | 1 | 1 | 1 | 2 | ⚪ | D |

---

### E12 — Documentation & Onboarding · `epic:docs`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E12-1 | `docs/setup.md`: Bot-Token holen, Webhook setzen, Vault mounten. | 4 | 2 | 1 | 2 | 4 | 🟡 | A |
| E12-2 | `ARCHITECTURE.md`: Diagramm + Modul-Map. | 3 | 1 | 1 | 2 | 4 | 🟡 | A |
| E12-3 | Troubleshooting-Sektion (ngrok-Restart, Migration-Fehler etc.). | 3 | 1 | 1 | 2 | 3 | 🟢 | D |
| E12-4 | ADR-Verzeichnis (`docs/adr/`) + Template. | 3 | 1 | 1 | 3 | 4 | 🟡 | A |

---

### E13 — REST API & Events · `epic:api`

Voraussetzung für n8n, externe Tools und spätere Custom Nodes. Engine bleibt
intern; API ist dünner Adapter nach außen.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E13-1 | REST-API v1: `POST /v1/capture`, `POST /v1/classify`, `GET /v1/entries` — gleiche Pipeline wie Telegram. | 5 | 3 | 2 | 5 | 4 | 🟢 | C |
| E13-2 | API-Key-Auth (`SEITON_API_KEY` in `.env`, Header `X-Seiton-Api-Key`). | 4 | 1 | 1 | 3 | 4 | 🟢 | C |
| E13-3 | Outbound Webhooks: `note.created`, `note.appended`, `entry.failed` (URL in Settings). | 4 | 2 | 2 | 4 | 3 | 🟢 | E |
| E13-4 | OpenAPI/Swagger-Dokumentation unter `/docs` (nur wenn API-Key gesetzt / DEBUG). | 2 | 1 | 1 | 2 | 2 | 🟢 | D |

Details: [`docs/integrations/n8n.md`](./docs/integrations/n8n.md)

---

### E14 — n8n-Ökosystem · `epic:n8n` · ❌ GESTRICHEN (ADR 0004)

> **Status: gestrichen für das Produkt.** Eine eigene n8n-Community-Node zu bauen
> und zu pflegen (eigenes Repo, npm-Releases, n8n-Review) bringt Privatkunden
> keinen Mehrwert und erzeugt nur Wartungslast. **Die REST-API (E13) bleibt** —
> Power-User können n8n jederzeit selbst per HTTP-Request-Node anbinden, ohne
> dass wir etwas dafür maintainen. Siehe [ADR 0004](./docs/adr/0004-commercial-consumer-product.md).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E14-1 | `examples/n8n/`: Workflow-JSONs für Power-User (kein Produktversprechen) | — | — | — | — | — | 🟢 | E |
| E14-2 | ~~Community-Node `n8n-nodes-seiton-brain`~~ | — | — | — | — | — | ❌ | — |
| E14-3 | Doku „Seiton + n8n" (REST-first, kein Custom Node) | — | — | — | — | — | 🟢 | E |

**Repo-Strategie:** Public Portfolio jetzt, kommerzielle Edition später — [ADR 0005](./docs/adr/0005-repo-and-license-strategy.md).

---

### E15 — Vault Backends · `epic:vault`

Obsidian = Markdown-Ordner. Weitere Backends über Interface — keine eigene
Notiz-App als Obsidian-Ersatz.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E15-1 | `VaultBackend`-Protocol; Filesystem-Implementierung extrahiert aus reader/writer. | 4 | 3 | 2 | 5 | 3 | ⚪ | D |
| E15-2 | Doku: „Obsidian optional“ — jeder Markdown-Ordner reicht (`vault.example/`). | 3 | 1 | 1 | 2 | 3 | ⚪ | D |
| E15-3 | (Optional) Git-backed Vault: Commit pro Note / konfigurierbarer Push. | 3 | 3 | 3 | 4 | 2 | ⚪ | E |
| E15-4 | ~~(Optional) Read-only Web-UI für Vault-Browse~~ → **aufgegangen in Epic E19 (UI/Dashboard)**. | — | — | — | — | — | ➡️ E19 | G |

Details: [`docs/integrations/vault-backends.md`](./docs/integrations/vault-backends.md)

---

### E16 — Setup & Onboarding CLI · `epic:public-ready`

Easy Setup für Selfhoster. **Keys nur lokal** — nie Remote-Install mit Key-Upload.

> **Reframe (ADR 0004):** Für das Consumer-Produkt verschiebt sich Onboarding von
> CLI/TUI in die **grafische UI** (Setup-Wizard, Epic **E19**). Die CLI-Stufen
> bleiben relevant für die Server-/VPS-Edition und Power-User; `seiton doctor`
> (E16-2) bleibt als Diagnose nützlich. `init`-TUI (E16-3) und Browser-Setup
> (E16-4) werden durch den UI-Wizard weitgehend abgelöst.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E16-1 | `scripts/init.sh` / `make init`: `.env` aus Example, Vault-Ordner, Docker-Hinweise — ohne Secrets abfragen. | 4 | 1 | 1 | 2 | 4 | ⚪ | D |
| E16-2 | `seiton doctor`: prüft `.env`, DB, Redis, Vault-Pfad, optional OpenAI/Telegram. | 4 | 2 | 1 | 3 | 4 | 🟢 | D |
| E16-3 | `seiton init` TUI: interaktiv `.env` schreiben (lokal, kein Netzwerk-Upload). | 4 | 2 | 1 | 3 | 3 | ⚪ | D/E |
| E16-4 | (Optional) Browser-Setup `localhost:8000/setup` — einmalig, nur localhost. | 2 | 3 | 2 | 3 | 1 | 🟢 | E |
| E16-5 | (Optional) At-Rest-Key-Schutz via OS-Keystore (`keyring` → macOS Keychain / Windows Credential Manager / libsecret). `seiton init` legt Keys im Store ab; Launcher injiziert sie beim `docker compose up` als Env statt Klartext-`.env`. Baut auf E16-3. | 3 | 4 | 3 | 4 | 2 | ⚪ | E |

Bewusst **nicht** in E16: universeller Dependency-Installer (kein Auto-Install von
Python/Docker/Obsidian über brew/winget/choco/apt/… — zu fragil, hoher Wartungsaufwand,
und durch Docker ohnehin grösstenteils überflüssig). Stattdessen **detect + guide**:
OS erkennen, prüfen ob Docker läuft, sonst OS-spezifischen Hinweis + Download-Link.
Obsidian bleibt eine separat installierte (und laut E15-2 optionale) App. Kein
OAuth-/Device-Flow für OpenAI/Telegram möglich (Provider bieten ihn nicht) — Vertrauen
entsteht über lokale Speicherung, auditierbaren Open-Source-Code und klare Kommunikation.

---

### E17 — Knowledge Retrieval & Q&A · `epic:retrieval`

Brain als **Wissensquelle**, nicht nur als Schreibtisch. Stufenweise von
Keyword-Liste über semantische Suche bis zu RAG-Antworten und externer
Programmatic-Access-Schicht (MCP / Tool-Use für LLM-Agenten). Baut auf
E5-3 (pgvector), E13 (REST-API) und E15 (`VaultBackend`-Interface) auf.

Default-Adapter: Telegram (`/ask`). Weitere Konsumenten: REST-API,
n8n-Workflows, externe LLM-Agenten via MCP — alle gegen denselben
Retrieval-Service.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E17-1 | Keyword-Suche über Vault-Index (DB-gespiegelt aus E5-1): Titel/Body-Match, Top-N Resultate mit `vault_path` + Snippet. Fundament für `/find` und `/v1/notes/search`. | 4 | 2 | 1 | 3 | 4 | 🟢 | C |
| E17-2 | Semantische Suche via pgvector (setzt E5-3 voraus): Embedding pro Notiz beim Schreiben/Append, Query-Embedding, kNN-Retrieval. | 5 | 4 | 3 | 5 | 3 | 🟢 | E/F |
| E17-3 | RAG-Antwort-Service: Retrieval (E17-1/2) → Prompt mit Kontext-Snippets + Quellen → LLM-Antwort mit `[[Wiki-Links]]` zu Source-Notes. Eigener Pydantic-Schema (`AnswerResult`: `answer`, `sources[]`, `confidence`). | 5 | 4 | 3 | 5 | 4 | 🟢 | F |
| E17-4 | Telegram-Command `/ask <frage>`: nutzt E17-3, Antwort im Chat mit anklickbaren Source-Links zur Vault-Notiz. | 5 | 2 | 2 | 4 | 4 | 🟢 | F |
| E17-5 | Retrieval-API: `POST /v1/ask` (RAG-Antwort), `GET /v1/notes/search?q=...&semantic=true` (Treffer-Liste). Gleiche API-Key-Auth wie E13-2. | 5 | 3 | 2 | 4 | 4 | 🟢 | F |
| E17-6 | MCP-Server `seiton-brain-mcp` (`examples/mcp/`): exponiert `search_notes`, `ask_brain`, `get_note` als MCP-Tools für Claude Desktop / Cursor / LLM-Agenten. Authentifiziert per `SEITON_API_KEY` gegen die REST-API. | 5 | 4 | 3 | 5 | 3 | 🟢 | F |
| E17-7 | Outbound-Event `note.indexed` (für n8n-Trigger nach Embedding-Berechnung) + Doku „Brain als Knowledge-Backend in n8n-/Agent-Workflows". | 3 | 2 | 2 | 3 | 2 | 🟢 | F |
| E17-8 | (Optional) Aggregierte Sichten: `/digest <thema>` / `POST /v1/digest` — LLM-Synthese mehrerer verwandter Notizen (Wochenrückblick, Themen-Brief). | 4 | 3 | 2 | 4 | 2 | 🟢 | F-Bonus |

Bewusst **nicht** in E17: eigene Such-UI (Obsidian-Suche bleibt für Browsing
zuständig); Re-Implementierung von Embedding-Berechnung außerhalb des Engine-
Cores; ungeschützter Public-Endpunkt (Retrieval ist genauso sensibel wie
Capture — Auth identisch zu E13-2).

Details: [`docs/integrations/knowledge-retrieval.md`](./docs/integrations/knowledge-retrieval.md)

---

### E18 — Multi-Format Ingestion · `epic:ingestion`

Vault = **echtes Second Brain**: nicht nur Markdown, sondern alles, was sich
ansammelt — Bewerbungen, Zeugnisse, Rechnungen, PDFs, Office-Dokumente, Fotos.
Seiton **liest** diese Dateien (verändert sie nie), extrahiert Text, chunkt ihn
und speist ihn in den Vault-Index (E5-1) ein, damit Retrieval & RAG (E17) über
**alle** Inhalte arbeiten — nicht nur über selbst geschriebene Notizen.

Priorisierung nach **RAG-Tauglichkeit** (Text first, Bild/Scan später):

- **Tier 1 — direkt RAG-tauglich (Text-Layer vorhanden):** `.md` ✅, `.txt`,
  PDF mit Text-Layer, `.docx`, `.pptx`
- **Tier 2 — Scans/Foto-Dokumente (brauchen OCR):** gescannte PDFs, abfotografierte
  Zeugnisse/Rechnungen
- **Tier 3 — reine Bilder (brauchen Vision-Modell):** Fotos ohne Text

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E18-1 | `DocumentExtractor`-Interface (Engine+Adapter) + Plain-Text/Markdown-Extractor. Vault-Index (E5-1) erfasst auch Nicht-`.md`-Dateien: `vault_path`, `doc_type`, extrahierter Text, `indexed_at`. | 4 | 3 | 2 | 4 | 4 | 🟢 | C |
| E18-2 | PDF-Text-Extraktion (Text-Layer via `pypdf`). Erkennt „kein Text-Layer" → markiert (`doc_type=pdf_no_text`) für OCR (E18-5). | 5 | 2 | 2 | 3 | 4 | 🟢 | C |
| E18-3 | Office-Formate: `.docx` (`python-docx`), `.pptx` (`python-pptx`). | 4 | 2 | 2 | 3 | 3 | 🟢 | F |
| E18-4 | Chunking großer Dokumente in retrieval-taugliche Abschnitte; Index-Schema von 1 Zeile/Notiz → N Chunks/Dokument (eigene `vault_chunk`-Tabelle). Voraussetzung für sinnvolles semantisches Retrieval (E17-2/3) über lange Dateien. | 4 | 3 | 3 | 4 | 3 | ⚪ | F |
| E18-5 | OCR für gescannte PDFs / Foto-Dokumente (Zeugnisse, Rechnungen) via Tesseract (`pytesseract`) — optionaler Adapter, nur wenn installiert. | 4 | 4 | 3 | 4 | 2 | ⚪ | F-Bonus |
| E18-6 | Vision-LLM für reine Foto-Inhalte: Bildbeschreibung + Tags als durchsuchbare Text-Repräsentation im Index. | 3 | 4 | 3 | 4 | 2 | ⚪ | F-Bonus |

Abhängigkeiten: **E5-1** (Vault-Index ✅) als Speicherziel, **E17-2** (Embeddings)
und **E17-3** (RAG) als Konsumenten des extrahierten Texts. Sinnvolle Reihenfolge:
E18-1 → E18-2/3 (Text-Formate) → E17-2 (Semantik) → E18-4 (Chunking) → E17-3 (RAG),
danach OCR/Vision (E18-5/6) als Bonus.

Bewusst **nicht** in E18: Originaldateien verändern oder neu schreiben (Dateien
kommen über Obsidian/Sync rein, Seiton liest nur); Seiton als Upload-Ziel/Dateimanager;
verlustfreie Format-Konvertierung. Fokus ist reine **Text-Gewinnung für Retrieval**.

---

### E19 — UI / Dashboard · `epic:ui`

Grafische Oberfläche als **Hauptsurface des Produkts** (ADR 0004). Macht Seiton
für Privatpersonen ohne Terminal/Obsidian nutzbar. Löst E15-4 (read-only Web-UI)
ab und nimmt den Setup-Wizard aus E16 auf.

> **Architektur-Abgrenzung:** Dashboard/Management/Retrieval-UI — **kein**
> vollwertiger Obsidian-Ersatz-Editor (ADR 0003/0004). Beginnt read-/manage-first.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E19-1 | Setup-Wizard in der UI: Vault-Ordner wählen, LLM-Key + (optional) Telegram eintragen, Verbindung testen. Ersetzt CLI/TUI-Onboarding für Consumer. | 5 | 3 | 2 | 4 | 5 | 🟢 | G |
| E19-2 | Dashboard: Entries/Notizen ansehen, Status, letzte Aktivität. | 5 | 3 | 2 | 4 | 5 | 🟢 | G |
| E19-3 | Suche + `/ask`-Chat in der UI (Konsument von E17 Retrieval/RAG). | 5 | 3 | 2 | 4 | 4 | 🟢 | G |
| E19-4 | Verwalten: Notiz öffnen/bearbeiten/löschen, Tags/Kategorien, Vault-Konfig. | 4 | 4 | 3 | 4 | 3 | 🟢 | G |
| E19-5 | Settings-UI: Keys/Provider, Kategorien, Backup, Edition-Optionen. | 3 | 2 | 2 | 3 | 3 | 🟢 | G |

Offen: Tech-Stack der UI — **E19-1:** FastAPI + Jinja2 + Vanilla-JS unter `/setup` (localhost-only).

---

### E20 — Packaging & Distribution · `epic:packaging`

Aus dem Stack ein **konsumierbares Produkt** machen — der eigentliche Hebel für
„passives Einkommen". Reduzierte Version zuerst, vollwertige Desktop-App zum
offiziellen Release (ADR 0004).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E20-1 | Reduzierte Version: stark vereinfachtes Setup / gebündelter Installer für die Heim-Box (Mac/Windows/Linux). | 5 | 4 | 4 | 5 | 5 | 🟢 | G |
| E20-2 | (Später) VPS-Deployment-Pfad (z. B. IONOS): Skript-Setup für Dauerbetrieb. | 4 | 3 | 3 | 4 | 2 | 🟢 | G+ |
| E20-3 | ~~Vollwertige native Desktop-App~~ — **kein Nahziel** (Web-UI E19 deckt den Bedarf ab, ADR 0004). Nur falls später echter Bedarf. | 2 | 5 | 4 | 4 | 1 | ⚪ | G+ |
| E20-4 | Auto-Update-Mechanismus (liefert Bugfixes/Updates an Kunden aus). | 4 | 3 | 3 | 4 | 3 | 🟢 | G |
| E20-5 | Code-Signing / Notarization (nur relevant, falls native App; sonst entbehrlich). | 2 | 3 | 3 | 3 | 1 | ⚪ | G+ |

---

### E21 — Commercial / Licensing · `epic:commercial`

Verkaufsmechanik für **buy-once**, ohne dass wir Server betreiben (ADR 0004).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E21-1 | Lizenz-Key: Format + **offline-validierbare** Prüfung (kein Server-Zwang). | 5 | 4 | 3 | 4 | 4 | 🟢 | G |
| E21-2 | Verkaufskanal (Eigenshop/Store) + Lizenz-Ausgabe an Käufer. | 4 | 3 | 2 | 3 | 3 | ⚪ | G+ |
| E21-3 | Klare Lizenz-/Edition-Kommunikation (was ist im Kauf enthalten, Update-Politik). | 3 | 1 | 1 | 2 | 3 | 🟢 | G+ |

Offen: genaue Lizenz-Mechanik, Update-Auslieferung, evtl. Edition-Stufen (ADR 0004).

---

## Aktueller Sprint (Phase A — MVP-Härtung) ✅ abgeschlossen

1. 🟢 **Doku-Fundament**: ROADMAP, ARCHITECTURE, CHANGELOG, ADR-Struktur, LICENSE, setup-Doku
2. 🟢 **E1-1** — Allowlist
3. 🟢 **E2-3** — Dev-Endpunkte entfernen
4. 🟢 **E2-1 + E2-2** — Entry-Modell erweitern + Migration
5. 🟢 **E1-2** — Update-Idempotenz
6. 🟢 **E3-1** — Filename-Kollision verhindern
7. 🟢 **E8-1** — Settings-Klasse (pydantic-settings)

## Aktueller Sprint (Phase B — Produktfunktionen)

1. 🟢 **E4-1 + E3-2** — Append-Logik (Killer-Feature)
2. 🟢 **E4-2** — Tags als strukturiertes Feld
3. 🟢 **E3-3** — Frontmatter-Updates bei Append (`updated:`-Datum, Tag-Merge)
4. 🟢 **E10-2** — Celery-Retries für OpenAI/Whisper (Reliability-Boost)
5. 🟢 **E1-3** — Telegram-Commands (`/start`, `/help`, `/recent`, `/find`, `/undo`)
6. 🟢 **E3-4** — Atomares Schreiben (Tempfile + `os.replace`)
7. 🟢 **E1-4** — Webhook-Body-Size-Limit + Ignore unbekannter Update-Typen

**Phase A (MVP) und Phase B (Product) sind komplett — Release v0.2.0.**
**Phase C** läuft: E10-4, E10-1, E8-2, E13-1, E13-2, E7-1, E9-1, E10-3, E9-4, E13-3, E14-1, E5-1, E17-1 🟢.
Mac-Mini-spezifisch (E9-3 Remote-Zugang) optional; **E9-2** Self-Hosting-Hub 🟢.

## Spätere Phasen (Kurzüberblick)

| Phase | Fokus | Wichtigste Epics |
|-------|-------|------------------|
| **C** | Robustheit, Self-Hosting, REST-API | E9, E10, **E13** (API v1) |
| **D** | Setup, Doku, Public-Readiness | E11, E12, **E16**, E7-2 |
| **E** | Ökosystem | **E15** Vault-Backends, E7-3/4, **E17-1/2** Suche (n8n-Eigenbau gestrichen, ADR 0004) |
| **F** | Brain als Wissensquelle | **E17-3/4** RAG + `/ask`, **E17-5** Retrieval-API, **E17-6** MCP-Server, **E17-8** Digest |
| **G** | Produktisierung (kommerziell) | **E19** UI/Dashboard, **E20** Packaging/Distribution, **E21** Lizenzierung, **E1-5** Long-Polling, **E9-2/5** Multi-Plattform/Stack |

Integrations-Vision und Szenarien: [`docs/integrations/`](./docs/integrations/).

---

## Definition of Done (pro Story)

- [ ] Code-Änderung klein und fokussiert
- [ ] Tests vorhanden (oder bewusste Begründung warum nicht)
- [ ] `ruff check` und `pytest` grün
- [ ] CHANGELOG-Eintrag unter `[Unreleased]`
- [ ] ROADMAP-Status aktualisiert
- [ ] Manuell getestet: Telegram → Vault → Datei sichtbar
