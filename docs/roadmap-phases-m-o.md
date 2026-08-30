# Geplante Phasen M–O (Detail)

> **Ausgelagert im Rahmen von E45-13 (2026-08-29)** — nicht Historie, sondern
> **zukünftige** Planung in voller Story-Detailtiefe.  
> Einstieg und Reihenfolge: [`ROADMAP.md`](../ROADMAP.md) · Kurzstand:
> [`docs/current-state.md`](current-state.md)  
> Begründende Audits: [`audit-2026-08-integrations.md`](audit-2026-08-integrations.md),
> [`audit-2026-08-private-knowledge-ai.md`](audit-2026-08-private-knowledge-ai.md),
> [`audit-2026-08-team-collaboration.md`](audit-2026-08-team-collaboration.md).

Status-Legende: 🟢 Done · 🟡 In Progress · 🔵 Ready · ⚪ Backlog · ⚫ Aufgegangen

---

## Phase M — Ecosystem & Interoperability (Integrations-Audit 2026-08)

Ergebnis des **Integrations-/Ökosystem-Audits**
([`audit-2026-08-integrations.md`](./audit-2026-08-integrations.md)),
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

E34-3 (Offsite-Rezept) ist bewusst das **Rezept**, nicht die Produktfähigkeit.
Die Verallgemeinerung auf mehrere Ziele mit 3-2-1-Policy, Integritätsprüfung und
Backup-Health ist **E48 Backup Guardian** ([`ROADMAP.md`](../ROADMAP.md)) — nach
V1.5. Hier keine parallele Backup-Strategie aufbauen.

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
([`audit-2026-08-private-knowledge-ai.md`](./audit-2026-08-private-knowledge-ai.md)),
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
([`audit-2026-08-team-collaboration.md`](./audit-2026-08-team-collaboration.md)),
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


