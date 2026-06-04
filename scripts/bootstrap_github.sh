#!/usr/bin/env bash
# Idempotentes Bootstrap-Skript für GitHub Labels, Milestones und initiale Issues.
# Voraussetzung: `gh` ist installiert und authentifiziert (`gh auth login`).
# Aufruf:
#   ./scripts/bootstrap_github.sh
#
# Mehrfaches Ausführen ist sicher — bestehende Labels/Milestones/Issues werden
# nicht doppelt angelegt.

set -euo pipefail

REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
echo "Repo: $REPO"

# ─── Labels ─────────────────────────────────────────────────────────────────────

# Format: name|color|description
LABELS=(
  # Epics
  "epic:telegram|0E8A16|Telegram input, webhook, bot UX"
  "epic:vault|1D76DB|Obsidian vault: reader, writer, conflicts"
  "epic:llm|5319E7|LLM classification, prompts, providers"
  "epic:db|0052CC|Database schema, migrations, persistence"
  "epic:voice|D93F0B|Voice transcription"
  "epic:infra|FBCA04|Docker, config, hosting, reliability"
  "epic:docs|C2E0C6|Documentation, onboarding, ADRs"
  "epic:public-ready|BFD4F2|Licensing, contributor docs, public-release prep"
  "epic:api|006B75|REST API, webhooks, external integrations"
  "epic:n8n|FF6D00|n8n workflows and community node"
  "epic:retrieval|7B61FF|Knowledge retrieval, RAG, /ask, MCP server"

  # Types
  "type:feature|A2EEEF|New feature"
  "type:bug|D73A4A|Something is broken"
  "type:chore|EDEDED|Maintenance, refactor, cleanup"
  "type:docs|0075CA|Documentation only"

  # Priorities
  "priority:high|B60205|High priority"
  "priority:medium|FBCA04|Medium priority"
  "priority:low|C5DEF5|Low priority"

  # Phases
  "phase:A-mvp|0E8A16|Phase A — MVP hardening"
  "phase:B-product|1D76DB|Phase B — Product features"
  "phase:C-robustness|5319E7|Phase C — Robustness & self-hosting"
  "phase:D-public|FBCA04|Phase D — Public release v1.0"
  "phase:E-integrations|FF6D00|Phase E — Integrations & ecosystem"
  "phase:F-knowledge|7B61FF|Phase F — Knowledge retrieval & Q&A"

  # Meta
  "meta:epic-tracker|6B7280|Umbrella issue tracking sub-stories of an epic"
)

echo ""
echo "── Labels ─────────────────────────────────────────"
for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<< "$entry"
  if gh label list --repo "$REPO" --limit 200 --json name -q '.[].name' | grep -Fxq "$name"; then
    echo "  ✓ exists: $name"
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" >/dev/null
    echo "  + created: $name"
  fi
done

# ─── Milestones ─────────────────────────────────────────────────────────────────

# Format: title|description
MILESTONES=(
  "Phase A — MVP|Ich nutze es zuverlässig allein. Auth, Datenhygiene, keine Notiz-Überschreibung."
  "Phase B — Product|Append-Logik, Telegram-Commands, Tags."
  "Phase C — Robustness|Retries, Logging, Mac Mini 24/7-Host, Cloudflare Tunnel."
  "Phase D — Public v1.0|Setup-Doku, optionaler Ollama-Provider, LICENSE-Ergänzungen."
  "Phase E — Integrations|REST-API, n8n, Vault-Backends, Setup-CLI. Siehe docs/integrations/."
  "Phase F — Knowledge|Brain als Wissensquelle: Suche, RAG, /ask, MCP-Server. Siehe docs/integrations/knowledge-retrieval.md."
)

echo ""
echo "── Milestones ─────────────────────────────────────"
existing_ms=$(gh api "repos/$REPO/milestones?state=all" --jq '.[].title')
for entry in "${MILESTONES[@]}"; do
  IFS='|' read -r title desc <<< "$entry"
  if echo "$existing_ms" | grep -Fxq "$title"; then
    echo "  ✓ exists: $title"
  else
    gh api "repos/$REPO/milestones" -f title="$title" -f description="$desc" >/dev/null
    echo "  + created: $title"
  fi
