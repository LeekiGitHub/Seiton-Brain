# Roadmap

Lebendes Dokument. Status-Updates per PR. Detaillierte Tickets liegen in **GitHub Issues** (Labels `epic:*`, `phase:*`, `priority:*`).

Status-Legende: 🟢 Done · 🟡 In Progress · 🔵 Ready (nächster Sprint) · ⚪ Backlog · ⚫ Aufgegangen in anderer Story

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
| **B — Produktfunktionen** | Echtes Second-Brain-Verhalten: „bestehende Notiz ergänzen", Telegram-Commands, Tags. | 🟢 done |
| **C — Robustheit & Self-Hosting** | Retries, Logging, Mac Mini als 24/7-Host (Cloudflare Tunnel statt ngrok). | 🟢 done |
| **D — Public Release v1.0** | LICENSE, Setup-Doku für Selfhoster, optionaler Ollama-Provider. | 🟢 done |
| **E — Integrations & Ökosystem** | REST-API, Vault-Backends, Multi-LLM-Agenten (optional). n8n-Eigenbau gestrichen (→ ADR 0004). | 🟢 done |
| **F — Knowledge Retrieval & Q&A** | Brain wird befragbar: semantische Suche, RAG-Antworten, Retrieval-API + MCP-Server für Fremdagents. | 🟢 done |
| **G — Produktisierung (kommerziell)** | UI/Dashboard, Packaging/Installer, Lizenzierung. Offen: Verkaufskanal (**E21-2**); native App (**E20-3/5**) kein Nahziel. | 🔵 |
| **H — Capture überall & Mobile** | UI-Capture, Telegram-Uploads, PWA/Companion, UI-Auth, Notiz-Templates, Betriebs-Polish. Epics **E22/E23/E25/E26**. | 🔵 |
| **I — Cloud-Edition (Abo)** | Hosted-Instanzen + Managed LLM für Nicht-Selfhoster. Gated auf **ADR 0007** (Proposed). Epic **E24**. | ⚪ |

> **Hinweis (ADR 0004):** Phase **G** ist bis auf Verkaufskanal (E21-2) und die
> bewusst zurückgestellte native App weitgehend fertig. Formelles **v1.0**-Tag
> und Shop-Mechanik sind die verbleibenden Produktisierungsschritte.
> **Phase H/I** (2026-08-08): Ergebnis der Bestandsaufnahme — Capture-Lücken,
> Mobile-Companion und die strategische Cloud-/Abo-Frage (ADR 0007).

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
| E4-3 | Konfigurierbare Kategorien (`vault_config.yaml`) statt hardcoded `CATEGORY_FOLDERS`. | 3 | 2 | 2 | 3 | 3 | 🟢 | B |
| E4-4 | Prompt-Versionierung (`classify.v1.txt`, `classify.v2.txt`, `PROMPT_VERSION` in DB). | 2 | 1 | 1 | 4 | 2 | 🟢 | C |

---

### E5 — Existing-Notes Lookup · `epic:vault`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E5-1 | Vault-Index in Postgres spiegeln (Titel, Pfad, mtime); statt jedes Mal `rglob`. Voraussetzung für E17-1 (Keyword-Suche). | 3 | 3 | 3 | 4 | 3 | 🟢 | C |
| E5-2 | Heuristisches Pre-Filtering vor LLM (Token-Match, max. 30 Notizen). | 3 | 2 | 1 | 3 | 3 | 🟢 | C |
| E5-3 | (Optional v2) pgvector-Embeddings für semantische Ähnlichkeit. Geliefert zusammen mit E17-2 (Embedding-Provider + `embedding`-Spalte + pgvector). | 4 | 4 | 3 | 5 | 2 | 🟢 | E/F |

---

### E6 — Voice Support · `epic:voice`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E6-1 | Voice-File-Size-Limit + freundliche Fehlermeldung. | 3 | 1 | 1 | 2 | 3 | 🟢 | C |
| E6-2 | Audio temporär persistieren bis Erfolg (Replay bei Crash). | 2 | 2 | 2 | 3 | 2 | 🟢 | C |
| E6-3 | `language`-Hint für Whisper (env-konfigurierbar). | 2 | 1 | 1 | 2 | 2 | 🟢 | C |
| E6-4 | (Optional) Lokaler Whisper via `whisper.cpp` auf Mac Mini → Cost-Ersparnis. | 3 | 3 | 2 | 4 | 2 | 🟢 | D-Bonus |

---

### E7 — LLM Provider Abstraktion · `epic:llm`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E7-1 | Provider-unabhängige JSON-Validierung + Retry bei `JSONDecodeError`. | 3 | 2 | 2 | 4 | 3 | 🟢 | C |
| E7-2 | Ollama-Provider implementieren (gleiches Pydantic-Schema). | 3 | 3 | 3 | 5 | 3 | 🟢 | D-Bonus |
| E7-3 | Spezialisierte LLM-Rollen: Router (create/append), Writer (Summary/Tags), Linker (related) — je Prompt + Pydantic-Schema, max. 2–3 Steps im Core. | 4 | 3 | 2 | 5 | 3 | 🟢 | C/E |
| E7-4 | (Optional) Multi-LLM-Orchestrierung in n8n statt im Python-Core dokumentieren + Beispiel-Workflow. | 3 | 2 | 1 | 4 | 2 | 🟢 | E |

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
| E9-3 | Optionaler Remote-Zugang für VPS-Betrieb (Reverse-Proxy/Tunnel, TLS). Für lokales Consumer-Hosting **nicht** nötig (Long-Polling, E1-5). | 3 | 2 | 2 | 3 | 3 | 🟢 | G |
| E9-4 | Backups: Postgres-Dump + Vault-Snapshot (lokal). | 3 | 2 | 2 | 3 | 3 | 🟢 | C |
| E9-5 | (Eval) Vereinfachter Stack für Consumer-Edition: SQLite statt Postgres, in-process Worker statt Redis/Celery — weniger bewegliche Teile beim Endnutzer. Server-/VPS-Edition behält vollen Stack. Offen: eine vs. zwei Editionen (ADR 0004). → **Ergebnis:** kein Fork, siehe [ADR 0006](docs/adr/0006-consumer-stack-no-sqlite-fork.md). | 4 | 4 | 4 | 5 | 3 | 🟢 | G |

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
| E11-4 | Repo-Topics, Screenshots, GIF im README. | 2 | 1 | 1 | 1 | 2 | 🟢 | D |

---

### E12 — Documentation & Onboarding · `epic:docs`

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E12-1 | `docs/setup.md`: Bot-Token holen, Webhook setzen, Vault mounten. | 4 | 2 | 1 | 2 | 4 | 🟢 | A |
| E12-2 | `ARCHITECTURE.md`: Diagramm + Modul-Map. | 3 | 1 | 1 | 2 | 4 | 🟢 | A |
| E12-3 | Troubleshooting-Sektion (ngrok-Restart, Migration-Fehler etc.). | 3 | 1 | 1 | 2 | 3 | 🟢 | D |
| E12-4 | ADR-Verzeichnis (`docs/adr/`) + Template. | 3 | 1 | 1 | 3 | 4 | 🟢 | A |

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
| E15-1 | `VaultBackend`-Protocol; Filesystem-Implementierung extrahiert aus reader/writer. | 4 | 3 | 2 | 5 | 3 | 🟢 | D |
| E15-2 | Doku: „Obsidian optional“ — jeder Markdown-Ordner reicht (`vault.example/`). | 3 | 1 | 1 | 2 | 3 | 🟢 | D |
| E15-3 | (Optional) Git-backed Vault: Commit pro Note / konfigurierbarer Push. | 3 | 3 | 3 | 4 | 2 | 🟢 | E |
| E15-4 | ~~(Optional) Read-only Web-UI für Vault-Browse~~ → **aufgegangen in Epic E19 (UI/Dashboard)**. | — | — | — | — | — | ➡️ E19 | G |
| E15-5 | Notion-Anbindung evaluieren: einseitiger Export/Sync nach Notion vs. vollwertiges API-Backend (Block-Modell ≠ Markdown; Frontmatter/Wiki-Links mappen nicht 1:1). Ergebnis als ADR/Doku, erst dann ggf. Code. | 3 | 4 | 3 | 3 | 2 | ⚪ | H+ |

Details: [`docs/integrations/vault-backends.md`](./docs/integrations/vault-backends.md)

---

### E16 — Setup & Onboarding CLI · `epic:public-ready`

Easy Setup für Selfhoster. **Keys nur lokal** — nie Remote-Install mit Key-Upload.

