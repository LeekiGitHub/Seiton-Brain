# Knowledge Retrieval & Q&A

Wie das Wissen, das Seiton Brain erfasst, auch wieder **abgerufen** und
**befragt** wird — von mir selbst per Telegram, von eigenen Workflows per
REST, und von externen LLM-Agenten per MCP-Server.

> **Architektur:** Capture und Retrieve sind gleichwertige Hälften derselben
> Engine. Output-Adapter „Retrieval / Q&A" in
> [ADR 0003](../adr/0003-engine-and-adapters.md) und Engine+Adapter-Diagramm
> in [`ARCHITECTURE.md`](../../ARCHITECTURE.md).

---

## Motivation

Heute kann ich dem Bot Gedanken **schicken**. Das Wissen liegt strukturiert
im Vault — aber befragen kann ich es nur über Obsidian-Suche oder
Datei-Browsing. Ein echtes Second Brain muss auch antworten können auf:

- „Was weiß ich schon über X?"
- „Welche Ideen hatte ich letzte Woche zu Thema Y?"
- „Fasse mir alle Notizen zu Z zusammen."

…und dasselbe Wissen anderen Systemen als **Wissensquelle** zur Verfügung
stellen (n8n-Workflows, Claude Desktop, Cursor, eigene LLM-Agenten).

---

## Drei Stufen (empfohlene Reihenfolge)

### Stufe 1 — Keyword-Suche (Phase C) 🟢

Nutzt den Vault-Index aus `E5-1` (DB-Spiegel von Titel/Pfad/mtime, optional
Body-Snippets). Reicht für Telegram-`/find`, REST-`/v1/notes/search` und
n8n-„Search Notes"-Node.

| Konsument | Aufruf |
|-----------|--------|
| Telegram | `/find idee fitness` → Top-N Treffer-Liste |
| REST | `GET /v1/notes/search?q=idee+fitness` |
| n8n | HTTP-Request-Node bzw. Custom-Node-Operation `Search Notes` |

**Stories:** `E17-1`, `E1-3` (Telegram), `E13-1` (API).

### Stufe 2 — Semantische Suche (Phase E/F) 🟢

Pgvector-Embeddings pro Notiz, kNN-Lookup. Umgesetzt zusammen mit `E5-3`
(Embeddings werden beim Schreiben/Append/Sync berechnet — gleiche Pipeline,
nicht doppelt). Query bekommt ein Embedding, Treffer werden nach
Cosine-Distanz sortiert (`semantic_search_vault_notes`).

Bausteine:
- `app/llm/embeddings.py` — `EmbeddingProvider` (ABC) + `OpenAIEmbeddingProvider`,
  Factory `get_embedding_provider()`.
- `vault_note_index.embedding` — `Vector(1536)`-Spalte (pgvector); Migration
  legt die `vector`-Extension an. Postgres-Image: `pgvector/pgvector:pg16`.
- Opt-in via `EMBEDDINGS_ENABLED` (Default aus). Nach dem Aktivieren einmal
  einen Vault-Sync laufen lassen, um Bestandsnotizen zu embedden (Backfill).
  Embeddings sind best-effort — schlägt ein Call fehl, bleibt die Keyword-
  Suche voll funktionsfähig.

Bewusst **kein** ANN-Index (ivfflat/hnsw): bei persönlicher Vault-Größe ist
exakter kNN-Scan schnell genug; ANN ist eine spätere Skalierungs-Optimierung.

Offen (Konsumenten): `/find`-Semantik-Schalter (E1-3, optional).

**Story:** `E17-2` 🟢.

### Stufe 3 — RAG-Antwort / `/ask` (Phase F)

Retrieval (Stufe 1 oder 2) → ausgewählte Notiz-Snippets als Kontext in einen
Answer-Prompt → LLM antwortet mit **Quellenangabe**. Eigenes Pydantic-Schema
`AnswerResult { answer, sources: list[NoteRef], confidence }`. Quellen
werden als `[[Wiki-Links]]` ausgespielt — in Telegram klickbar zur
Vault-Notiz, in REST/MCP als strukturierte `sources`.

Der **Service** (`E17-3`) ist umgesetzt 🟢 — `app/services/answer.py`:

- `answer_question(question, db, *, limit, semantic)` — bevorzugt semantische
  Suche (wenn `EMBEDDINGS_ENABLED`), sonst Keyword-Fallback.