done

# ─── Issues ─────────────────────────────────────────────────────────────────────
#
# Format pro Issue:
#   title|milestone|labels (komma-separiert)|body
#
# Sortierung folgt der ROADMAP.md. Wir legen nur die Stories der Phase A
# automatisch als Issues an (das sind die unmittelbar relevanten). Phase B–D
# bleiben in der ROADMAP als Backlog, bis wir näher dran sind.

ISSUES=(
"E1-1: Telegram-Allowlist (TELEGRAM_ALLOWED_USER_IDS)|Phase A — MVP|epic:telegram,type:feature,priority:high,phase:A-mvp|Aktuell kann jeder mit Bot-Token Nachrichten an den Bot schicken. Wir wollen, dass nur konfigurierte Telegram-User-IDs verarbeitet werden.

**Akzeptanzkriterien**
- Env-Variable \`TELEGRAM_ALLOWED_USER_IDS\` (komma-separiert) in \`.env.example\` dokumentiert
- Webhook lehnt unbekannte User mit \`200 OK\` + freundlicher Nachricht ab (kein 401, damit Telegram nicht retried)
- Test deckt Allow- und Deny-Fall ab

**Story-ID:** E1-1
**Bewertung:** N5 · S1 · R1 · L2 · P5"

"E2-3: Dev-Endpunkte /entries entfernen|Phase A — MVP|epic:db,type:chore,priority:high,phase:A-mvp|Die Endpunkte \`POST /entries\` und \`GET /entries\` in \`app/main.py\` stammen aus Epic 2 als Schreib-/Lese-Test und sind ungeschützt.

**Akzeptanzkriterien**
- Beide Endpunkte aus \`app/main.py\` entfernt
- Imports von \`Entry\` / \`select\` ggf. mit entfernt
- Tests laufen weiter grün

**Story-ID:** E2-3
**Bewertung:** N3 · S1 · R1 · L2 · P4"

"E11-1: LICENSE (MIT) hinzufügen|Phase A — MVP|epic:public-ready,type:docs,priority:high,phase:A-mvp|Vorbereitung public-ready. Ohne LICENSE darf strenggenommen niemand das Repo nutzen.

**Akzeptanzkriterien**
- \`LICENSE\`-Datei im Root (MIT)
- README erwähnt License

**Story-ID:** E11-1
**Bewertung:** N5 · S1 · R1 · L1 · P5"

"E2-1: Entry-Modell erweitern (telegram_*, raw_input, vault_path, status, kind)|Phase A — MVP|epic:db,type:feature,priority:high,phase:A-mvp|Aktuell speichert die DB nur title/category/summary. Für Idempotenz, /recent, /undo und Append-Logik brauchen wir mehr Felder.

**Akzeptanzkriterien**
- \`Entry\` um folgende Felder erweitert:
  - \`telegram_chat_id: BigInteger\`
  - \`telegram_message_id: BigInteger\`
  - \`telegram_update_id: BigInteger UNIQUE\`
  - \`raw_input: Text\` (Originaltext bzw. Transkript)
  - \`vault_path: String\` (relativ zum Vault)
  - \`status: String\` (\`processed\` | \`failed\` etc.)
  - \`kind: String\` (\`text\` | \`voice\`)
- ORM-Tests bleiben grün

**Story-ID:** E2-1
**Bewertung:** N5 · S2 · R2 · L4 · P5"

"E2-2: Alembic-Migration für erweitertes Entry-Modell|Phase A — MVP|epic:db,type:feature,priority:high,phase:A-mvp|Folge-Issue zu E2-1.

**Akzeptanzkriterien**
- Neue Migration in \`alembic/versions/\` (autogenerate)
- \`upgrade\` und \`downgrade\` implementiert
- Backfill-tauglich: bestehende Zeilen mit sinnvollen Defaults
- \`docker compose run --rm api alembic upgrade head\` läuft sauber durch

**Story-ID:** E2-2
**Bewertung:** N3 · S2 · R2 · L4 · P4"

"E3-1: Filename-Kollision im Vault verhindern|Phase A — MVP|epic:vault,type:feature,priority:high,phase:A-mvp|\`write_note\` schreibt \`{title}.md\` und überschreibt stillschweigend existierende Notizen gleichen Titels.

**Akzeptanzkriterien**
- Wenn Zieldatei existiert: nicht überschreiben, sondern \`Title (2).md\`, \`Title (3).md\` etc.
- Test deckt Kollisionsfall ab

**Story-ID:** E3-1
**Bewertung:** N5 · S2 · R3 · L3 · P5"

"E8-1: Settings-Klasse (pydantic-settings)|Phase A — MVP|epic:infra,type:chore,priority:medium,phase:A-mvp|Aktuell \`os.environ[...]\` an Modul-Ebene in mehreren Dateien. Bei fehlender Env-Variable knallt der Import mit kryptischem \`KeyError\`.

**Akzeptanzkriterien**
- \`app/config.py\` mit \`Settings(BaseSettings)\` (pydantic-settings)
- Alle \`os.environ[...]\`-Lookups durch \`settings.<feld>\` ersetzt
- Fehlende Env → klare \`ValidationError\`-Meldung beim Start
- \`requirements.txt\` ergänzt

**Story-ID:** E8-1
**Bewertung:** N4 · S2 · R1 · L4 · P4"

"E1-2: Update-Idempotenz (telegram_update_id unique)|Phase A — MVP|epic:telegram,type:feature,priority:medium,phase:A-mvp|Telegram retried Webhooks bei Timeout. Aktuell führt das zu doppelten Notizen.

**Akzeptanzkriterien**
- Vor dem Enqueue (oder im Worker) Check, ob \`telegram_update_id\` schon existiert
- DB-Unique-Constraint (siehe E2-1) verhindert Race-Condition
- Bei Duplikat: silent ack, kein zweiter Worker-Lauf

**Abhängigkeit:** E2-1, E2-2
**Story-ID:** E1-2
**Bewertung:** N4 · S2 · R2 · L4 · P4"

# ─── Phase B — aktuelle/nächste Stories ─────────────────────────────────────

"E3-3: Frontmatter-Updates bei Append (updated + Tag-Merge)|Phase B — Product|epic:vault,type:feature,priority:medium,phase:B-product|Beim Append (E3-2) bleibt das Frontmatter heute unverändert. Eine Notiz, an die 5× angehängt wurde, zeigt immer noch nur das \`created\`-Datum vom ersten Mal — schlecht für Obsidian-\"Sort by modified\" und für Tag-Konsolidierung.

**Akzeptanzkriterien**
- Beim Append: Frontmatter parsen, \`updated: <heute>\` setzen (Feld neu, falls noch nicht da)
- Tags mergen: bestehende + neue Tags vereinen, deduppen, lowercase (gleiche Sanitize-Logik wie E4-2)
- Test deckt ab: Updated-Datum gesetzt, Tag-Merge ohne Duplikate
- Frontmatter bleibt valides YAML

**Abhängigkeit:** E3-2 ✅, E4-2 ✅
**Story-ID:** E3-3
**Bewertung:** N3 · S2 · R2 · L3 · P3"

"E3-4: Atomares Schreiben im Vault (Tempfile + os.replace)|Phase B — Product|epic:vault,type:chore,priority:medium,phase:B-product|Aktuell schreibt der Writer direkt in die Zieldatei. Bei Obsidian Sync (Syncthing/iCloud) sieht der Sync-Client kurzzeitig halbe Dateien, was zu Sync-Konflikten führen kann.

**Akzeptanzkriterien**
- \`write_note\` und \`append_to_note\` schreiben in Tempfile im selben Verzeichnis, dann \`os.replace\` → atomare Veröffentlichung
- Funktioniert auch auf macOS/Linux/Windows (Verzeichnis-Kongruenz beachten)
- Test simuliert Crash zwischen Schreiben und Replace, prüft dass Zieldatei intakt bleibt

**Story-ID:** E3-4
**Bewertung:** N3 · S1 · R2 · L4 · P3"

"E10-2: Celery-Retries mit Backoff für OpenAI/Whisper|Phase B — Product|epic:infra,type:feature,priority:medium,phase:B-product|OpenAI- und Whisper-Calls können transiente Fehler werfen (Rate-Limit, Network, 5xx). Aktuell crasht der Task ohne Retry — User bekommt nur die generische \"Etwas ist schiefgelaufen\"-Nachricht.

**Akzeptanzkriterien**
- \`autoretry_for=(openai.APIError, httpx.HTTPError, ConnectionError)\` an Celery-Tasks
- Backoff: exponentiell, max 3 Retries, max 60s
- Bei finalem Fehlschlag: \`Entry.status = 'failed'\` (wenn schon angelegt) + Telegram-Fehlermeldung
- Test mit Mock, der erste 2 Calls fehlschlagen lässt → 3. Call klappt

**Story-ID:** E10-2
**Bewertung:** N4 · S2 · R2 · L4 · P4"

"E1-3: Telegram-Commands (/start, /help, /recent, /find, /undo)|Phase B — Product|epic:telegram,type:feature,priority:medium,phase:B-product|Aktuell verarbeitet der Webhook jeden Text als Capture-Input. Slash-Commands für Self-Service-Workflows fehlen.

**Akzeptanzkriterien**
- \`/start\` und \`/help\`: kurze Anleitung
- \`/recent [n]\`: letzte N Einträge mit \`[[Title]]\` zurück (Default 5)
- \`/find <query>\`: Substring-Suche über Titel (Vorbereitung E17-1)
- \`/undo\`: löscht den letzten Eintrag des Users (DB + Vault-Datei) — mit Bestätigung
- Tests für jeden Command (Mock-DB, Mock-Vault)

**Abhängigkeit:** E2-1 ✅ (Titel/User-ID-Felder)
**Story-ID:** E1-3
**Bewertung:** N4 · S2 · R1 · L3 · P4"

"E1-4: Webhook-Body-Size-Limit + Ignore unbekannter Update-Typen|Phase A — MVP|epic:telegram,type:chore,priority:low,phase:A-mvp|Sicherheits-/Robustheits-Hardening. Aktuell nimmt der Webhook beliebig grosse Payloads an und ignoriert nur implizit Update-Typen ausser \`message\`.

**Akzeptanzkriterien**
- Body-Size-Limit (z. B. 1 MB) — größere Requests werden mit 413 abgelehnt
- Bekannte aber nicht unterstützte Update-Typen (\`edited_message\`, \`callback_query\`, …) → 200 OK ohne Verarbeitung, kein Warnings-Log-Spam
- Test deckt beide Pfade ab

**Story-ID:** E1-4
**Bewertung:** N2 · S1 · R2 · L2 · P2"

# ─── Epic-Tracker für Phase C–F (Umbrella-Issues mit Checkboxen) ───────────
#
# Statt 30+ Mini-Issues für Stories, die noch Phasen entfernt sind, legen wir
# je Epic ein Tracker-Issue an. Wenn wir näher an der Implementierung sind,
# splitten wir die Checkboxen in eigene Issues.

"Epic E13 — REST API & Events|Phase C — Robustness|epic:api,meta:epic-tracker,priority:medium,phase:C-robustness|Sammelt die Stories für eine interne REST-API (Voraussetzung für n8n und MCP).

**Stories**
- [ ] E13-1: REST-API v1 (\`POST /v1/capture\`, \`POST /v1/classify\`, \`GET /v1/entries\`)
- [ ] E13-2: API-Key-Auth (\`SEITON_API_KEY\` + Header \`X-Seiton-Api-Key\`)
- [ ] E13-3: Outbound Webhooks (\`note.created\`, \`note.appended\`, \`entry.failed\`) — Phase E
- [ ] E13-4: OpenAPI/Swagger unter \`/docs\`

Details: \`ROADMAP.md\` Epic E13, \`docs/integrations/n8n.md\`."

"Epic E14 — n8n-Ökosystem|Phase D — Public v1.0|epic:n8n,meta:epic-tracker,priority:medium,phase:D-public|Beispiele und optionaler Community-Node für n8n.

**Stories**
- [ ] E14-1: \`examples/n8n/\` Workflow-JSONs (Capture, Webhook-Trigger, Todoist→Seiton)
- [ ] E14-2: Community-Node \`n8n-nodes-seiton-brain\` (separates Repo) — Phase E
- [ ] E14-3: README/Doku \"Seiton + n8n\"

Details: \`docs/integrations/n8n.md\`."

"Epic E15 — Vault Backends|Phase D — Public v1.0|epic:vault,meta:epic-tracker,priority:medium,phase:D-public|\`VaultBackend\`-Interface + Filesystem-Implementierung; weitere Backends optional.

**Stories**
- [ ] E15-1: \`VaultBackend\`-Protocol; Filesystem aus reader/writer extrahieren
- [ ] E15-2: Doku \"Obsidian optional\"
- [ ] E15-3: Git-backed Vault (optional) — Phase E
- [ ] E15-4: Read-only Web-UI (optional) — Phase E

Details: \`docs/integrations/vault-backends.md\`."

"Epic E16 — Setup & Onboarding CLI|Phase D — Public v1.0|epic:public-ready,meta:epic-tracker,priority:medium,phase:D-public|Easy Setup für Selfhoster — Keys nur lokal, kein Remote-Install mit Key-Upload.

**Stories**
- [ ] E16-1: \`scripts/init.sh\` / \`make init\`
- [ ] E16-2: \`seiton doctor\` (Health-CLI)
- [ ] E16-3: \`seiton init\` TUI (lokal, kein Netzwerk-Upload)
- [ ] E16-4: Browser-Setup \`localhost:8000/setup\` (optional) — Phase E

Details: \`docs/integrations/setup-onboarding.md\`."

"Epic E17 — Knowledge Retrieval & Q&A|Phase F — Knowledge|epic:retrieval,meta:epic-tracker,priority:medium,phase:F-knowledge|Brain als Wissensquelle: Capture und Retrieve als gleichwertige Hälften.

**Stories**
- [ ] E17-1: Keyword-Suche über Vault-Index (\`/find\`, \`/v1/notes/search\`) — Phase C/E
- [ ] E17-2: Semantische Suche via pgvector (benötigt E5-3) — Phase E/F
- [ ] E17-3: RAG-Antwort-Service (\`AnswerResult\` mit Sources)
- [ ] E17-4: Telegram-Command \`/ask <frage>\`
- [ ] E17-5: Retrieval-API (\`POST /v1/ask\`, semantische Search-Query)
- [ ] E17-6: MCP-Server \`seiton-brain-mcp\` (separates Repo) — Phase F
- [ ] E17-7: Outbound-Event \`note.indexed\` + n8n-Doku
- [ ] E17-8: (Optional) Digest-Synthese \`/digest <thema>\` — Phase F-Bonus

Details: \`docs/integrations/knowledge-retrieval.md\`, ROADMAP Epic E17."
)

echo ""
echo "── Issues ─────────────────────────────────────────"
existing_titles=$(gh issue list --repo "$REPO" --state all --limit 200 --json title -q '.[].title')

for entry in "${ISSUES[@]}"; do
  IFS='|' read -r title milestone labels body <<< "$entry"
  if echo "$existing_titles" | grep -Fxq "$title"; then
    echo "  ✓ exists: $title"
  else
    gh issue create \
      --repo "$REPO" \
      --title "$title" \
      --body "$body" \
      --milestone "$milestone" \
      --label "$labels" >/dev/null
    echo "  + created: $title"
  fi
done

echo ""
echo "Done. Optional: GitHub Project (v2) Board anlegen:"
echo "  gh project create --owner @me --title 'Seiton Brain'"
echo "  → dann Issues per UI ins Board ziehen"
