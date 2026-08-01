# Multi-LLM in n8n (E7-4)

Power-User-Muster: **mehrere Modelle außerhalb des Python-Cores** orchestrieren,
Seiton bleibt Engine für Capture, Vault und Validierung.

> Kein Custom-n8n-Node (ADR 0004). Nur Standard-HTTP-Request-Nodes.
> Kern-Rollen (Router/Writer/Linker) bleiben in Seiton — siehe [E7-3](../llm-providers.md#classify-rollen-vs-ein-shot-e7-3) und [ADR 0003](../adr/0003-engine-and-adapters.md).

## Wann n8n, wann Core?

| Bedarf | Ort |
|--------|-----|
| create/append, Summary, Tags, Related (ein Provider) | **Seiton Core** (`SEITON_LLM_ROLES_ENABLED=true`) |
| billiges lokales Preprocessing + teures Cloud-Modell | **n8n** (dieses Muster) |
| fremde Inputs (E-Mail, Todoist) vor Capture | **n8n** → `POST /v1/capture` |
| Agent-Framework / undurchsichtige Graphen im Core | ❌ bewusst nicht (ADR 0003) |

Seiton validiert weiterhin JSON/Pydantic beim Capture. n8n liefert nur den
**Eingabetext** (ggf. angereichert) — keine parallele Vault-Schreiberei.

## Beispiel-Workflow 05

**Datei:** [`examples/n8n/05-multi-llm-enrich-then-capture.json`](../../examples/n8n/05-multi-llm-enrich-then-capture.json)

```
[Manual Trigger]
  → [Roh-Text]
  → [Ollama anreichern]          # lokales Modell, OpenAI-kompatibles /v1
  → [Antwort extrahieren]
  → [Seiton Capture]             # Core klassifiziert (Rollen E7-3)
```

1. Rohnotiz geht an **Ollama** (`POST …/v1/chat/completions`) — z. B. Klartext-
   Zusammenfassung auf Deutsch.
2. n8n übernimmt `choices[0].message.content`.
3. `POST /v1/capture` an Seiton mit dem angereicherten Text.

So mischst du **lokales** (Ollama) und **Core-LLM** (OpenAI oder Ollama je nach
`LLM_PROVIDER`) ohne den Core um ein Agent-Framework zu erweitern.

### Voraussetzungen

- Seiton läuft, `SEITON_API_KEY` gesetzt
- [Ollama](https://ollama.com) mit Modell, z. B. `ollama pull llama3.2`
- n8n kann Ollama und Seiton erreichen (siehe URL-Tabelle in
  [`examples/n8n/README.md`](../../examples/n8n/README.md))

Platzhalter im Workflow:

| Platzhalter | Bedeutung |
|-------------|-----------|
| `REPLACE_WITH_SEITON_API_KEY` | Header `X-Seiton-Api-Key` |
| `http://host.docker.internal:11434` | Ollama-Base (anpassen) |
| `llama3.2` | Ollama-Modellname |
| `http://host.docker.internal:8000` | Seiton-API |

### Varianten

**Zwei Cloud-Modelle:** zweiten HTTP-Request-Node (z. B. OpenAI Chat) vor Capture
einfügen — gleiches Muster, anderer `url` / Body.

**Nur klassifizieren:** statt Capture `POST /v1/classify` — kein Vault-Schreiben;
n8n entscheidet selbst über Speichern.

**Core schlank halten:** `SEITON_LLM_ROLES_ENABLED=false` → Ein-Shot-Classify in
Seiton; schwere Multi-Step-Logik bleibt in n8n. Meist unnötig: E7-3 deckt den
Alltag ab.

## Abgrenzung zu E7-3

E7-3 = **max. 2–3 typisierte Steps im Core** (Router → Writer → Linker), ein
Provider. E7-4 = **optionale Orchestrierung in n8n** für Power-User, die Modelle
mischen oder vorverarbeiten wollen — dokumentiert, nicht Produkt-Default.