- Prompt `prompts/answer.txt`; LLM antwortet als JSON, geparst zu `LLMAnswer`.
- Quellen werden auf **real existierende** Treffer aufgelöst (Halluzinationen
  verworfen), `confidence` auf 0–1 geklemmt.
- Ohne Treffer: ehrliche „nichts gefunden"-Antwort **ohne** LLM-Call.
- `format_answer_for_chat()` rendert `[[Wiki-Links]]` für Chat-Surfaces.

| Konsument | Aufruf | Antwort | Status |
|-----------|--------|---------|--------|
| (Engine) | `answer_question(...)` | `AnswerResult` | 🟢 `E17-3` |
| Telegram | `/ask Was weiß ich über X?` | Antworttext + `[[Quellen]]` | 🟢 `E17-4` |
| Telegram | `/digest Ideas` | Themen-Synthese + `[[Quellen]]` | 🟢 `E17-8` |
| REST | `GET /v1/notes/search?q=...&semantic=true` | Treffer-Liste | 🟢 `E17-5` |
| REST | `POST /v1/ask { "question": "..." }` | `AnswerResult` JSON | 🟢 `E17-5` |
| REST | `POST /v1/digest { "topic": "...", "days": 7 }` | `DigestResult` JSON | 🟢 `E17-8` |
| MCP | Tool `ask_brain(question)` | `AnswerResult` | 🟢 `E17-6` |

`/ask` läuft asynchron über den Worker (LLM-Call): Sofort-Ack im Chat, Antwort
folgt mit aufgelösten `[[Quellen]]`. Andere Slash-Commands bleiben synchron.

**Stories:** `E17-3` 🟢 (Service), `E17-4` 🟢 (Telegram), `E17-5` 🟢 (REST), `E17-6` 🟢 (MCP).

---

## Brain als Tool für Fremdagents — MCP-Server (Phase F) 🟢

Unter [`examples/mcp/seiton-brain-mcp/`](../../examples/mcp/seiton-brain-mcp/README.md)
im Hauptrepo (dünner REST-Wrapper; separates Repo optional später). stdio-MCP
für Cursor, Claude Desktop und andere MCP-Clients — wrappt die Retrieval-API
(E17-5), keine Embedding-/RAG-Logik im MCP-Prozess.

| MCP-Tool | Wrappt | Anwendungsfall |
|----------|--------|----------------|
| `search_notes(query, semantic?)` | `GET /v1/notes/search` | Agent prüft, ob ich schon etwas weiß |
| `ask_brain(question)` | `POST /v1/ask` | Agent stellt mir Fragen an mein Wissen |
| `get_note(entry_id \| vault_path)` | `GET /v1/entries/{id}` / `GET /v1/notes/content` | Volle Notiz nachladen |

Auth: `SEITON_API_KEY` im MCP-Server-Env (identisch zu E13-2).

**Story:** `E17-6` 🟢.

---

## Brain als Knowledge-Backend in n8n- & Agent-Workflows (E17-7) 🟢

Capture-Events (`note.created`, `note.appended`) feuern **sofort** nach dem
Speichern — die semantische Suche ist zu dem Zeitpunkt evtl. noch nicht bereit
(Embedding-Berechnung läuft im selben Index-Schritt, Webhook-Reihenfolge:
`note.indexed` kurz vor `note.created`).

Für Workflows, die **Retrieval** brauchen (semantische Suche, RAG, MCP), ist
das Event **`note.indexed`** der richtige Trigger:

| Event | Wann | Payload (Auszug) | Typische n8n-Aktion |
|-------|------|------------------|---------------------|
| `note.indexed` | Embedding erfolgreich berechnet (`EMBEDDINGS_ENABLED`) | `vault_path`, `title`, `category`, `folder`, `doc_type` | `GET /v1/notes/search?semantic=true`, `POST /v1/ask`, Slack „Wissen aktualisiert" |
| `note.created` | Neue Notiz gespeichert | + `entry_id`, `classification` | Benachrichtigung ohne Retrieval |
| `note.appended` | Notiz ergänzt | wie oben | Review-Workflow |

Konfiguration: dieselbe `SEITON_WEBHOOK_URL` wie E13-3; Event im JSON-Feld
`event` oder Header `X-Seiton-Event`.

**Hinweis:** Bulk-Vault-Sync (`sync_vault_index_from_disk`) sendet **keine**
`note.indexed`-Events (Backfill würde sonst hunderte Webhooks auslösen).
Events kommen bei inkrementellem Indexieren über `upsert_vault_note_index`
(Capture, Append, Undo-Delete-Reindex).