> **Reframe (ADR 0004):** Für das Consumer-Produkt verschiebt sich Onboarding von
> CLI/TUI in die **grafische UI** (Setup-Wizard, Epic **E19**). Die CLI-Stufen
> bleiben relevant für die Server-/VPS-Edition und Power-User; `seiton doctor`
> (E16-2) und `seiton init` (E16-3) bleiben als CLI-Pfade; Browser-Setup (E16-4)
> ist im UI-Wizard aufgegangen.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E16-1 | `scripts/init.sh` / `make init`: `.env` aus Example, Vault-Ordner, Docker-Hinweise — ohne Secrets abfragen. | 4 | 1 | 1 | 2 | 4 | 🟢 | D |
| E16-2 | `seiton doctor`: prüft `.env`, DB, Redis, Vault-Pfad, optional OpenAI/Telegram. | 4 | 2 | 1 | 3 | 4 | 🟢 | D |
| E16-3 | `seiton init` TUI: interaktiv `.env` schreiben (lokal, kein Netzwerk-Upload). | 4 | 2 | 1 | 3 | 3 | 🟢 | D/E |
| E16-4 | (Optional) Browser-Setup `localhost:8000/setup` — einmalig, nur localhost. | 2 | 3 | 2 | 3 | 1 | 🟢 | E |
| E16-5 | (Optional) At-Rest-Key-Schutz via OS-Keystore (`keyring` → macOS Keychain / Windows Credential Manager / libsecret). `seiton init` legt Keys im Store ab; Launcher injiziert sie beim `docker compose up` als Env statt Klartext-`.env`. Baut auf E16-3. | 3 | 4 | 3 | 4 | 2 | 🟢 | E |

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
| E18-4 | Chunking großer Dokumente in retrieval-taugliche Abschnitte; Index-Schema von 1 Zeile/Notiz → N Chunks/Dokument (eigene `vault_chunk`-Tabelle). Voraussetzung für sinnvolles semantisches Retrieval (E17-2/3) über lange Dateien. | 4 | 3 | 3 | 4 | 3 | 🟢 | F |
| E18-5 | OCR für gescannte PDFs / Foto-Dokumente (Zeugnisse, Rechnungen) via Tesseract (`pytesseract`) — optionaler Adapter, nur wenn installiert. | 4 | 4 | 3 | 4 | 2 | 🟢 | F-Bonus |
| E18-6 | Vision-LLM für reine Foto-Inhalte: Bildbeschreibung + Tags als durchsuchbare Text-Repräsentation im Index. | 3 | 4 | 3 | 4 | 2 | 🟢 | F-Bonus |

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

### E22 — Capture Everywhere · `epic:capture`

Capture-Lücken schließen (Analyse 2026-08-08): Die UI kann Notizen **verwalten,
aber nicht erfassen**; Telegram nimmt **keine Fotos/Dokumente** an; MCP ist
read-only. ADR 0004 will die UI als Hauptoberfläche — dann muss sie auch der
Haupteingang sein.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E22-1 | UI-Capture: Notiz in der Web-UI erfassen (Text, gleiche Pipeline wie Telegram/REST, inkl. Status-Feedback). | 5 | 2 | 1 | 2 | 5 | 🟢 | H |
| E22-2 | Telegram Foto-/Dokument-Capture: Uploads annehmen → OCR (E18-5) / Vision (E18-6) / Extractors (E18-1..3) in der Inbox-Pipeline. | 4 | 3 | 2 | 3 | 4 | 🟢 | H |
| E22-3 | Digest in der Web-UI (Konsument von E17-8; heute nur REST/Telegram). | 3 | 2 | 1 | 2 | 3 | 🟢 | H |
| E22-4 | MCP-Tools `capture_note` + `digest` (heute nur Retrieval) — Agenten können ins Brain schreiben. | 3 | 2 | 2 | 3 | 3 | 🟢 | H |
| E22-5 | E-Mail-Ingestion: dediziertes IMAP-Postfach pollen → capture (Newsletter, Mail-an-mich-selbst). | 3 | 3 | 2 | 3 | 2 | ⚪ | H |
| E22-6 | `/ask`-Antwort als Notiz speichern (Q&A→Note, offene Designfrage aus `docs/integrations/knowledge-retrieval.md`). | 3 | 2 | 1 | 2 | 2 | ⚪ | H |

---

### E23 — Mobile Companion (PWA-first) · `epic:mobile`

„Passende App" ohne native-App-Kosten: die bestehende Web-UI **installierbar**
machen (PWA). Nativer Wrapper nur bei echtem Bedarf (ersetzt die
E20-3-Diskussion). Voraussetzung für alles Mobile: **UI-Auth**, da localhost-only
nicht reicht, sobald das Handy zugreift.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E23-1 | UI-Auth: Login/Session (Passwort oder Token) statt nur localhost-Guard — Voraussetzung für Remote-/Mobile-Zugriff und Cloud-Edition. | 5 | 3 | 3 | 3 | 5 | 🟢 | H |
| E23-2 | PWA: Manifest + Service Worker + Icons — UI auf Handy/Desktop „installierbar" (Homescreen). | 4 | 3 | 2 | 3 | 4 | 🟢 | H |
| E23-3 | Offline-Capture-Queue: Notiz ohne Verbindung erfassen, Sync bei Reconnect (Service Worker + Background Sync). | 3 | 4 | 3 | 4 | 2 | ⚪ | H+ |
| E23-4 | Teilen ins Brain: Android `share_target` (PWA) + iOS-Shortcuts-Beispiel gegen `POST /v1/capture`. | 4 | 2 | 1 | 2 | 3 | ⚪ | H |
| E23-5 | (Später) Nativer Wrapper (z. B. Capacitor) nur bei echtem Bedarf — löst E20-3/5 ab. | 2 | 4 | 3 | 3 | 1 | ⚪ | H+ |

---

### E24 — Cloud-Edition & Abo · `epic:cloud` · ⚠️ gated auf ADR 0007

Für Kunden, die **nicht selbst hosten** und **keinen eigenen LLM-Key** wollen:
gehostete Instanz + Managed LLM im **Abo** — bewusster Bruch mit Teilen von
ADR 0004, daher zuerst Entscheidung ([ADR 0007](./docs/adr/0007-cloud-edition-subscription.md), Proposed).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E24-1 | ADR 0007 entscheiden: Single-Tenant-Instanzen vs. Multi-Tenant vs. Partner-Hosting; Abo-Preislogik; DSGVO-Rahmen. | 5 | 2 | 2 | 4 | 4 | ⚪ | I |
| E24-2 | Managed-LLM-Proxy: eigener Key serverseitig, per-Kunde-Quota (Tokens/Monat), Kostendeckel, Modell-Whitelist. | 4 | 4 | 4 | 4 | 3 | ⚪ | I |
| E24-3 | Provisioning-Blaupause: Instanz pro Kunde automatisiert aufsetzen/updaten (EU-Hoster), Monitoring + Backups. | 4 | 4 | 4 | 4 | 3 | ⚪ | I |
| E24-4 | Abo-Billing (z. B. Stripe) + Entitlements — koexistiert mit Buy-once-Lizenz (E21-1); Verknüpfung mit E21-2. | 4 | 3 | 3 | 3 | 3 | ⚪ | I |
| E24-5 | DSGVO-Paket: AVV-Vorlage, Datenexport, Löschkonzept, EU-Region-Garantie. | 4 | 3 | 3 | 3 | 3 | ⚪ | I |

---

### E25 — Betrieb & Polish · `epic:ops-polish`

Kleine, klar umrissene Verbesserungen aus der Bestandsaufnahme 2026-08-08.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E25-1 | Backup/Restore in der Settings-UI: One-Click-Backup + geführter Restore (heute nur `scripts/backup.sh` + Doku). | 4 | 2 | 2 | 2 | 4 | 🟢 | H |
| E25-2 | `seiton doctor` als CLI-Subcommand (Parität zu `scripts/doctor.sh`, E16-2-Wortlaut). | 2 | 2 | 1 | 2 | 2 | ⚪ | H |
| E25-3 | Rate-Limits für `/ask` und `/digest` (Kostenkontrolle, offene Designfrage aus `knowledge-retrieval.md`). → **aufgegangen in E27-6** (ein Rate-Limit-Konzept für Login + `/v1` + LLM-Endpunkte). | 3 | 2 | 1 | 2 | 3 | ⚫ | H |
| E25-4 | Dashboard-Panel „System-Gesundheit": Health, Queue-Länge, letzte Fehler (nutzt `/health` + Logs). | 3 | 3 | 2 | 3 | 2 | ⚪ | H+ |

