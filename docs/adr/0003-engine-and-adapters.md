# ADR 0003: Engine + Adapter statt monolithischem Telegram/Obsidian-Bot

- **Status:** Accepted
- **Datum:** 2026-06-02
- **Entscheider:** Yannik
- **Phase / Epic:** Phase E · epic:api · epic:n8n · epic:vault

## Kontext

Seiton Brain startete als Telegram-Bot, der OpenAI nutzt und Markdown in einen
Obsidian-Vault schreibt. Das funktioniert, ist aber **kein vollständiges
Produktmodell** für ein public-ready Self-Hosting-Repo.

Geplante Erweiterungen (Diskussion 2026-06-02):

- **n8n** als Integrations- und Orchestrierungsschicht
- **Mehrere LLMs / spezialisierte Agent-Schritte**
- **Alternativen zu Obsidian** (andere Vault-Backends)
- **Einfaches Setup** (CLI/TUI), ohne Vertrauensprobleme bei API-Keys

Ohne klare Architekturentscheidung droht Feature-Creep: n8n ersetzt Celery,
Obsidian-Logik vermischt sich mit API-Logik, Setup-Skripte werden zu
Remote-Installern mit Key-Abfrage.

## Entscheidung

Seiton Brain wird langfristig als **Headless Second-Brain-Engine** modelliert.
**Telegram**, **Obsidian (Filesystem-Markdown)** und später **n8n** sind
**Adapter** — keine fest verdrahteten Kernbestandteile.

```
Eingänge (Input Adapters)     →  Core Engine  →  Ausgänge (Output Adapters)
Telegram, HTTP API, n8n, CLI       Queue/Worker      VaultBackend, Webhooks
                                   LLM Provider
                                   classify/route/append
                                   Postgres Audit
```

### Festlegungen

1. **Celery bleibt interner Job-Runner.** n8n orchestriert Integrationen
   *außerhalb* der Engine (Slack, Kalender, externe LLM-Ketten), ersetzt aber
   nicht Idempotenz, DB-Races und Worker-Retries.

2. **REST-API v1 ist Voraussetzung für n8n.** Erste n8n-Anbindung über
   Standard-HTTP-Request-Nodes; Custom Community-Node erst in separatem
   npm-Repo, wenn die API stabil ist.

3. **Vault als Interface (`VaultBackend`).** Das heutige Filesystem-Markdown
   (Obsidian-kompatibel) ist die erste Implementierung. Weitere Backends
   (Git, S3, read-only Web-UI) pluggen ein — **keine eigene Notiz-App** als
   Obsidian-Ersatz.

4. **LLM-Provider bleibt abstrahiert (`LLMProvider`).** Multi-Agent bedeutet
   zunächst 2–3 spezialisierte Prompts/Rollen mit Pydantic-Schemas zwischen
   Steps — nicht ein undurchsichtiges Agent-Framework. Externe Multi-Agent-
   Orchestrierung optional über n8n (Phase E).

5. **Setup: Keys nie an unsere Server.** Onboarding schreibt nur lokal
   `.env` (CLI/TUI/`seiton init`). Kein `curl | bash` mit Remote-Key-Upload.
   Siehe `docs/integrations/setup-onboarding.md`.

6. **Events nach außen.** Später Webhooks (`note.created`, `note.appended`) für
   n8n-Trigger — Engine bleibt Quelle der Wahrheit, n8n reagiert darauf.

## Konsequenzen

### Positiv

- Public Repo kann klar kommunizieren: *„Self-hosted Second Brain Engine“*
- Telegram-only-User und n8n-Power-User teilen denselben Core
- Obsidian optional — jeder Markdown-Ordner reicht
- Integrations-Ideen landen in Phase E, blockieren Phase B (Append) nicht

### Negativ / Trade-offs

- REST-API + Auth + Event-Webhooks sind zusätzlicher Aufwand vor n8n-Custom-Node
- `VaultBackend`-Abstraktion erfordert Refactor von `reader.py`/`writer.py`
- Zwei Repos für Custom n8n-Node (Wartung, Release-Zyklus)

### Folgearbeiten

- ROADMAP Phase E + Epics E13–E17 (siehe `ROADMAP.md`)
- `docs/integrations/` mit n8n-, Setup- und Vault-Backend-Notizen
- Phase C: REST-API v1 (`E13-1`)
- Phase D: n8n-Beispiel-Workflows, `seiton doctor` / `seiton init`
- Phase E: Custom n8n-Node (separates Repo), zweites VaultBackend

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|-------------|--------------|
| n8n ersetzt Celery intern | Schwächer bei Idempotenz, Retries, DB-Race; falsche Verantwortlichkeit |
| Alles in ein Repo (Python + n8n-Node) | Unterschiedliche Toolchains (npm vs. Python), Release-Chaos |
| Obsidian-Ersatz-App bauen | Ablenkung vom Kern; Markdown-Ordner + optional Web-UI reicht |
| Remote-Setup mit Key-Eingabe an uns | Vertrauensproblem; widerspricht Self-Hosting-Philosophie |
| Multi-Agent komplett in Python | Komplexität früh; n8n als optionaler Orchestrator flexibler |

## Referenzen

- Roadmap: [`ROADMAP.md`](../../ROADMAP.md) — Phase E, Epics E13–E17
- Integrationen: [`docs/integrations/`](../integrations/)
- Code heute: `app/services/process_message.py`, `app/llm/provider.py`, `app/vault/`
