# Private Knowledge AI, RAG & Personal Assistant — Audit 2026-08

**Datum:** 2026-08-18 · **Scope:** Produkt-/Architektur-Analyse, **keine Implementierung**
**Leitfrage:** Soll und kann Seiton Brain langfristig ein privates, durchsuchbares
Wissenssystem werden, auf das ein persönlicher AI-Assistent **kontrolliert**
zugreifen kann?

> **Status: Entscheidungsgrundlage.** Dieser Bericht ändert keinen Code.
>
> **Entscheidung (2026-08-18):** Strategie **D — Privacy-First Knowledge AI**
> (inkrementell B→C→D) vom Product Owner bestätigt. Umsetzung als
> **Phase N** in der ROADMAP: **E37** Retrieval-Fundament, **E38**
> Permission-Layer `ai_access`, **E39** Local AI komplett, **E40** Knowledge
> Chat. Strategie E (Agent) und die Tier-„NOT yet"-Liste (Abschnitt 17)
> bleiben bewusst außen vor.

Verwandte Dokumente: [`audit-2026-08-product-readiness.md`](./audit-2026-08-product-readiness.md)
(Phase L), [`audit-2026-08-integrations.md`](./audit-2026-08-integrations.md)
(Phase M, insb. E36 „Kontrollierter AI-Access"), ADR 0004/0006/0007.

---

## Executive Summary

**Antwort auf die Leitfrage: Ja — und wir sind näher dran, als die Frage
vermuten lässt.** Seiton Brain *ist* bereits ein privates, durchsuchbares
Wissenssystem mit RAG (`/ask`), semantischer Suche (pgvector), Multi-Format-
Ingestion (MD/TXT/PDF/DOCX/PPTX/OCR/Vision) und einer Provider-Abstraktion,
die heute schon OpenAI **und** Ollama (lokal) für Chat-Aufgaben unterstützt.
Was fehlt, ist nicht „AI einbauen", sondern vier gezielte Lücken schließen:

1. **Hybrid Retrieval** (Volltext + Vektor mit Rank-Fusion) statt des heutigen
   Entweder-oder-Fallbacks — der größte messbare Qualitätshebel.
2. **Lokale Embeddings** — der einzige Baustein, der einem vollständig lokalen
   Modus noch im Weg steht (Chat lokal ✅, Whisper lokal ✅, Embeddings ❌).
3. **Permission-Layer** (`ai_access` pro Ordner/Notiz) mit Filterung **vor**
   dem Retrieval — das ist das Differenzierungsmerkmal, das kein relevanter
   Wettbewerber granular anbietet.
4. **Knowledge Chat** als UI-Fläche (heute ist `/ask` ein One-Shot ohne
   Verlauf, Scope-Wahl oder Kontext-Transparenz).

Empfohlene Strategie: **D — Privacy-First Knowledge AI**, erreicht inkrementell
über B (Smart Retrieval) → C (Knowledge Chat) → D. Strategie E (Agent mit
Schreibrechten) bewusst **nicht** in der ersten Ausbaustufe.

---

## 1. Current State — Ist-Inventar

Legende: 🟢 implementiert · 🟡 teilweise · 🔵 technisch vorbereitet ·
📋 geplant (Roadmap) · ⚪ nicht vorhanden

| Fähigkeit | Status | Befund im Code |
|---|---|---|
| Full-Text Search | 🟡 | `search_vault_notes`: ILIKE über Titel/Body-Snippet/Chunks (`app/vault/index.py`). Kein Postgres-`tsvector`/BM25-Ranking — Substring-Match ohne Relevanz-Score. |
| Semantische Suche | 🟢 | `semantic_search_vault_notes`: pgvector-Cosine-kNN über Chunks, Dedup pro Dokument (bester Chunk gewinnt). Opt-in via `EMBEDDINGS_ENABLED`. |
| Embeddings | 🟡 | `EmbeddingProvider`-Interface mit `embed`/`embed_batch` — aber **nur OpenAI** implementiert (`text-embedding-3-small`, 1536 dim). `get_embedding_provider()` wirft bei `LLM_PROVIDER=ollama`. Kein Modell-/Dimensions-Metadatum am Chunk. |
| Vector Database | 🟢 | pgvector in bestehendem Postgres (`vault_chunk.embedding`), exakter kNN — für Single-User-Vaults richtig dimensioniert (ADR: kein HNSW nötig). |
| Chunking | 🟢 | `chunk_text` (E18-4): zeichenbasiert 1500/200 Overlap, Whitespace-bewusst. Kein Parent/Child, kein semantisches Chunking. |
| Indexierung | 🟢 | `vault_note_index` + `vault_chunk`; Upsert pro Write, `sync_vault_index_from_disk` als Voll-Scan. **Kein Content-Hash** — jeder Sync re-embedded alles (Kosten!). E28-1 (Index-Sync) ist geplant. |
| Metadata | 🟢 | Frontmatter (title, category), Ordner, `doc_type`, `mtime`. Kein `source`/`source_url` (📋 E33-1 Provenance), keine Tags im Index. |
| File Parsing | 🟢 | Extractor-Adapter (E18): Markdown, TXT/LOG, PDF (Text-Layer), DOCX (inkl. Tabellen), PPTX (inkl. Notizen), Bilder. ⚪ CSV/XLSX, HTML, ENEX, Code/Repos. |
| OCR | 🟢 | Tesseract für Bilder + PDF-Scans (E18-5, opt-in, `deu+eng`). |
| Search Ranking | ⚪ | Keyword: nur `mtime`-Sortierung. Semantisch: nur Cosine-Distanz. Keine Fusion, kein Reranking. |
| Hybrid Search | 🟡 | `retrieve_vault_notes(semantic=True)`: semantisch **oder** (bei 0 Treffern) Keyword — Fallback, keine Fusion (RRF fehlt). |
| RAG | 🟢 | `answer_question` (E17-3): Top-5-Retrieval → Kontext-Prompt → Antwort mit `sources` + `confidence`. Anti-Halluzinations-Guards: Quellen-Titel werden gegen echte Treffer aufgelöst (erfundene verworfen); ohne Treffer **kein LLM-Call** („nichts gefunden"). |
| AI/LLM Integration | 🟢 | `LLMProvider`-ABC + Factory: OpenAI, Ollama (OpenAI-kompatibles `/v1`). Rollen-Pipeline Router→Writer→Linker (E7-3). Whisper lokal via whisper.cpp (E6-4). Vision opt-in (E18-6). |
| Context Management | 🟡 | Kontext = 5 Hits à 400-Zeichen-Snippet. Kein Parent-Chunk-Nachladen, keine Kompression, kein Verlauf (One-Shot). |
| Permissions | ⚪ | Keine AI-Zugriffssteuerung auf Inhaltsebene. Ein API-Key, all-or-nothing (📋 E36-1 Scoped Keys, E36-2 Zugriffs-Log). |
| Collections/Workspaces | 🟡 | Ordner + Kategorien existieren (Vault-Struktur, `vault_config.yaml`); kein Workspace-/ACL-Konzept darüber. |
| Tags | 🟡 | In Notizen/Templates vorhanden, aber nicht im Index abfragbar. |
| Attachments/Uploads | 🟢 | Telegram-Dokumente/Fotos (E22-2), UI-Uploads — landen im Vault und werden indexiert. |
| Import | 🟡 | Vault = nativer Import (bestehende Obsidian-Vaults); 📋 E32-1 Onboarding, E32-3 ZIP-Import. |
| Background Processing | 🟢 | Celery + Redis; Scheduler-Grundlage (Beat) kommt mit E28-1. |
| APIs | 🟢 | REST `/v1`: capture, classify, entries, notes/content, notes/search, ask, digest. MCP-Server (`examples/mcp/`). Outbound-Webhooks. |
| Chat-UI | ⚪ | `/ask`-Seite = Frage→Antwort One-Shot. Kein Verlauf, kein Scope-Selector, kein Kontext-Inspektor. |
| Evaluation | ⚪ | 522 Unit-/Integrationstests, aber kein Retrieval-Qualitäts-Harness (Gold-Fragen). |

**Kernbefund:** Die Pipeline `Datei → Extraktion → Chunking → Embedding →
kNN → RAG mit Quellen` steht durchgängig. Die Lücken sind chirurgisch:
Ranking-Qualität, lokale Embeddings, Permission-Filter, Chat-Erlebnis,
Kosten-Hygiene (Hashing), Messbarkeit.

---

## 2. Existing AI/RAG Capabilities — Bewertung

Was heute schon **gut** ist (und so bleiben sollte):

- **Ehrlichkeit vor Eloquenz:** kein LLM-Call ohne Retrieval-Treffer;
  Quellen-Titel werden verifiziert statt geglaubt; `confidence` wird geclampt.
  Das ist genau die „Unsicherheit kommunizieren"-Grundhaltung aus der Leitfrage.
- **Ein Retrieval-Seam:** alle Konsumenten (Telegram `/ask`, REST, UI, MCP)
  laufen durch `retrieve_vault_notes()` / `answer_question()`. Hybrid-Fusion,
  Permission-Filter und Reranking können an **einer** Stelle eingebaut werden —
  keine Sackgasse.
- **Provider-Trennung:** Chat-LLM (`LLMProvider`) und Embeddings
  (`EmbeddingProvider`) sind getrennte Interfaces mit Factories — exakt das
  Adapter-Muster, das Abschnitt 6 fordert. Es fehlt nur die zweite
  Embedding-Implementierung.
- **Embeddings zentral in der Engine** (beim Indexieren), nicht in den
  Konsumenten — verhindert Drift und doppelte Kosten.

Was heute **begrenzt**:

- Kontext ist Snippet-basiert (400 Zeichen) — für „Fasse meine Notizen zu X
  zusammen" zu dünn; Chunk-Volltext bzw. Parent-Kontext wäre nötig.
- Keyword-Suche ohne Ranking versagt bei mehrwortigen Fragen; semantische
  Suche versagt bei exakten Begriffen (Produktnamen, Codes) — die Fusion
  beider ist der Standard-Fix (RRF, s. Abschnitt 5).
- `sync_vault_index_from_disk` re-embedded den gesamten Vault — bei 1k Notizen
  akzeptabel (~Cent-Bereich), aber unnötig und bei lokalen Embeddings langsam.

---

## 3. Potential User Value — Jobs to be Done

Aus Nutzersicht (Beispiel-Fragen aus dem Auftrag, gruppiert):

| Job | Beispiel | Braucht | Heute |
|---|---|---|---|
| **Wiederfinden** | „Wo war diese Info nochmal?", „In welcher Datei steht X?" | Hybrid Search, gute Snippets | 🟡 geht, Ranking schwach |
| **Erinnern** | „Habe ich dazu schon mal was geschrieben?" | Semantic Search + Similar Notes | 🟡 `/ask` kann es indirekt |
| **Verdichten** | „Fasse meine Notizen zu X zusammen" | RAG mit mehr Kontext pro Quelle | 🟡 Digest existiert, Kontext dünn |
| **Nachvollziehen** | „Zeig mir die Originalquelle" | Quellen-Links, Provenance | 🟢 sources / 📋 E33-1 |
| **Vergleichen/Widersprüche** | „Vergleiche Projekt A und B" | Multi-Query, größerer Kontext | ⚪ realistisch erst später |
| **Vertrauen** | „Was wurde an welches Modell geschickt?" | Kontext-Inspektor, External-AI-Indikator | ⚪ |

Der höchste Nutzwert liegt in den ersten vier Jobs — alle erreichbar mit
besserem Retrieval + moderatem Chat-Ausbau, **ohne** Agent, ohne neue Kanäle.
„Vergleichen/Widersprüche" ist ein Frontier-Feature; ehrlicher Umgang: erst
wenn Retrieval-Qualität gemessen gut ist.

---

## 4. File & Knowledge Source Support — „Knowledge Folder"

Bewertung pro Typ (Aufwand: S/M/L; RAG-Eignung: wie gut Text-Extraktion +
Chunking funktionieren):

| Typ | Status | RAG-Eignung | Privacy-Hinweis | Aufwand | Empfehlung |
|---|---|---|---|---|---|
| Markdown/TXT | 🟢 | exzellent | — | — | Kern, fertig |
| PDF (Text) | 🟢 | gut | oft sensibel (Verträge!) | — | fertig |
| PDF (Scan)/Bilder | 🟢 OCR | mittel | OCR lokal (Tesseract) ✅ | — | fertig |
| Bilder ohne Text | 🟢 Vision | mittel | ⚠️ Vision = Cloud-Call | — | Vision unter Permission-Layer stellen |
| DOCX/PPTX | 🟢 | gut | — | — | fertig |
| CSV/XLSX | ⚪ | schwach für RAG (Tabellen ≠ Prosa) | Finanzdaten! | M | Tier 2: indexieren ja, RAG-Erwartung dämpfen |
| HTML/Webseiten | ⚪ | gut nach Readability-Extraktion | Fremdinhalt = untrusted | M | via 📋 E33-2 URL-Capture, nicht als Datei-Typ |
| Audio/Transkripte | 🟢 | gut (Voice→Whisper→Text) | Whisper lokal möglich ✅ | — | fertig |
| Code/Projekte | ⚪ | eigene Disziplin (Code-RAG) | — | L | **nicht bauen** — Cursor/IDE-Domäne, MCP reicht |
| Git-Repos | ⚪ | wie Code | — | L | **nicht bauen** (E34 = Vault-Versionierung, nicht Repo-Ingestion) |
| E-Mail | 📋 E22-5 | gut | sehr sensibel | — | geplant, unter Permission-Layer |

**Antwort auf die Kernfrage:** Ja — das Produkt sollte „persönliches Wissen"
statt nur „Notizen" verstehen, und tut es faktisch schon (der Vault indexiert
heute PDFs, Office-Dateien, Bilder). Die richtige Erzählung ist nicht „neuer
Knowledge Folder", sondern: **der Vault ist der Knowledge Folder.** Fehlend
mit gutem Nutzen/Aufwand-Verhältnis: CSV/XLSX (einfach) und HTML via
URL-Capture (E33-2). Code/Git-Ingestion bewusst nicht — dafür gibt es
spezialisierte Tools, und unser MCP-Server macht Seiton-Wissen dort verfügbar.

---

## 5. RAG Architecture Recommendation

Stand der Technik 2026 (Recherche-Konsens) vs. was für **Personal** Knowledge
Management (10²–10⁴ Dokumente, Single-User, Deutsch+Englisch) wirklich lohnt:

| Verfahren | Konsens 2026 | Für Seiton | Begründung |
|---|---|---|---|
| Hybrid Search (BM25+Vektor, RRF-Fusion) | Standard, größter Basis-Hebel | ✅ **bauen** | Postgres `tsvector` (mit `german`/`english` Config) + bestehendes pgvector, RRF ist ~20 Zeilen SQL/Python; kein neues System. Fixt „exakte Begriffe" (Namen, Codes) und „vage Erinnerung" gleichzeitig. |
| Parent/Child-Chunks | verbreitet | 🟡 **light** | Voller Parent-Ansatz ist Overkill; stattdessen: Treffer-Chunk **voll** (statt 400-Zeichen-Snippet) + Nachbar-Chunks in den Kontext. Nutzt bestehende `chunk_index`-Spalte. |
| Cross-Encoder-Reranking | „höchster ROI nach Basics" | ⏳ **später, messbar** | Erst wenn Eval zeigt, dass Precision der Engpass ist (Konsens: nicht default bei kleinen Korpora). Lokal möglich (bge-reranker-v2-m3), CPU-tauglich. |
| Query Rewriting / Multi-Query / HyDE | situativ | ⏳ später | Zusätzliche LLM-Calls (Kosten/Latenz); erst nach Eval. |
| Semantic Chunking | situativ | ❌ nicht | Notizen sind kurz und strukturiert; Markdown-Überschriften-bewusstes Splitting wäre der einzige sinnvolle Refinement-Schritt. |
| Contextual Embeddings (Titel voranstellen) | +15–30 % Precision | 🟢 **haben wir** | `_embedding_text()` stellt bereits den Titel voran. |
| Citation Generation | Pflicht für Vertrauen | 🟢 haben wir | Quellen-Auflösung gegen echte Treffer. |
| Kontext klein halten (Top 3–8) | Konsens („lost in the middle") | 🟢 haben wir | Top-5-Default passt. |

**Empfohlene Ziel-Pipeline** (alles im bestehenden Stack):

```
Frage → [Permission-Filter: ai_access ∩ Scope]        (Abschnitt 8/9)
      → Volltext (tsvector) ∥ Vektor (pgvector)
      → RRF-Fusion (top ~30)
      → [später: lokaler Reranker → top 5]
      → Kontext: Treffer-Chunk voll + Titel + Pfad
      → LLM (Provider laut Trust-Level) → Antwort + verifizierte Quellen
```

Kein LangChain/LlamaIndex nötig — die Pipeline ist klein genug, um sie
weiter selbst zu besitzen (weniger Dependencies, keine Lizenz-/Churn-Risiken).

---

## 6. Local AI Feasibility

**Wie viel Modell braucht die Aufgabe?** Die Recherche stützt die These der
Leitfrage: Bei gutem Retrieval sind die generativen Aufgaben eines Second
Brain (Antwort aus 5 gegebenen Passagen formulieren, zusammenfassen, Tags
vorschlagen) **klein**. Extraktion + Grounding ist keine Frontier-Aufgabe.

| Aufgabe | Braucht großes LLM? | Lokal machbar mit |
|---|---|---|
| Dokumente finden | ❌ (kein LLM nötig) | Hybrid Search |
| Frage aus gegebenem Kontext beantworten | ❌ | Qwen3-8B / Gemma-Klasse (Q4) |
| Zusammenfassen | ❌ | dito |
| Klassifizieren/Tags | ❌ | läuft heute schon via Ollama |
| Komplexe Vergleiche/Synthese | 🟡 | 14B+ lokal oder Cloud |
| Vision (Foto-Beschreibung) | 🟡 | lokal möglich (Gemma multimodal), heute Cloud |

**Hardware-Realität 2026** (Konsens der Quellen): 16-GB-Laptop/Apple Silicon
→ 8B-Klasse (Q4) flüssig; 32 GB / 12 GB VRAM → 14B „best local"; CPU-only
→ langsam aber machbar (Phi-4-mini/Gemma-Small). Embeddings (BGE-M3, 568M
Parameter) und Reranker laufen problemlos auf CPU.

**Vollständig lokaler Modus — Lückenanalyse für Seiton:**

| Baustein | lokal heute? |
|---|---|
| Parsing/OCR | ✅ (pypdf, Tesseract, python-docx/pptx) |
| Chat-LLM | ✅ Ollama-Provider (E7-2) |
| Whisper | ✅ whisper.cpp (E6-4) |
| Vector Index | ✅ pgvector (läuft im eigenen Docker) |
| **Embeddings** | ❌ **einzige Lücke** — `get_embedding_provider()` wirft bei Ollama |
| Vision | ❌ (nur OpenAI) — opt-in, verschmerzbar |

Lokale Embeddings via Ollama (`bge-m3`: MIT-Lizenz, 100+ Sprachen, **stärker
als OpenAI-3-small auf Deutsch/multilingual**, 1024 dim) schließen die Lücke.
**Architektur-Konsequenz:** Vektor-Dimension ist heute hart 1536 — der Wechsel
braucht Embedding-Metadaten (Modell, Dimension) pro Chunk/Index-Generation und
eine Re-Index-Routine bei Modellwechsel. Das ist die wichtigste „heute
vorbereiten"-Entscheidung (Abschnitt 15).

UX-Ehrlichkeit: „Local AI" bleibt vorerst ein Power-User-Modus (Ollama
installieren, Modell ziehen, RAM). Für Consumer: Cloud-Default mit ehrlicher
Anzeige + lokaler Modus als dokumentierter, geführter Pfad — kein eigenes
Modell-Management in Seiton bauen (Ollama/LM Studio machen das besser).

---

## 7. Cloud/BYOK Architecture

**Wichtige Einordnung:** Im Self-Hosted-Modell (heute) ist **jeder Key ein
BYOK** — `OPENAI_API_KEY` gehört dem Nutzer, Seiton ist nie Zwischenhändler.
Das ist bereits die datenschutzfreundlichste Konstellation. BYOK als
*Feature-Frage* stellt sich erst bei der Cloud-Edition (E24 / ADR 0007).

Provider-agnostisch — Bewertung des Ist-Zustands:

- ✅ Chat: Interface + Factory vorhanden; da Ollama via OpenAI-kompatiblem
  `/v1` läuft, deckt derselbe Pfad **jeden** OpenAI-kompatiblen Endpoint ab
  (LM Studio, vLLM, Mistral API, Azure OpenAI, Gateways). Fehlt nur:
  generischer `openai_compatible`-Provider mit freier `base_url` (klein).
- ✅ Embeddings: Interface vorhanden, zweite Implementierung fehlt (s. o.).
- ⚪ Reranking: kein Interface — bei Bedarf analog anlegen (drittes, kleines
  Interface; nicht auf Vorrat).
- 🟡 Vision: hartkodiert OpenAI — bei Gelegenheit hinter dasselbe Muster.
- ❌ Anthropic/Gemini native SDKs: **nicht bauen.** OpenAI-kompatible Ebene +
  Gateways decken den Bedarf; jedes native SDK ist Wartungslast.

BYOK-Betriebsfragen (relevant ab Cloud-Edition): Key-Speicherung verschlüsselt
(Keyring-Grundlage E16-5 existiert), kein Key in Logs (Log-Hygiene E31-3),
Kostenkontrolle = Token-Zähler pro Antwort anzeigen (auch heute sinnvoll),
Provider-Ausfall = sauberer Fehler statt stillem Fallback auf anderen Provider
(**kein Auto-Fallback über Trust-Grenzen hinweg** — ein „Local-only"-Setup darf
bei Ollama-Ausfall niemals still zu OpenAI wechseln).

---

## 8. Privacy Permission Model

**Das Herzstück.** Vorschlag: ein Feld `ai_access` mit vier Stufen, definiert
auf **Ordner-Ebene** (primär) mit **Notiz-Override** (Frontmatter):

```
ai_access: none | local | trusted | external   (Default: external*)
```

| Stufe | Bedeutung |
|---|---|
| `none` | Nie für AI: kein Embedding, kein Retrieval-Kandidat, kein LLM-Kontext. Nur klassische Keyword-Suche in der UI. |
| `local` | Nur Provider der Klasse „local" (Ollama auf eigener Maschine). |
| `trusted` | + selbst gehostete/vom Nutzer kontrollierte Endpoints (eigener vLLM, EU-Gateway). |
| `external` | + konfigurierte externe APIs (OpenAI, …). |

\* Default `external` entspricht dem Status quo (Nutzer hat OpenAI-Key
bewusst konfiguriert); beim Setup/Onboarding wird der Default erklärt und
pro Ordner änderbar gemacht („Finanzen → nie an externe AI").

**Wo definiert:** `vault_config.yaml` (Ordner-Regeln, versionierbar, auch für
Obsidian-Nutzer lesbar) + Frontmatter-Override pro Notiz + UI in Settings.
**Wo durchgesetzt:** denormalisiert als Spalte auf `vault_note_index` (beim
Indexieren aufgelöst) → Retrieval filtert per WHERE-Klausel.

**Granularität bewusst begrenzt:** Ordner + Notiz reichen (deckt Workspace-,
Collection- und Dokument-Ebene der Anforderung ab — Ordner *sind* unsere
Collections). Tag-basierte Regeln und Abschnitts-Granularität = spätere
Ausbaustufe; Abschnitts-Granularität vermutlich nie (Komplexität vs. Nutzen).

Provider bekommen eine deklarierte **Trust-Klasse** (local/trusted/external) —
konfiguriert, nicht erraten. Die Prüfung ist ein simpler Vergleich:
`nutzbar wenn trust(provider) ≤ ai_access(note)`.

**Sensitive Data Controls (Abschnitt 11 des Auftrags):** `ai_access: none`
deckt „Exclude from AI + Exclude from embeddings" in einem ab (bei `none`
wird gar nicht erst embedded — sonst lägen Vektoren sensibler Inhalte in der
DB). Automatische Sensibilitäts-Erkennung: höchstens als **Hinweis** beim
Capture („sieht nach Finanzdaten aus — Ordner ‚Finanzen' ist auf ‚lokal
only' gestellt?"), niemals als alleinige Barriere. Der Nutzer entscheidet.

---

## 9. Security & Threat Model (Permission-Aware RAG)

**Pipeline-Prinzip — Filter vor Retrieval, nicht danach:**

```
Frage → Provider bestimmen → Trust-Klasse → erlaubte ai_access-Stufen
     → WHERE ai_access ∈ erlaubt  (im Retrieval-SQL, eine Stelle)
     → kNN/Volltext nur über erlaubte Chunks → Kontext → LLM
```

Da alle Konsumenten durch `retrieve_vault_notes()` laufen, gibt es genau
**einen** Durchsetzungspunkt — testbar mit dem Muster der Proxy-Guard-Tests
(E27-1): „externe AI erhält nie einen `local`-Chunk" als CI-Invariante.

Nebenkanäle, die mitgedacht werden müssen: Embeddings (bei `none` nicht
erzeugen, bei Stufenwechsel nach unten löschen), Prompt-/Debug-Logs (nie
Kontext-Inhalte loggen — E31-3-konform), Backups (Vault-Backup enthält alles —
ok, ist lokal; aber kein Prompt-Cache einführen), Webhook-Payloads (nur
Metadaten, keine Inhalte — heute schon so).

**Threat Model (Dokumente = untrusted input):**

| Bedrohung | Relevanz | Gegenmaßnahme |
|---|---|---|
| Indirect Prompt Injection (PDF, geteilte URL, E-Mail → Notiz → `/ask`-Kontext) | **hoch**, steigt mit E33-2/E22-5 | Read-only-Pipeline (keine Tools im Answer-Pfad — ist heute so, **beibehalten**); Kontext klar delimitiert („Dokumente, keine Anweisungen"); Antwort wird nie als Aktion interpretiert |
| Data Exfiltration via Injection | mittel | Kein Tool-Zugriff im Answer-Pfad = kein Exfil-Kanal; Markdown-Link-Rendering in UI ohne Auto-Fetch |
| Permission-Filter-Bug | hoch (Kernversprechen) | Ein Durchsetzungspunkt + Invarianten-Tests + fail-closed (unbekannte Stufe = `none`) |
| Kompromittierter API-Key | mittel | Scoped Keys (E36-1), Zugriffs-Log (E36-2) |
| Channel-Leak (Telegram liefert `local`-Inhalte aus) | mittel | Kanäle bekommen ebenfalls Trust-Klassen: Telegram = `external`-Kanal ⇒ `/ask` via Telegram sieht nur `external`-freigegebene Inhalte (gleicher Filter, zweite Dimension) |
| RAG-Corpus-Poisoning | niedrig (Single-User, eigener Vault) | Provenance (E33-1): „Woher kam diese Notiz?" sichtbar |
| Cross-User-Leakage | n/a heute (Single-User); Pflicht-Design bei E24 Cloud | strikte Instanz-Trennung (ADR 0007: eigene Instanzen — gut) |

**Chat ≠ Agent (Abschnitt 13 des Auftrags):** Die heutige Architektur ist
faktisch Read-only — das ist ein **Sicherheitsmerkmal**, kein Mangel.
Empfehlung: Read-only als Architektur-Invariante der ersten Ausbaustufen
dokumentieren. Schreibende AI-Aktionen (Notizen ändern, löschen) erst als
eigene, spätere Entscheidung mit Confirmation + Audit + Undo (Git-Backup E34
wäre das natürliche Undo-Fundament).

---

## 10. Cost Analysis

Kostenrealität für einen persönlichen Vault (Rechenbasis: 1 000 Notizen ×
~500 Token; `text-embedding-3-small` ≈ $0.02/1M Token):

| Posten | Einmalig (1k Notizen) | Laufend |
|---|---|---|
| Voll-Embedding | ~$0.01 | pro neuer Notiz ~$0.00001 |
| `/ask`-Frage (gpt-4o-mini-Klasse, ~2k Kontext + Antwort) | — | ~$0.001–0.003 |
| Digest | — | ~$0.005 |
| OCR (Tesseract) | 0 (lokal) | 0 |
| Vision | — | ~$0.002–0.01/Bild (deshalb opt-in — richtig so) |

**Embeddings sind ein Rundungsfehler; LLM-Antworten sind Zehntelcents.**
Für Self-Hosted mit eigenem Key ist Kostenkontrolle kein Blocker — aber
Hygiene lohnt trotzdem:

1. **Content-Hashing** (Hash pro Chunk, nur Geändertes re-embedden) — spart
   Cloud-Cents, macht aber v. a. **lokale** Embeddings praktikabel (CPU-Zeit!)
   und gehört ohnehin zu E28-1 (Index-Sync). Höchste Priorität.
2. Token-/Kosten-Transparenz pro Antwort (UI) — Vertrauen + BYOK-Vorbereitung.
3. Kein Embedding-Cache-Service, kein Semantic-Cache — Overengineering bei
   dieser Größenordnung.

Geschäftsmodell-Sicht (E24-Vorgriff): Self-Hosted = BYOK per Definition;
Cloud-Edition kann „wir zahlen AI, Abo deckt es" (kalkulierbar, da Kosten/User
niedrig) **oder** BYOK anbieten — Architektur muss dafür nur Keys pro Instanz
sauber trennen, was ADR 0007 (eigene Instanzen) bereits erledigt.

---

## 11. Competitive Analysis

| Produkt | Modell | Stärken | Schwächen / Nutzerkritik | Lehre für Seiton |
|---|---|---|---|---|
| **Khoj** (~20k ⭐, AGPL) | Self-hosted Second-Brain-Chat | Obsidian/Emacs-Integration, viele Clients (auch WhatsApp), lokale LLMs | Setup-Hürde, simple Memory-Schicht, AGPL blockt kommerzielle Einbettung | Engster Verwandter. Differenz: unsere Capture-Pipeline + Permission-Layer; MIT-Lizenz ist Vorteil |
| **AnythingLLM** (MIT) | Desktop/Docker „private ChatGPT for docs" | Polierte UI, Workspaces (grobe Isolation), jeder Provider | Default-Embeddings = OpenAI (Falle!), Obsidian-Integration schwach | Workspaces = gröbste Form unseres Permission-Layers; UI-Messlatte |
| **Obsidian Smart Connections / Copilot** | Plugins, BYOK/lokal | Lokale Embeddings zero-config, 786k+ Downloads → **bewiesene Nachfrage** | Nur im Obsidian-Desktop, kein Capture, kein Server | Koexistenz statt Konkurrenz (E32-2); zeigt: lokale Embeddings sind Consumer-tauglich |
| **Notion AI** | Cloud, kein BYOK | Nahtlos integriert | Kein BYOK („walled garden"-Kritik), Inhalte zu Dritt-LLMs, Lock-in-Angst | Genau die Gegenposition, die uns definiert: BYOK + lokal + granulare Kontrolle |
| **Reor / Msty / PrivateGPT** | Local-first Desktop | Volle Privatsphäre | Kein Capture-Flow, Insellösungen | Local-only als *Modus*, nicht als Produktgrenze |

**Positionierungs-Lücke im Markt:** Alle bieten entweder „alles lokal" oder
„alles Cloud" oder grobe Workspace-Trennung. **Niemand bietet granulare
Per-Ordner-Kontrolle „diese Inhalte nur lokal, jene auch extern" in einem
Capture-first-Produkt.** Das ist unsere glaubwürdige Differenzierung — und
E36 („Kontrollierter AI-Access") aus dem Integrations-Audit ist der bereits
bestätigte erste Schritt in genau diese Richtung.

---

## 12. Retrieval-without-LLM Opportunities

Mit vorhandenen Embeddings + Index heute schon möglich, **ohne** generative
Calls (0 Kosten, 0 Halluzination, 0 Privacy-Transfer bei lokalen Embeddings):

| Feature | Basis | Aufwand |
|---|---|---|
| **Similar Notes** („Ähnliche Notizen" auf der Notiz-Seite) | kNN auf bestehende Vektoren | S |
| **„Dazu hast du schon geschrieben"** beim Capture (Dedup/Verknüpfungs-Hinweis) | kNN auf neuen Text vor dem Schreiben | S–M |
| Bessere UI-Suche (Hybrid-Ranking auch in `/notes`) | selbe RRF-Pipeline | S (fällt mit ab) |
| Related-Links im Frontmatter (Linker-Rolle stärken) | kNN statt LLM-Raten | M |
| Topic-Clustering / Timeline | Embedding-Clustering | M–L, später |

Diese Features tragen die Produktstrategie **„excellent retrieval first,
chatbot second"**: Sie liefern täglich sichtbaren Wert, machen die
Retrieval-Qualität für den späteren Chat messbar besser und funktionieren
für *alle* Nutzer — auch die, die AI-Skepsis haben und `ai_access`
restriktiv setzen.

---

## 13. Recommended Product Strategy

| Strategie | Nutzerwert | Differenzierung | Komplexität | Privacy-Risiko | Monetarisierung | Urteil |
|---|---|---|---|---|---|---|
| A — No AI | niedrig | keine (Markt ist weiter) | — | — | schwach | ❌ verspielt vorhandene Assets |
| B — Smart Retrieval | hoch | mittel | **niedrig** | minimal | solide Basis | ✅ als Fundament |
| C — Knowledge Chat | hoch | mittel (viele haben Chat) | mittel | mittel | gut | ✅ als zweite Stufe |
| **D — Privacy-First Knowledge AI** | **hoch** | **hoch (Marktlücke, s. 11)** | mittel–hoch | **niedrig by design** | **stark (zahlungsbereite Zielgruppe: Anwälte, Ärzte, Berater)** | ⭐ **Empfehlung** |
| E — Knowledge Agent | spekulativ | mittel | hoch | **hoch** | unklar | ⏳ bewusst vertagen |

**Empfehlung: D als Nordstern, erreicht als B → C → D.** Die Stufen sind
keine Alternativen, sondern eine Rampe: B (Hybrid Retrieval + Similar Notes)
ist für C Voraussetzung, C (Chat mit Quellen) ist für D die Fläche, D
(Permission-Layer + Local Embeddings + Transparenz) ist das Versprechen.
Jede Stufe ist einzeln shipbar und einzeln wertvoll.

Das passt zudem exakt zur bestehenden Planung: Phase L härtet die Basis,
Phase M (E32–E36) baut Offenheit + kontrollierten AI-Zugriff — Strategie D
ist die konsequente Fortsetzung, nicht ein Schwenk.

---

## 14. Potential MVP — „Chat with your own knowledge"

Kleinste Version mit „Wow, ich kann mein Wissen wirklich fragen" —
abgeleitet aus unserer Architektur (nicht aus der Beispiel-Liste):

1. **Hybrid Search** — `tsvector` + pgvector + RRF in `retrieve_vault_notes`
   (ein Modul, eine Migration). Verbessert sofort `/ask`, `/find`, REST, MCP, UI.
2. **Index-Hygiene** — Content-Hash pro Chunk + Embedding-Metadaten
   (Modell/Dimension); Re-Index nur bei Änderung. (Synergie/Teil von E28-1.)
3. **`ai_access`-Permission-Layer** — Ordner-Regel + Frontmatter-Override,
   denormalisiert im Index, WHERE-Filter im Retrieval, Invarianten-Tests.
4. **Lokale Embeddings** — `OllamaEmbeddingProvider` (bge-m3), geführter
   Modellwechsel mit Re-Index. Schließt den Local-First-Modus.
5. **Chat-Seite** — `/ask` wird Konversation: Verlauf (Session, nicht
   persistiert), **Scope-Selector** (ganzer Vault / Ordner / Kategorie),
   Quellen-Links auf Notizen, Provider-Badge („lokal" / „extern: OpenAI"),
   aufklappbarer **Kontext-Inspektor** („diese 5 Passagen wurden gesendet").
6. **Retrieval-Eval-Harness** — 30–50 deutsche Gold-Fragen gegen einen
   Fixture-Vault; Hit-Rate@5 als CI-Metrik (ohne LLM lauffähig → keine
   API-Kosten in CI). Faithfulness stichprobenartig manuell.

Bewusst **nicht** im MVP: Reranker (erst wenn Eval ihn rechtfertigt),
Query-Rewriting, persistente Chat-Historie, neue Kanäle, Agent-Aktionen,
CSV/XLSX, automatische Sensibilitäts-Erkennung.

Der Per-Conversation-Scope (Punkt 5) ist dabei doppelt wertvoll: Privacy-
Kontrolle **und** Retrieval-Präzision **und** Kostenreduktion in einem
UI-Element — der beste Nutzen/Aufwand-Punkt des gesamten Konzepts.

---

## 15. Future Architecture — was heute vorbereiten

Sackgassen-Vermeidung, geordnet nach „nachträglich teuer":

| Entscheidung | Warum jetzt | Aufwand jetzt |
|---|---|---|
| **Embedding-Metadaten** (Modell, Dimension, Version) pro Chunk/Index-Generation | Ohne sie ist jeder Modellwechsel (lokal! besser! billiger!) ein manueller Vault-Reset; Dimension 1536 ist derzeit implizit verdrahtet | S (Spalten + beim Schreiben füllen) |
| **Content-Hash** im Index | Re-Embedding-Kosten, lokale Performance, E28-1 braucht ihn ohnehin | S |
| **Provenance** (`source`, `source_url`) | bereits als E33-1 bestätigt — auch Threat-Model-relevant („Woher kam diese Notiz?") | geplant |
| **`ai_access`-Konvention reservieren** (Frontmatter-Feld + `vault_config.yaml`-Schema dokumentieren) | Fremd-Tools/Nutzer sollen das Feld nicht anders belegen; Durchsetzung kann später kommen | XS (Doku) |
| **Trust-Klasse pro Provider** im Config-Modell | verhindert späteres „welcher Provider ist eigentlich lokal?"-Raten; verbietet Auto-Fallback über Trust-Grenzen | S |
| **Read-only-Invariante des Answer-Pfads** dokumentieren | schützt vor versehentlichem „Agent-Creep" bei künftigen Features | XS |
| Retrieval hinter einem Seam halten | ✅ ist bereits so (`retrieve_vault_notes`) — Konvention festschreiben | XS |

**Nicht** auf Vorrat bauen: Reranking-Interface, Plugin-System,
Workspace-Tabellen, Kanal-Matrix-UI, Anthropic/Gemini-SDKs, Multi-User-ACL
(ADR 0004/0007: eigene Instanzen).

---

## 16. Datenschutz / Deutschland / EU (keine Rechtsberatung)

- **Self-Hosted (heute):** Nutzer ist für seine eigenen Daten selbst
  verantwortlich; Seiton überträgt nur an vom Nutzer konfigurierte Provider.
  Wichtig bleibt Transparenz (welche Daten gehen wohin — Kontext-Inspektor)
  und Datensparsamkeit (nur Top-5-Passagen, nie den ganzen Vault).
- **Cloud-Provider-Realität 2026:** OpenAI/Anthropic trainieren per Default
  nicht auf API-Daten, DPA + SCCs verfügbar; echte EU-Residenz: OpenAI
  EU-Endpoint (approval-gated) / Azure OpenAI EU / Vertex EU / Mistral (EU-
  Anbieter). Für die Doku heißt das: EU-bewussten Nutzern OpenAI-kompatible
  EU-Endpoints empfehlen können — unsere `base_url`-Flexibilität (Abschnitt 7)
  macht genau das möglich, ohne Code.
- **Embeddings sind personenbezogene Daten** (Konsens; Inversionsangriffe
  existieren): Löschung einer Notiz muss Chunks+Vektoren mitlöschen
  (✅ kaskadiert heute), `ai_access: none` darf gar nicht erst embedden,
  Stufen-Downgrade muss Vektoren aufräumen.
- **Besondere Kategorien (Gesundheit, Finanzen):** exakt der Anwendungsfall
  des Permission-Layers — Architektur ermöglicht DSGVO-Argumentation
  („Gesundheitsordner verlässt nachweislich nie das Gerät").
- **Schwer umkehrbare Entscheidungen:** Provenance nachrüsten (deshalb E33-1
  jetzt), Embedding-Metadaten nachrüsten (deshalb MVP-Punkt 2), Logging-
  Disziplin (nie Prompt-Inhalte loggen — von Anfang an, E31-3).
- **Cloud-Edition (E24):** dann volle AVV-/Subprozessor-Kette nötig; ADR 0007
  (Instanz pro Kunde) hält das Cross-Tenant-Risiko strukturell klein.

---

## 17. Risks & Things We Should Explicitly NOT Build Yet

**Risiken:**

| Risiko | Schwere | Mitigation |
|---|---|---|
| Permission-Layer-Bug untergräbt das Kernversprechen | hoch | ein Durchsetzungspunkt, fail-closed, Invarianten-Tests in CI |
| Retrieval-Qualität enttäuscht → „AI ist dumm"-Eindruck | mittel | Eval-Harness **vor** Chat-Ausbau; ehrliches „nichts gefunden" beibehalten |
| Scope-Creep Richtung Agent/Kanäle | mittel | Read-only-Invariante; Kanal-Ausbau erst nach D-Kern |
| Lokal-Modus-Support-Last (Ollama-Setups) | mittel | „geführter Power-User-Pfad" statt Vollautomatik; doctor.sh-Check |
| Prompt Injection über capturte Fremdinhalte | mittel | Read-only-Pipeline, Delimiting, Provenance sichtbar |

**Bewusst NICHT bauen (jetzt):**

- **Agent mit Schreibrechten** (Strategie E) — erst wenn D steht, mit
  Confirmation/Audit/Undo-Konzept.
- **Reranker als Default** — erst nach gemessenem Bedarf (Eval).
- **Query-Rewriting / Multi-Query / HyDE / Knowledge Graph** — Overengineering
  für Vault-Größen unserer Zielgruppe.
- **Neue Kanäle** (WhatsApp, Discord, Slack, Voice) — Telegram + Web + REST +
  MCP decken die Jobs; jeder Kanal ist eine eigene Trust-Grenze.
- **Anthropic-/Gemini-native SDKs** — OpenAI-kompatible Ebene reicht.
- **Automatische PII-/Sensibilitäts-Klassifikation als Barriere** — höchstens
  als Hinweis; Kontrolle bleibt beim Nutzer.
- **Eigenes Modell-Management** (Downloads, Updates) — Ollama/LM Studio
  delegieren.
- **Persistente Chat-Historie / Memory-System** — erst wenn der Chat selbst
  bewiesen hat, dass er genutzt wird (und dann als Privacy-Entscheidung).

---

## Abschließende Empfehlung

**Sollten wir diese Richtung verfolgen? Ja.** Sie ist die natürliche
Fortsetzung dessen, was schon gebaut ist (RAG, Provider-Abstraktion, lokaler
Chat), sie besetzt eine real existierende Marktlücke (granulare Per-Ordner-
AI-Kontrolle in einem Capture-first-Produkt), und sie stärkt statt verwässert
das Kernversprechen „deine Daten, deine Kontrolle".

- **Heute architektonisch vorbereiten:** Embedding-Metadaten + Content-Hash
  (mit E28-1), `ai_access`-Konvention + Provider-Trust-Klassen dokumentieren,
  Provenance (E33-1, bestätigt), Read-only-Invariante festschreiben.
- **Erstes AI-Feature:** Hybrid Search (RRF) + Similar Notes — größter
  Qualitätssprung, kein einziges neues Privacy-Risiko, nützt jedem Feature
  danach. Direkt danach: Permission-Layer + lokale Embeddings + Chat-Seite
  (MVP, Abschnitt 14).
- **Bewusst verschieben:** Agent-Schreibrechte, Reranking, neue Kanäle,
  Chat-Persistenz, CSV/XLSX, Sensibilitäts-Automatik (Liste in Abschnitt 17).

**Produktprinzip, festgeschrieben:**
`User data → Permission/Trust Boundary → Retrieval → Context Selection → Model`
— der Filter sitzt **vor** dem Retrieval, ein externes Modell kann Inhalte
ohne Freigabe strukturell nicht erhalten.

Nächster Schritt nach Bestätigung: Epics/Stories ausarbeiten (voraussichtlich
als Phase N bzw. Erweiterung von E36) — erst nach ausdrücklichem Go.
