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

### Stufe 2 — Semantische Suche (Phase E/F)

Pgvector-Embeddings pro Notiz, kNN-Lookup. Setzt `E5-3` voraus
(Embeddings werden beim Schreiben/Append berechnet — gleiche Pipeline,
nicht doppelt). Query bekommt ein Embedding, Treffer werden nach
Cosine-Similarity sortiert.

API-Erweiterung: `GET /v1/notes/search?q=...&semantic=true`.

**Story:** `E17-2`.

### Stufe 3 — RAG-Antwort / `/ask` (Phase F)

Retrieval (Stufe 1 oder 2) → ausgewählte Notiz-Snippets als Kontext in einen
Answer-Prompt → LLM antwortet mit **Quellenangabe**. Eigenes Pydantic-Schema
`AnswerResult { answer, sources: list[NoteRef], confidence }`. Quellen
werden als `[[Wiki-Links]]` ausgespielt — in Telegram klickbar zur
Vault-Notiz, in REST/MCP als strukturierte `sources`.

| Konsument | Aufruf | Antwort |
|-----------|--------|---------|
| Telegram | `/ask Was weiß ich über X?` | Antworttext + `[[Quellen]]` |
| REST | `POST /v1/ask { "question": "..." }` | `AnswerResult` JSON |
| MCP | Tool `ask_brain(question)` | `AnswerResult` |

**Stories:** `E17-3` (Service), `E17-4` (Telegram), `E17-5` (REST).

---

## Brain als Tool für Fremdagents — MCP-Server (Phase F)

Analog zum Custom-n8n-Node (`E14-2`) ein **separates Repo**
`seiton-brain-mcp`, das die Retrieval-API als Model-Context-Protocol-Server
wrappt. Damit kann jeder MCP-fähige Client meinen Vault als Wissensquelle
nutzen — Stand 2026 u. a.:

- **Claude Desktop** und **Claude Code CLI**
- **Cursor** (eingebauter MCP-Support)
- **VS Code Continue**, **Open-WebUI** und andere Open-Source-LLM-Clients
- **LangGraph / CrewAI / n8n LangChain-Nodes** für eigene Agent-Workflows

Verfügbare Tools:

| MCP-Tool | Wrappt | Anwendungsfall |
|----------|--------|----------------|
| `search_notes(query, semantic?)` | `GET /v1/notes/search` | Agent prüft, ob ich schon etwas weiß |
| `ask_brain(question)` | `POST /v1/ask` | Agent stellt mir Fragen an mein Wissen |
| `get_note(path\|id)` | `GET /v1/entries/{id}` | Volle Notiz nachladen |

Auth: `SEITON_API_KEY` — identisch zu E13-2. **Keine** anonymen Endpunkte;
Retrieval ist genauso sensibel wie Capture.

**Story:** `E17-6`.

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

(Story `E17-8`.)

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
5. Phase F-Bonus: `E17-8` Digest

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
- MCP-Server: eigenes Repo (analog `E14-2`) oder `examples/mcp/` im Hauptrepo?