---

### E26 — Notiz-Templates · `epic:templates`

Nutzer bestimmen selbst, **wie** die KI Notizen ablegt (Idee 2026-08-08). Heute
ist das Format hartcodiert (`filesystem.py`: Frontmatter + Titel + Summary +
Related). Zwei Schichten: **Render-Template** (deterministische Markdown-Vorlage
mit Platzhaltern, kein LLM) und **KI-Felder** (nutzerdefinierte Felder wie
„Action Items", die der Writer-LLM aus dem Input füllt). Für
Nicht-Markdown-Nutzer ein **visueller Builder** in der UI — nur eine zweite
Ansicht auf dasselbe Template-Artefakt.

**Leitplanken:** Frontmatter-Pflichtteil bleibt fix (Append-Logik E3-3/E4-1 und
Index dürfen nicht brechen); Templates liegen als Dateien im Vault (in Obsidian
sichtbar, portabel), nicht in der DB; kaputte Templates → Default + Warnung.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E26-1 | Render-Template: Markdown-Vorlage mit Platzhaltern (`{{title}}`, `{{summary}}`, `{{tags}}`, `{{date}}`, `{{related}}`) ersetzt hartcodiertes Body-Format; Default = heutiges Layout; Datei im Vault (z. B. `_seiton/templates/note.md`). | 4 | 3 | 3 | 3 | 4 | 🟢 | H |
| E26-2 | Validierung + Fallback: unbekannte Platzhalter/kaputtes Template → Default-Layout + Log/UI-Warnung; Append-/Frontmatter-Kompatibilität abgesichert (Tests). | 4 | 2 | 2 | 2 | 4 | 🟢 | H |
| E26-3 | KI-Felder: eigene Felder im Template (z. B. `{{ai:action_items}}`, `{{ai:kernaussagen}}`) → Writer-Prompt bekommt dynamisches Feld-Schema, LLM füllt sie aus dem Input. | 4 | 4 | 3 | 4 | 3 | ⚪ | H |
| E26-4 | Template-Editor in der Settings-UI: Markdown-Editor + Live-Vorschau mit Beispieldaten. | 3 | 2 | 1 | 2 | 3 | ⚪ | H |
| E26-5 | Visueller Builder: Bausteine (Titel, Zusammenfassung, Tags, KI-Feld, …) benennen/sortieren per Drag-and-drop → erzeugt intern das Markdown-Template. | 4 | 4 | 2 | 3 | 2 | ⚪ | H+ |
| E26-6 | Template pro Kategorie (Aufgabe ≠ Idee ≠ Journal), mit globalem Default. | 3 | 2 | 2 | 2 | 2 | ⚪ | H+ |

Sinnvolle Reihenfolge: E26-1 → E26-2 → E26-4 → E26-3 → E26-6 → E26-5.

---

## Phase L — Launch-Härtung (Audit 2026-08)

Ergebnis des **Product Readiness Audits**
([`docs/audit-2026-08-product-readiness.md`](./docs/audit-2026-08-product-readiness.md)):
Gesamturteil **GO WITH CONDITIONS**. Die Epics E27–E31 sind die Bedingungen —
sie kommen **vor** Monetarisierung/Cloud (E21-2, E24). Alle Findings sind im
Ist-Code verifiziert (Datei-Referenzen im Audit-Bericht).

### E27 — Security-Härtung · `epic:security` · **P0/P1**

Betroffene Komponenten: `app/setup/security.py`, `app/ui/`, `deploy/`,
`docker-compose*.yml`. Risiko bei Nichtumsetzung: Secrets-/Datenzugriff durch
Dritte auf dem dokumentierten VPS-Deployment-Pfad.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E27-1 | **P0 — Proxy-sichere Zugriffskontrolle:** `require_localhost` prüft nur `request.client.host` — hinter dem dokumentierten Caddy/nginx-Proxy immer die Proxy-IP → `/setup`, UI ohne Passwort und `/docs` sind remote erreichbar. Umgesetzt fail-closed **ohne** neues Setting: Forwarded-Header (`X-Forwarded-For`/`X-Real-IP`/`Forwarded`) werden ausgewertet — alle gemeldeten Hops müssen localhost sein; Deploy-Beispiele blocken `/setup` + `/docs` zusätzlich im Proxy. AK erfüllt: Setup remote 403; Tests mit simulierten Proxy-Headern. | 5 | 2 | 3 | 2 | 5 | 🟢 | L |
| E27-2 | **XSS-Fix:** `dashboard.js` rendert `title`/`folder`/`vault_path`/`err.message` ungeescaped in `innerHTML` (Stored XSS über Notiz-Titel, z. B. aus OCR/Dokument-Inhalten); `login.js`/`setup.js` latent. Zentrale `escapeHtml`-Nutzung überall; Regression-Test der die JS-Dateien auf rohe Interpolationen prüft. | 5 | 1 | 2 | 1 | 5 | 🟢 | L |
| E27-3 | **Sichere Remote-Defaults:** Session-Cookie `Secure`-Flag (config-gesteuert bei TLS), Standard-Compose bindet `127.0.0.1:8000` statt `0.0.0.0`, Setup-Wizard macht Telegram-Allowlist zum empfohlenen Pflichtschritt (Warnung wenn leer + Webhook aktiv), Logout per POST. | 4 | 2 | 2 | 2 | 4 | 🟢 | L |
| E27-4 | **Frontmatter-/Pfad-Härtung:** Titel/Tags werden roh ins YAML-Frontmatter geschrieben (Newline/`---` zerstören die Notiz) → sanitizen; `resolve_vault_file` nutzt `startswith` ohne Separator → `is_relative_to`; Append-Pfad läuft an `resolve_vault_file` vorbei → vereinheitlichen. | 4 | 2 | 2 | 1 | 4 | 🟢 | L |
| E27-5 | **Rate-Limits & Brute-Force** (ersetzt E25-3): Limits für `/api/ui/login`, `/v1/*` und LLM-Endpunkte (`/ask`, `/digest`, Capture) — Kostenkontrolle + Key-Brute-Force; Lockout-Store proxy-/multi-worker-tauglich (Redis). Webhook-Secret timing-safe vergleichen. | 4 | 3 | 2 | 2 | 4 | ⚪ | L |

Abhängigkeiten: keine untereinander; E27-1 zuerst (größtes Risiko).

### E28 — Datenintegrität & Index-Konsistenz · `epic:data-integrity` · **P1**

Betroffene Komponenten: `app/services/process_message.py`,
`app/vault/filesystem.py`, `app/vault/index.py`, `app/worker/tasks.py`.
Risiko: Datenverlust/Doppelnotizen unter Parallelität; stale Suche/RAG nach
externen Obsidian-Edits — bricht das Kernversprechen Vault-Koexistenz.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E28-1 | **Inkrementeller Index-Sync:** externe Vault-Edits landen heute nie im Index (Full-Sync nur bei leerem Index). mtime-basierter inkrementeller Sync (periodischer Worker-Task; etabliert damit die **Celery-Beat-/Scheduler-Grundlage**, die Phase M für E34-2/E22-5 wiederverwendet) + „Neu indexieren"-Button in Settings. AK: Obsidian-Edit ist nach ≤ Sync-Intervall in Suche/RAG sichtbar. | 5 | 3 | 3 | 3 | 5 | 🟢 | L |
| E28-2 | **File-Locks für Create/Append:** `_next_available_path` und Read-Modify-Write-Append ohne Lock → Lost Updates bei parallelen Captures. Prozessübergreifendes Locking (z. B. `flock` pro Zieldatei) + Test. | 4 | 2 | 3 | 2 | 4 | 🟢 | L |
| E28-3 | **Capture-Kompensation:** Vault-Write vor DB-Commit ohne Rollback → Orphan-Dateien; bei Telegram-Retry im Verarbeitungsfenster Doppel-Writes. Kompensationslogik (Datei löschen bei DB-Fehler auf Create-Pfad) + Idempotenz-Fenster schließen. | 4 | 3 | 3 | 2 | 4 | 🟢 | L |
| E28-4 | **Idempotency-Key für REST/UI-Capture:** optionaler `Idempotency-Key`-Header (REST) bzw. Client-Token (UI) gegen Mehrfachklick/Netz-Retry-Doppelnotizen. | 3 | 2 | 2 | 2 | 3 | ⚪ | L |
| E28-5 | **Fehler-Semantik reparieren:** `APIError` zu breit in `RETRYABLE_EXCEPTIONS` (retryt 4xx/Auth sinnlos) → nur transiente Fehler; `entries.status="failed"` bei permanenten Fehlern tatsächlich setzen (Dashboard zeigt Status heute nie). | 3 | 2 | 2 | 1 | 4 | 🟢 | L |

Reihenfolge: E28-5 (klein) → E28-2 → E28-3 → E28-1 → E28-4. E28-1 vor E30-2
(klickbare Treffer nützen wenig, wenn der Index stale ist).

### E29 — Release- & Ops-Readiness · `epic:release-ops` · **P1**

Risiko: nicht reproduzierbare Builds, Schema-Drift bei Kunden-Updates,
Support-Unfähigkeit ohne Release-Stände.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E29-1 | **Dependencies pinnen** (`requirements.txt` komplett ungepinnt) + Dependabot/`pip-audit` in CI; Python-Version im Dockerfile bewusst festlegen (3.14-slim prüfen). | 4 | 1 | 2 | 1 | 5 | 🟢 | L |
| E29-2 | **CI-Härtung:** Docker-Build-Job + Alembic-`upgrade head` gegen echte `pgvector/pgvector:pg16`-Postgres (Service-Container) + Smoke-Insert mit Vector. | 4 | 2 | 2 | 2 | 4 | 🟢 | L |
| E29-3 | **Release v0.3.0:** CHANGELOG-„Unreleased"-Berg schneiden, Git-Tag, GitHub-Release, leichter Release-Prozess dokumentieren (kein Release seit 0.2.0 trotz ~20 Features). | 4 | 1 | 1 | 1 | 4 | 🟢 | L |
| E29-4 | **Backup-Retention + Restore-Verifikation:** Backups wachsen unbegrenzt → Rotation (konfigurierbar, z. B. letzte N behalten); Restore einmal automatisiert als Roundtrip testen (CI oder Skript); Update-Skript bricht bei fehlgeschlagenem Backup ab statt weiterzulaufen. | 4 | 2 | 2 | 2 | 4 | ⚪ | L |
| E29-5 | **Doku-Sync:** README (Stand „Phase C–F, 360 Tests") und ARCHITECTURE.md (Modul-Map ohne `ui/`, falsches DB-Image, veraltete Write-Reihenfolge, `kind` ohne document/photo) auf Ist-Stand; `KIND_VALUES`/`STATUS_VALUES` im Code an Realität anpassen. | 3 | 2 | 1 | 1 | 4 | ⚪ | L |
| E29-6 | **Betriebs-Robustheit:** Log-Rotation im Compose (`max-size`), Restart-Policies auch im Standard-Compose dokumentiert abgrenzen, `/health` optional um Worker-Erreichbarkeit + Vault-Schreibbarkeit erweitern (Basis für E25-4). | 3 | 2 | 2 | 2 | 3 | ⚪ | L |

### E30 — UX Consumer-Pass · `epic:ux-polish` · **P1/P2**

Vom „fähigen Admin-Tool" zum kaufbaren Produkt (UI-Audit: die Kern-Journey
„wiederfinden → lesen" ist heute unterbrochen).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E30-1 | **Retrieval-Loop schließen:** Suchtreffer + Ask-/Digest-Quellen klickbar → öffnen die Notiz (`/notes?path=…`-Deep-Link). | 5 | 1 | 1 | 1 | 5 | 🟢 | L |
| E30-2 | **Notiz-Lesemodus:** Markdown-Preview (gerendert, XSS-sicher) mit Edit-Toggle; klickbare `[[Wikilinks]]`; Speichern-Feedback statt stillem Erfolg. | 5 | 3 | 2 | 3 | 4 | ⚪ | L |
| E30-3 | **Post-Setup-Onboarding:** Abschluss-Screen mit Neustart-Checkliste + CTA „Erste Notiz erfassen"; „Setup" verschwindet aus der Hauptnav, wenn abgeschlossen; Formular-Labels statt Env-Namen (`OBSIDIAN_VAULT_HOST_PATH` → „Vault-Ordner"). | 5 | 2 | 1 | 2 | 4 | 🟢 | L |
| E30-4 | **Feedback-Layer:** Toasts/Modals statt `alert()`/`confirm()`; alle nutzerseitigen Fehlertexte deutsch (heute z. T. rohe EN-API-Details wie „Duplicate capture rejected"); Undo-Snackbar bzw. Papierkorb beim Löschen. | 4 | 3 | 1 | 2 | 4 | ⚪ | L |
| E30-5 | **Terminologie- & Status-Pass:** eine Nutzersprache (keine „Entries", Status-Rohwerte `appended`/`failed`, „E26"-Codes oder Container-Pfade in Primär-UI); Empty-States mit CTA. | 3 | 2 | 1 | 1 | 3 | ⚪ | L |
| E30-6 | **Mobile-Politur:** Topnav umbrechen/Hamburger, Touch-Targets ≥ 44 px, Fokus-Styles auf Buttons, `aria-current`, `<main>`-Landmark (A11y-AA-Basis). | 3 | 2 | 1 | 2 | 3 | ⚪ | L |
| E30-7 | **Ask-Verlauf persistieren:** Chat-History überlebt Reload (DB oder LocalStorage) — bei Wettbewerbern Standard. | 3 | 2 | 1 | 2 | 3 | ⚪ | L+ |
| E30-8 | **Integrations-Karte in Settings:** API-Key/MCP/Webhooks/n8n verständlich erklärt und verlinkt (Discoverability der Power-Features). | 2 | 1 | 1 | 1 | 3 | ⚪ | L+ |

Reihenfolge: E30-1 → E30-3 → E30-4 → E30-2 → E30-5 → E30-6 → E30-7 → E30-8.

### E31 — Privacy/DSGVO-Basis · `epic:privacy` · **P1 (vor Verkauf in DE/EU)**

Technischer Produktbedarf (juristische Prüfung von AGB/Datenschutzerklärung
ist separat und **nicht** Teil dieser Stories).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E31-1 | **Voll-Löschung:** ein geführter Weg („Alle Daten löschen" in Settings + CLI), der DB (Entries, Index, Chunks, Embeddings), Voice-Cache und optional Vault + Backups löscht. Art.-17-Basis. | 4 | 2 | 2 | 2 | 4 | ⚪ | L |
| E31-2 | **Strukturierter Export:** Vault ist schon portabel; zusätzlich Entries/Metadaten/Einstellungen als JSON/ZIP-Export (Art.-20-Basis, auch Umzugs-Feature). | 3 | 2 | 1 | 2 | 3 | ⚪ | L |
| E31-3 | **Log- & Retention-Hygiene:** kein Notiz-/Transkript-Text in Logs (heute 80-Zeichen-Transkript-Snippet), Voice-Cache-TTL/Cleanup, `raw_input_preview` im Outbound-Webhook opt-in. | 3 | 1 | 1 | 1 | 4 | ⚪ | L |
| E31-4 | **Datenfluss-Doku `docs/privacy.md`:** welche Daten gehen an OpenAI/Telegram, lokale Alternativen (Ollama, whisper.cpp) als Privacy-Modus dokumentiert — Grundlage für spätere Datenschutzerklärung und DE-Verkaufsargument. | 3 | 1 | 1 | 1 | 3 | ⚪ | L |

### Bewusst NICHT aufgenommen (Challenge-Ergebnis, siehe Audit-Bericht)

- **Multi-User/Rollen** — ADR 0004: Single-User; Cloud-Edition = eigene Instanzen.
- **ANN-Index (HNSW)** — erst bei großen Vaults/Cloud relevant, exakter kNN reicht.
- **i18n-Umsetzung** — erst bei EN-Markteintritt; E30-4 (zentrale Fehlertexte) bereitet vor.
- **Daily Notes, Feature-Flags, Prometheus-Stack, breite E2E-Browser-Tests** — Aufwand/Nutzen für Self-Hosted-Single-User nicht gerechtfertigt.

---

## Phase M — Ecosystem & Interoperability (Integrations-Audit 2026-08)

Ergebnis des **Integrations-/Ökosystem-Audits**
([`docs/audit-2026-08-integrations.md`](./docs/audit-2026-08-integrations.md)),
alle 5 Initiativen vom Product Owner bestätigt (2026-08-18). Leitidee: nicht
fremde Plattformen einzeln integrieren, sondern die **eigene Offenheit
vervollständigen** — Vault als offene Wissensschicht, Capture von überall,
Events/API für Automation, MCP für AI. Phase M startet **nach** dem
Phase-L-Kern; E28-1 (Index-Sync inkl. periodischem Worker-Task) ist die
technische Vorstufe mehrerer M-Stories.

**Bewusst NICHT gebaut (Tier 4, siehe Audit):** Task-Tool-Integrationen
(→ n8n-Rezepte E35-3), Google/Microsoft-Office-Embeds & Two-Way-Sync,
Cloud-Storage-OAuth-APIs (Ordnersync/rclone genügt), Zapier-App (erst mit
Cloud-Edition E24 neu bewerten), Plugin-System, OAuth-Framework auf Vorrat.

### E32 — Vault-Interop & Migration · `epic:vault-interop` (Initiative 1)

„Bring your Second Brain": bestehende Obsidian-Vaults sind der native
Import; das Obsidian-Ökosystem (Readwise-Plugin, Web Clipper, Ordnersync)
wird via Index-Sync automatisch zum Seiton-Integrationskatalog.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E32-1 | **Vault-Onboarding im Setup:** „Bestehenden Vault verbinden" als eigener Schritt — erkennt vorhandene Notizen, zeigt Statistik (Anzahl, Ordner), startet Erstindexierung mit Fortschrittsanzeige und erklärt Koexistenz (Obsidian parallel nutzen). AK: bestehender 1k-Notizen-Vault ist nach Setup durchsuchbar, Nutzer sieht Fortschritt/Ergebnis. Abhängig von E28-1. | 5 | 3 | 2 | 3 | 4 | ⚪ | M |
| E32-2 | **Koexistenz-Rezepte (Doku):** `docs/integrations/obsidian-ecosystem.md` — Readwise-Plugin, Obsidian Web Clipper, iCloud/Syncthing-Ordnersync als „Integrationen ohne Code"; Frontmatter-/`_seiton`-Konventionen für Fremd-Tools. | 3 | 1 | 1 | 1 | 3 | ⚪ | M |
| E32-3 | **Markdown-ZIP-Import:** Upload eines ZIP (z. B. Notion-Export) in der UI → Dateien in Vault-Unterordner entpacken (Pfad-sicher), indexieren, Import-Report (übernommen/übersprungen). Deckt Notion-/Generic-Markdown-Migration ab; ENEX/OneNote bewusst Tier 3. | 4 | 3 | 2 | 3 | 3 | ⚪ | M |

### E33 — Universal Capture · `epic:universal-capture` (Initiative 3)

„Everything can be sent into my Second Brain." Ergänzt die bestehenden
Stories **E22-5** (E-Mail via IMAP) und **E23-4** (Share-Target/Shortcut) —
beide werden mit Phase M priorisiert und bleiben unter ihren Epics geführt.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E33-1 | **Provenance im Capture-Pfad:** `source` (telegram/ui/rest/email/web/mcp) + optionales `source_url` **+ `actor`** (Telegram-User-ID/API-Key-ID/Session — Team-Audit 2026-08: Attribution-Vorstufe für E41-2) durch `process_text_message` bis ins Frontmatter (`source:`) und `entries`; Filter in Notes-API. Grundlage für E33-2/E22-5 und Vertrauen („Woher kam das?"). Jetzt billig, nachträglich teuer. | 4 | 2 | 2 | 2 | 4 | ⚪ | M |
| E33-2 | **URL/Web-Capture:** erkannte URL (Telegram/UI/REST) → Artikel-Fetch + Text-Extraktion (Readability-Ansatz, permissive Lizenz prüfen) → Notiz mit Quelle, Titel, Auszug; Fallback bei Paywall/Fehler = heutiges Verhalten. AK: geteilter Artikel-Link wird zur durchsuchbaren Wissensnotiz mit `source_url`. | 5 | 3 | 2 | 3 | 4 | ⚪ | M |
| E33-3 | **Capture-Rezepte (Doku):** Bookmarklet gegen `POST /v1/capture`, iOS-Shortcut-Beispiel (bis E23-4), E-Mail-Weiterleitungs-Setup (mit E22-5). | 2 | 1 | 1 | 1 | 3 | ⚪ | M |

### E34 — Git-Backup & Data Ownership · `epic:git-backup` (Initiative 2)

`GitVaultBackend` (E15-3) kann bereits Commit-pro-Änderung + Push —
produktisieren: geführtes Setup, externe Edits, Sichtbarkeit. Zusammen mit
Backup-Rotation (E29-4) und Export (E31-2) wird „**Deine Daten, versioniert,
für immer**" zum Marketing-Argument.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E34-1 | **Geführtes Git-Backup-Setup:** Settings-Karte — Repo-Status erkennen, `git init` anbieten, Remote/Deploy-Key-Anleitung (GitHub/GitLab/lokal), Test-Push, Statusanzeige (letzter Commit/Push, Fehler). | 4 | 3 | 2 | 2 | 4 | ⚪ | M |
| E34-2 | **Auto-Commit externer Edits:** periodischer Task (nutzt Scheduler aus E28-1) committet Obsidian-/Fremd-Änderungen im Vault (`git add -A` + Batch-Commit, konfigurierbares Intervall) + optional Push. Heute werden nur Seiton-eigene Writes committet. | 4 | 2 | 2 | 2 | 4 | ⚪ | M |
| E34-3 | **Offsite-Rezept:** `docs/backup-offsite.md` + optionaler Hook im Backup-Flow — rclone/S3/beliebiges Sync-Ziel für `backups/` und Vault; bewusst ohne eigene Cloud-OAuth-Integrationen. | 3 | 1 | 1 | 1 | 3 | ⚪ | M |

### E35 — Automation-Fundament · `epic:automation` (Initiative 4)

Ein sauberes Fundament statt Dutzender Einzelintegrationen (ADR 0004:
REST + n8n statt Custom-Nodes). Deckt Task-Tools, Benachrichtigungen und
Long-Tail-Wünsche ab.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E35-1 | **REST-CRUD vervollständigen:** `PUT /v1/notes/content`, `DELETE /v1/notes`, `PATCH`-Semantik für Tags/Kategorie; konsistente Fehler; OpenAPI-Beispiele. Heute ist die API read+capture-only. | 4 | 2 | 2 | 2 | 4 | ⚪ | M |
| E35-2 | **Webhooks härten:** HMAC-Signatur (`X-Seiton-Signature`), Payload-`version`, Retry mit Backoff, neue Events `note.updated`/`note.deleted`; Empfänger-Doku. | 4 | 2 | 2 | 2 | 4 | ⚪ | M |
| E35-3 | **n8n-Rezepte:** 3–4 Beispiel-Workflows in `examples/n8n/` — Aufgabe→Todoist/Linear (via `note.created` + category), Wochen-Digest→Slack/E-Mail, Webhook→Sheets-Log. | 3 | 2 | 1 | 2 | 3 | ⚪ | M |

### E36 — Kontrollierter AI-Access · `epic:ai-access` (Initiative 5)

MCP haben wir vor dem Mainstream — die Vertrauensschicht (Scope, Revocation,
Audit) macht daraus ein bewerbbares Differenzierungsmerkmal.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E36-1 | **Scoped API-Keys:** mehrere Keys (DB-Tabelle statt Env-String), Scope `read` / `read-write`, Anlegen/Widerrufen in Settings; `SEITON_API_KEY` bleibt als Legacy-Fallback. AK: AI-Client mit Read-only-Key kann suchen/lesen, aber nicht capturen/ändern. | 4 | 3 | 2 | 3 | 4 | ⚪ | M |
| E36-2 | **Zugriffs-Log (opt-in):** pro API-Key letzte Zugriffe (Endpoint, Zeit) in Settings sichtbar — „welches Tool hat wann was gelesen"; keine Inhalte loggen (E31-3-konform). | 3 | 2 | 1 | 2 | 3 | ⚪ | M |
| E36-3 | **AI-Integrations-Doku + Settings-Karte:** Claude Desktop/ChatGPT/Cursor-Setup Schritt für Schritt, Read-only-Empfehlung; Synergie mit E30-8 (Integrations-Karte). | 3 | 1 | 1 | 1 | 3 | ⚪ | M |

Sinnvolle Reihenfolge Phase M: E33-1 (Provenance, klein & fundamental) →
E32-1/E32-2 → E34-1/E34-2 → E33-2 → E35-1/E35-2 → E36-1 → Rest.
E22-5 + E23-4 parallel einplanen, sobald E33-1 gemerged ist.

---

## Phase N — Privacy-First Knowledge AI (Knowledge-AI-Audit 2026-08)

Ergebnis des **Private-Knowledge-AI-/RAG-Audits**
([`docs/audit-2026-08-private-knowledge-ai.md`](./docs/audit-2026-08-private-knowledge-ai.md)),
Strategie **D — Privacy-First Knowledge AI** vom Product Owner bestätigt
(2026-08-18). Nordstern: *„Chat with your own knowledge"* — ohne Kontrollverlust
über die eigenen Daten. Erreicht als Rampe **B → C → D**: erst Retrieval-
Qualität (E37), dann Permission-Layer (E38) + Local AI (E39), dann Knowledge
Chat (E40). Produktprinzip (Architektur-Invariante):
`User data → Permission/Trust Boundary → Retrieval → Context Selection → Model`
— der Filter sitzt **vor** dem Retrieval; der Answer-Pfad bleibt **read-only**.

Phase N startet nach dem Phase-M-Kern; **E37-2 gehört technisch zu E28-1**
(Index-Sync) und kann mit Phase L/M vorgezogen werden. Synergien: E33-1
(Provenance), E36 (Scoped Keys/Zugriffs-Log = API-Seite desselben
Vertrauensversprechens).

**Bewusst NICHT gebaut (siehe Audit, Abschnitt 17):** Agent mit
Schreibrechten (Strategie E — eigene spätere Entscheidung mit
Confirmation/Audit/Undo), Cross-Encoder-Reranking als Default (erst nach
gemessenem Bedarf via E37-3), Query-Rewriting/Multi-Query/HyDE/Knowledge
Graph, neue Kanäle (WhatsApp/Discord/Voice), persistente Chat-Historie,
Anthropic-/Gemini-native SDKs (OpenAI-kompatible Ebene reicht), automatische
Sensibilitäts-Klassifikation als Barriere, eigenes Modell-Management.

### E37 — Retrieval-Fundament · `epic:retrieval` (Stufe B)

„Excellent retrieval first, chatbot second." Größter Qualitätshebel, kein
neues Privacy-Risiko; nützt `/ask`, `/find`, REST, MCP und UI gleichzeitig.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E37-1 | **Hybrid Search (RRF):** Postgres-Volltext (`tsvector`, Konfig `german`+`english`) parallel zu pgvector-kNN, Fusion via Reciprocal Rank Fusion in `retrieve_vault_notes` (ein Durchsetzungspunkt bleibt). Ersetzt den heutigen Entweder-oder-Fallback. AK: Mehrwort-Fragen und exakte Begriffe (Namen, Codes) treffen; alle Konsumenten profitieren ohne API-Änderung. | 5 | 3 | 2 | 4 | 5 | ⚪ | N |
| E37-2 | **Index-Hygiene — Content-Hash + Embedding-Metadaten:** Hash pro Chunk (nur Geändertes re-embedden) + Modell/Dimension/Version am Index; Re-Index-Routine bei Modellwechsel. Löst die implizite 1536-Dim-Verdrahtung — Voraussetzung für E39-1. Teil von/Synergie mit E28-1. | 4 | 2 | 2 | 3 | 5 | ⚪ | N |
| E37-3 | **Retrieval-Eval-Harness:** 30–50 deutsche Gold-Fragen gegen Fixture-Vault, Hit-Rate@5 als CI-Metrik — **ohne** LLM-Call lauffähig (keine API-Kosten in CI). Entscheidungsgrundlage für „Reranker ja/nein" und jede künftige Retrieval-Änderung. | 4 | 2 | 1 | 4 | 4 | ⚪ | N |
| E37-4 | **Similar Notes ohne LLM:** „Ähnliche Notizen" auf der Notiz-Seite (kNN auf vorhandene Vektoren) + Capture-Hinweis „Dazu hast du schon geschrieben" (kNN vor dem Schreiben, Schwellwert). 0 Kosten, 0 Halluzination, wirkt täglich. | 4 | 2 | 1 | 3 | 3 | ⚪ | N |

### E38 — Permission-Layer `ai_access` · `epic:ai-permissions` (Stufe D-Kern)

Das Differenzierungsmerkmal (Marktlücke, Audit Abschnitt 11): granulare
Per-Ordner-Kontrolle, welche Inhalte welche AI-Klasse sehen darf —
**fail-closed, vor dem Retrieval durchgesetzt.**

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E38-1 | **Konvention + Datenmodell:** `ai_access: none \| local \| trusted \| external` — Ordner-Regeln in `vault_config.yaml`, Frontmatter-Override pro Notiz, denormalisiert als Spalte auf `vault_note_index` (beim Indexieren aufgelöst); Konvention dokumentiert (auch für Fremd-Tools/Obsidian-Nutzer). Default `external` = Status quo, beim Onboarding erklärt. | 5 | 2 | 2 | 3 | 5 | ⚪ | N |
| E38-2 | **Durchsetzung vor Retrieval:** WHERE-Filter in `retrieve_vault_notes` (`trust(provider) ≤ ai_access`); bei `none` wird **nicht embedded**, Stufen-Downgrade löscht vorhandene Vektoren; unbekannte Stufe = `none` (fail-closed). AK: CI-Invarianten-Test „externe AI erhält nie einen `local`-Chunk" (Muster E27-1-Tests). | 5 | 3 | 3 | 4 | 5 | ⚪ | N |
| E38-3 | **Provider- & Kanal-Trust-Klassen:** jeder LLM-/Embedding-Provider deklariert `local`/`trusted`/`external` (konfiguriert, nicht erraten); **kein Auto-Fallback über Trust-Grenzen** (Ollama-Ausfall wechselt nie still zu OpenAI). Kanäle als zweite Dimension: Telegram = `external`-Kanal ⇒ `/ask` via Telegram sieht nur `external`-freigegebene Inhalte. | 4 | 2 | 2 | 3 | 4 | ⚪ | N |
| E38-4 | **Settings-UI:** Ordner-Liste mit `ai_access`-Wahl (+ Vererbung sichtbar), Hinweis-Texte („Finanzen → nie an externe AI"); Änderungen stoßen Re-Index/Vektor-Aufräumen an. | 4 | 2 | 1 | 2 | 4 | ⚪ | N |

### E39 — Local AI komplett · `epic:local-ai`

Chat lokal ✅ (E7-2), Whisper lokal ✅ (E6-4) — es fehlen nur die Embeddings.
Danach ist „No data leaves the user's environment" ein ehrlicher Modus.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E39-1 | **Lokale Embeddings (Ollama):** `OllamaEmbeddingProvider` (Empfehlung `bge-m3`: MIT, 1024 dim, stark auf Deutsch), Dimension aus Embedding-Metadaten (E37-2); geführter Modellwechsel mit Re-Index + Fortschrittsanzeige. AK: Vault komplett ohne externe API durchsuchbar (semantisch). Abhängig von E37-2. | 5 | 3 | 2 | 4 | 4 | ⚪ | N |
| E39-2 | **Generischer OpenAI-kompatibler Provider:** `LLM_PROVIDER=openai_compatible` mit freier `base_url` + Key — deckt LM Studio, vLLM, Mistral API, Azure OpenAI und EU-Gateways ohne je ein natives SDK ab; Trust-Klasse konfigurierbar (E38-3). | 3 | 1 | 1 | 2 | 3 | ⚪ | N |
| E39-3 | **Local-Modus-Doku + Doctor-Check:** `docs/local-ai.md` — geführter Power-User-Pfad (Ollama installieren, Modellempfehlung nach Hardware, Grenzen ehrlich benennen); `doctor.sh` prüft Ollama-Erreichbarkeit + Modelle. | 3 | 1 | 1 | 1 | 3 | ⚪ | N |

### E40 — Knowledge Chat · `epic:knowledge-chat` (Stufe C)

`/ask` wird vom One-Shot zur Konversation — mit Quellen, Scope und voller
Transparenz, **read-only by design**.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E40-1 | **Chat-Seite mit Verlauf:** Session-Verlauf (bewusst nicht persistiert), Folgefragen mit Kontext; Retrieval-Kontext = voller Treffer-Chunk (+ Nachbar-Chunks via `chunk_index`) statt 400-Zeichen-Snippet. Quellen als klickbare Notiz-Links (nutzt E30-1). | 5 | 3 | 2 | 3 | 4 | ⚪ | N |
| E40-2 | **Per-Conversation-Scope:** Selector „ganzer Vault / Ordner / Kategorie" vor bzw. im Chat — wirkt als zusätzlicher Retrieval-Filter (schneidet mit `ai_access`, ersetzt ihn nie). Erhöht Präzision, senkt Kosten, stärkt Vertrauen — bester Nutzen/Aufwand-Punkt des Audits. | 4 | 2 | 1 | 2 | 4 | ⚪ | N |
| E40-3 | **Transparenz-Layer:** Provider-Badge („lokal" / „extern: OpenAI"), aufklappbarer Kontext-Inspektor (welche Passagen wurden gesendet, Modell, ungefähre Tokenzahl), ehrliches „nichts gefunden" bleibt. AK: Nutzer kann pro Antwort nachvollziehen, was das Gerät verlassen hat. | 4 | 2 | 1 | 2 | 4 | ⚪ | N |
| E40-4 | **Injection-Härtung + Read-only-Invariante:** Kontext klar delimitiert („Dokumente, keine Anweisungen"), Antwort wird nie als Aktion interpretiert, keine Tools im Answer-Pfad — als dokumentierte Invariante + Testabdeckung (Basis: OWASP LLM01, Dokumente = untrusted input; relevant ab E33-2/E22-5). | 4 | 2 | 2 | 3 | 4 | ⚪ | N |

Sinnvolle Reihenfolge Phase N: E37-2 (mit/nach E28-1) → E37-1 → E37-3 →
E38-1 + E38-2 → E38-3 → E39-1 → E40-1/2/3 → E40-4 → E38-4 → E37-4 →
E39-2/3. Reranker-Entscheidung erst nach E37-3-Messung.

---

## Phase O — Shared Knowledge & Small Teams (Team-Audit 2026-08)

Ergebnis des **Team-/Collaboration-Audits**
([`docs/audit-2026-08-team-collaboration.md`](./docs/audit-2026-08-team-collaboration.md)),
Einstufung **PERSONAL + SMALL TEAM**. Kernmodell: **Shared Instance** — ein
Team = eine Instanz = ein gemeinsamer Vault (konsistent mit ADR 0004/0007;
die Instanzgrenze bleibt die Isolationsgrenze, **kein** Multi-Tenant-Umbau).
Zielgruppe: 2–10 Personen (Familien, kleine Teams, Agenturen, Kanzleien) —
„das gemeinsame Gedächtnis, selbst gehostet, mit kontrollierter AI".
Kollaboration heißt geteiltes Wissen, **nicht** Echtzeit-Redaktion.

Phase O startet **nach** dem Phase-N-Kern: E38 (Permission-Muster) ist
Vorstufe von E42-2/E44-2, E34 (Git-Backup) von E43-2, E36-1 (Scoped Keys)
von E42-3. Vorstufe in Phase M: **E33-1 wird um `actor` erweitert**
(Attribution im Capture-Pfad — jetzt billig, nachträglich teuer).

**Bewusst NICHT gebaut (siehe Audit-Matrix):** Realtime-Editing (CRDT/OT,
Presence), Kommentare/Threads/Mentions/Notifications, Kanban/Sprints/
Projektmanagement (→ E35-Integrationen), externe Share-Links (P4,
beobachten), Multi-Tenant/Workspace-Tabellen, SSO/SAML/SCIM/Enterprise-IAM,
Cross-Instance-Links.

### E41 — Identity & Accounts · `epic:identity` (P0-Fundament)

Heute: ein geteiltes `UI_PASSWORD`, zustandslose Sessions, keine
`users`-Tabelle. Für Teams braucht jede Person Login + Attribution.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E41-1 | **Accounts + Login pro Person:** `users`-Tabelle (Name, E-Mail, Passwort-Hash argon2/bcrypt), Login-Session mit `user_id` (serverseitig widerrufbar statt zustandslos), Owner-Account im Setup-Wizard; `UI_PASSWORD` bleibt Single-User-Fallback (Personal-Modus unverändert). Bewusst **ohne** SSO/OIDC — built-in Login ist für kleine Teams ein Feature (Outline-Gegenbeispiel). AK: zwei Personen können sich getrennt an-/abmelden; Passwortwechsel einer Person wirft nicht alle raus. | 5 | 3 | 3 | 4 | 5 | ⚪ | O |
| E41-2 | **Attribution:** `created_by`/`updated_by` (nullable) auf `entries` + `author:` im Frontmatter; Telegram-ID→User-Mapping (Allowlist wird personenbezogen); Autor in Notes-API/UI sichtbar. Nutzt den `actor` aus E33-1. AK: „Wer hat das erfasst/geändert?" ist pro Notiz beantwortbar; Alt-Daten ohne Autor bleiben gültig. | 4 | 2 | 2 | 3 | 5 | ⚪ | O |
| E41-3 | **Einladung & Offboarding:** Invite-Link/-Code durch Owner (kein E-Mail-Server nötig), Eingeladener setzt eigenes Passwort (Default-Rolle Editor); Deaktivieren = Sessions + API-Keys sofort ungültig; Inhalte bleiben der Instanz (Attribution bleibt), dokumentiertes Verfahren für private Ordner Ausgeschiedener (Export/Überführung durch Owner). | 4 | 2 | 2 | 2 | 4 | ⚪ | O |

### E42 — Rollen & Sichtbarkeit · `epic:roles-visibility`

Drei Rollen, capabilities-basiert intern, serverseitig durchgesetzt —
und Ordner-Sichtbarkeit nach dem `ai_access`-Muster (E38), am selben
Durchsetzungspunkt **vor** dem Retrieval.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E42-1 | **Rollen Owner/Editor/Viewer:** Rolle am User, intern Capability-Mapping (`can(user, capability)`: read/write/manage_members/manage_ai/manage_settings/export); Durchsetzung in UI-Routen **und** REST/MCP (Backend-only, Frontend blendet nur aus). AK: Viewer kann suchen/lesen/fragen, aber weder capturen noch ändern; nur Owner sieht Settings/Members. | 5 | 3 | 3 | 3 | 5 | ⚪ | O |
| E42-2 | **Ordner-Sichtbarkeit `visibility`:** `team` (Default) \| `private` (nur Ersteller + dokumentierter Owner-Notfallzugriff) — Ordner-Regel in `vault_config.yaml` + Frontmatter-Override, denormalisiert auf `vault_note_index`; WHERE-Filter in `retrieve_vault_notes` (Suche, Vektor, RAG, Digest, Notes-API), fail-closed (unbekannt = privat). AK: CI-Invariante „User B findet/liest nie private Notizen von User A — auch nicht via Suche/AI/Embeddings". Abhängig von E38-1/2, E41-1. | 5 | 3 | 3 | 4 | 5 | ⚪ | O |
| E42-3 | **API-Keys pro Nutzer:** E36-1-Keys bekommen `user_id`-Bezug — REST/MCP-Zugriffe laufen unter Rolle + Sichtbarkeit des Key-Inhabers; Key-Widerruf beim Offboarding (E41-3). | 4 | 2 | 2 | 2 | 4 | ⚪ | O |

### E43 — Team-Gedächtnis & Wiki-Qualitäten · `epic:team-memory`

Wiki-*Qualitäten* (Auffindbarkeit, Vertrauen, Historie) statt Wiki-Produkt —
maximal auf Vorhandenem aufbauend (Git E34, Templates E26, entries).

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E43-1 | **Recently Changed & Autor:** „Zuletzt geändert"-Liste (Dashboard) + Autor/„zuletzt geändert von" auf der Notiz-Seite — aus `entries`-Attribution (E41-2) + Git-Log (E34-2); respektiert Sichtbarkeit. Bewusst ohne Mentions/Notifications (Pushes → Webhooks/n8n E35-3). | 4 | 2 | 1 | 2 | 4 | ⚪ | O |
| E43-2 | **Version History (git-basiert):** Verlauf pro Notiz (Zeitpunkt, Autor), Diff-Ansicht, Restore einzelner Versionen (als neuer Commit), Wiederherstellen gelöschter Notizen — UI über `GitVaultBackend`-Historie, **keine** eigene Revisions-DB. Auch für Einzelnutzer wertvoll (Undo über `/undo` hinaus). Abhängig von E34-1/2. AK: „Wer hat das geändert und wie sah es vorher aus?" in 2 Klicks. | 5 | 3 | 2 | 3 | 4 | ⚪ | O |
| E43-3 | **Team-Template-Paket:** mitgelieferte E26-Vorlagen für Profi-Nutzung — Meeting Notes, Decision Record, Project Brief, SOP, Retro, Kundennotiz; im geteilten Vault automatisch team-weit; Doku. | 3 | 1 | 1 | 1 | 3 | ⚪ | O |
| E43-4 | **Aufgaben-Ansicht (light):** Liste über `category: aufgabe` + `status: offen/erledigt` im Frontmatter, Abhaken in der UI, optional `assignee` (ab E41-2); Filter „mir zugewiesen". Bewusst **kein** Kanban/Due-Date-Engine/PM — echtes Projektmanagement via E35-3 (Todoist/Linear). | 3 | 2 | 1 | 2 | 3 | ⚪ | O |
| E43-5 | **Konflikt-Erkennung beim UI-Speichern:** mtime-/Hash-Check („Notiz wurde zwischenzeitlich geändert — neu laden/überschreiben"), Git als Sicherheitsnetz; bewusst **kein** Realtime-Editing/CRDT. Ergänzt E28-2 (File-Locks). | 3 | 2 | 2 | 2 | 3 | ⚪ | O |

### E44 — Team-AI & Administration · `epic:team-ai`

Fortsetzung von Phase N im Team-Kontext: der Owner kontrolliert, welche AI
das Team-Wissen sehen darf — Members können nur enger stellen, nie lockern.

| ID | Story | N | S | R | L | P | Status | Phase |
|----|-------|---|---|---|---|---|--------|-------|
| E44-1 | **Admin-AI-Policy:** Owner legt instanzweit fest: erlaubte Provider-/Trust-Klassen (nur `local`? auch `external`?), eigener Company-Endpoint (via E39-2), ob eigene Keys/Endpoints der Members erlaubt sind. Default restriktiv. Abhängig von E38-3. AK: Member kann keinen Provider nutzen, den die Policy verbietet. | 4 | 2 | 2 | 3 | 4 | ⚪ | O |
| E44-2 | **Permission-aware Team-RAG:** Retrieval-Filter dreidimensional — `ai_access(note) ∩ visibility(note, user) ∩ Kanal-Trust`; ein Nutzer ohne Ordner-Zugriff bekommt daraus **nie** RAG-Kontext (Filter vor Retrieval, E38-2-Mechanik). AK: CI-Invariante analog E42-2, zusätzlich für den LLM-Kontext. Abhängig von E38-2, E42-2. | 5 | 2 | 3 | 4 | 5 | ⚪ | O |
| E44-3 | **Security-Audit-Log (Owner):** Login-Ereignisse, Einladung/Entfernung, Rollenänderung, AI-Provider-/Policy-Änderung, Export, Löschungen — nur Metadaten, keine Inhalte (E31-3-konform); getrennt von der Activity-Liste (E43-1). Kein SIEM/Retention-Engine. | 3 | 2 | 1 | 2 | 3 | ⚪ | O |

Sinnvolle Reihenfolge Phase O: E41-1 → E41-2 (+ E33-1-`actor` liegt dann
vor) → E42-1 → E42-2 → E44-2 → E41-3 → E42-3 → E44-1 → E43-2 → E43-1 →
E43-5 → E43-3/4 → E44-3. Lizenz-Seite (Seats/`edition` im E21-1-Payload)
bei E21-2 (Verkaufskanal) mitdenken.

---

## Aktueller Sprint (Phase A — MVP-Härtung) ✅ abgeschlossen

1. 🟢 **Doku-Fundament**: ROADMAP, ARCHITECTURE, CHANGELOG, ADR-Struktur, LICENSE, setup-Doku
2. 🟢 **E1-1** — Allowlist
3. 🟢 **E2-3** — Dev-Endpunkte entfernen
4. 🟢 **E2-1 + E2-2** — Entry-Modell erweitern + Migration
5. 🟢 **E1-2** — Update-Idempotenz
6. 🟢 **E3-1** — Filename-Kollision verhindern
7. 🟢 **E8-1** — Settings-Klasse (pydantic-settings)

## Aktueller Sprint (Phase B — Produktfunktionen) ✅ abgeschlossen

1. 🟢 **E4-1 + E3-2** — Append-Logik (Killer-Feature)
2. 🟢 **E4-2** — Tags als strukturiertes Feld
3. 🟢 **E3-3** — Frontmatter-Updates bei Append (`updated:`-Datum, Tag-Merge)
4. 🟢 **E10-2** — Celery-Retries für OpenAI/Whisper (Reliability-Boost)
5. 🟢 **E1-3** — Telegram-Commands (`/start`, `/help`, `/recent`, `/find`, `/undo`)
6. 🟢 **E3-4** — Atomares Schreiben (Tempfile + `os.replace`)
7. 🟢 **E1-4** — Webhook-Body-Size-Limit + Ignore unbekannter Update-Typen

**Phasen A–F sind komplett** (Release-Linie v0.2.x). **Phase G** weitgehend:
E19/E20-1/2/4/E21-1/3 🟢; offen **E21-2** (Verkaufskanal); **E20-3/5** kein Nahziel.

## Sprint Phase H ✅ (Kern abgeschlossen)

1. 🟢 **E22-1** — UI-Capture (größte Produkt-Lücke: UI soll Haupteingang sein)
2. 🟢 **E22-3** — Digest in der Web-UI (klein, rundet Retrieval-UI ab)
3. 🟢 **E25-1** — Backup/Restore One-Click in Settings
4. 🟢 **E22-2** — Telegram Foto-/Dokument-Capture (nutzt vorhandene E18-Extractors)
5. 🟢 **E23-1** — UI-Auth (Voraussetzung für Mobile **und** Cloud)
6. 🟢 **E23-2** — PWA installierbar (danach E23-4 Share-Target)
7. 🟢 **E22-4** — MCP `capture_note` + `digest`
8. 🟢 **E26-1 + E26-2** — Notiz-Templates: Render-Template + Validierung/Fallback

Offen aus H (nach Phase L wieder aufnehmen): E22-5/6, E23-3/4, E25-2/4,
E26-3/4/6.

## Nächster Sprint (Phase L — Launch-Härtung, Reihenfolge nach Risiko/Nutzen)

Ergebnis Audit 2026-08 (**GO WITH CONDITIONS**) — diese Punkte kommen vor
Monetarisierung/Cloud:

1. 🔵 **E27-1** — P0: Proxy-sichere Zugriffskontrolle (`/setup` remote dicht)
2. 🔵 **E27-2** — XSS-Fix Dashboard/Login/Setup (Quick Win, hohes Risiko)
3. 🟢 **E27-3 + E27-4** — Sichere Defaults + Frontmatter-/Pfad-Härtung
4. 🟢 **E28-5** — Retry-/Status-Semantik (klein, entlastet Debugging sofort)
5. 🟢 **E29-1** — Dependencies pinnen + Dependabot (Quick Win)
6. 🟢 **E30-1** — Klickbare Suchtreffer/Quellen (größter UX-Hebel, Aufwand S)
7. 🟢 **E28-2 + E28-3** — File-Locks + Capture-Kompensation
8. 🟢 **E28-1** — Inkrementeller Index-Sync (Obsidian-Koexistenz-Versprechen)
9. 🟢 **E29-2 + E29-3** — CI-Härtung + Release v0.3.0
10. 🟢 **E30-3** — Post-Setup-Onboarding
11. 🔵 **E30-4** — Feedback-Layer
12. 🔵 **E31-1 + E31-3** — Voll-Löschung + Log-Hygiene
13. Danach: restliche E29/E30/E31-Stories, dann **Phase M** (Ecosystem &
    Interoperability, E32–E36 + E22-5/E23-4), danach **Phase N**
    (Privacy-First Knowledge AI, E37–E40; E37-2 ggf. mit E28-1 vorziehen),
    danach **Phase O** (Shared Knowledge & Small Teams, E41–E44) und
    parallel **E24-1** (ADR 0007 Cloud/Abo) und **E21-2** (Verkaufskanal)
    auf gehärteter Basis

## Verbleibender Backlog (übrig aus Phase G)

| ID | Fokus | Hinweis |
|----|-------|---------|
| **E21-2** | Verkaufskanal + Lizenz-Ausgabe | Kommerziell; bei Cloud-Entscheidung mit E24-4 zusammen denken |
| **E20-3 / E20-5** | Native Desktop-App / Code-Signing | Kein Nahziel; wenn überhaupt, dann als E23-5-Wrapper |

Integrations-Vision und Szenarien: [`docs/integrations/`](./docs/integrations/).

---

## Definition of Done (pro Story)

- [ ] Code-Änderung klein und fokussiert
- [ ] Tests vorhanden (oder bewusste Begründung warum nicht)
- [ ] `ruff check` und `pytest` grün
- [ ] CHANGELOG-Eintrag unter `[Unreleased]`
- [ ] ROADMAP-Status aktualisiert
- [ ] Manuell getestet: Telegram → Vault → Datei sichtbar