### Beispiel-Flow (n8n)

```
Telegram → Seiton Capture
         → note.indexed Webhook
         → HTTP GET /v1/notes/search?q={{ $json.body.title }}&semantic=true
         → optional POST /v1/ask { "question": "Was steht in der neuen Notiz?" }
         → Slack / Mail
```

Importierbare Workflows: [`examples/n8n/`](../../examples/n8n/README.md) —
Workflow **02** (Event-Router inkl. `note.indexed`), **04** (Retrieval-API
nach indexiertem Wissen).

### Agent-Workflows (Cursor, Claude Desktop)

Externe LLM-Agenten nutzen den **MCP-Server** (E17-6) statt Webhooks —
gleiche REST-API, synchrones Tool-Use. n8n eignet sich für **asynchrone**
Ketten (Cron, Benachrichtigungen, Multi-Tool-Orchestrierung); MCP für
**interaktives** Coding/Chat mit direktem Vault-Zugriff.

**Story:** `E17-7` 🟢.

---

## Was Retrieval **nicht** sein soll

| Bereich | Bleibt aus | Grund |
|---------|------------|-------|
| Eigene Such-UI im Browser | ❌ | Obsidian-Suche reicht zum Browsen; Web-UI höchstens `E15-4` |
| Eigene Embedding-Engine | ❌ | Embeddings werden zentral in der Engine berechnet, nicht im MCP-Wrapper |
| Public/anonyme Q&A-Endpunkte | ❌ | Auth identisch zur Capture-API |
| Ersatz für ChatGPT/Claude als Allzweck-LLM | ❌ | RAG antwortet **nur** auf Basis des Vaults; Quellen-Pflicht im Schema |

---

## Beispiel-Szenarien

### A — Tagesfrage per Telegram

```
Ich: /ask Welche Travel-Ideen hatte ich für Japan?
Bot: Du hattest 3 Notizen dazu: [[Japan Reiseroute]] (Mai), 
     [[Tokio Cafés]] (April), [[JR Pass Optionen]] (März). 
     Kerngedanken: <Zusammenfassung mit Quellen>.
```

### B — Cursor-Agent nutzt mein Brain

In Cursor konfiguriert: MCP-Server `seiton-brain-mcp`. Beim Coding fragt der
Agent automatisch `ask_brain("Welche Lessons hatte ich zu Async-DB in
Celery?")` und bekommt meine ADR-Notizen als Kontext.

### C — n8n-Wochenrückblick

```
Cron (Sonntag) → POST /v1/digest { topic: "Ideas" }
              → LLM-Synthese aller Ideas-Notizen der Woche
              → Mail an mich + neue Notiz „Wochenrückblick KW XX"
```

(Story `E17-8` 🟢.)

### D — Bot-Self-Reference beim Capture

Beim nächsten Append-Schritt fragt die Engine intern selbst Retrieval:
„Existiert schon eine Notiz mit ähnlichem semantischen Inhalt?" — bessere
Duplikat-Erkennung als reines Titel-Matching. (Synergie E5-3 ↔ E17-2.)

---

## Abhängigkeiten (Reihenfolge)

1. Phase B: Append, Tags (sauberer Wissensbestand)
2. Phase C: REST-API + Auth (`E13-1`, `E13-2`), `E17-1` Keyword-Suche
3. Phase E: `E5-3` Embeddings, `E17-2` semantische Suche
4. Phase F: `E17-3..6` RAG, `/ask`, Retrieval-API, MCP-Server
5. Phase F-Bonus: `E17-8` Digest 🟢

---

## Offene Fragen (für spätere ADRs)

- Embedding-Provider abstrahieren (OpenAI vs. lokal über Ollama)? Vermutlich
  analog zu `LLMProvider` ein eigenes Interface.
- RAG-Kontextlänge & Chunking-Strategie pro Notiz (ganze Notiz vs. Sektionen
  vs. Update-Blöcke seit E3-2)?
- Sollen `/ask`-Antworten selbst wieder als Notiz im Vault landen (Audit
  „Was hat das Brain mir wann erzählt")? Naheliegender Vorschlag: `kind: qa`
  im `Entry`-Modell (siehe `KIND_VALUES`), Frontmatter mit `question:` und
  `sources:`. Macht das Brain selbst-referentiell — Q&A-Antworten werden
  beim nächsten Retrieval wieder mitgefunden.
- Rate-Limiting/Cost-Cap für Q&A (LLM-Kosten pro Frage > Capture)?
