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
