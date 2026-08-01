# LLM-Provider (OpenAI & Ollama)

Seiton Brain abstrahiert Klassifikation, RAG-Antwort und Digest hinter
`LLMProvider` (`app/llm/provider.py`). Beide Wege liefern dasselbe
Pydantic-Schema (`ClassificationResult` / `LLMAnswer` / `LLMDigest`).

## OpenAI (Default)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Ollama (E7-2)

Lokales Modell über Ollamas OpenAI-kompatibles API (`/v1/chat/completions`):

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Voraussetzungen:

1. [Ollama](https://ollama.com) installieren und starten
2. Modell ziehen, z. B. `ollama pull llama3.2`
3. Modell sollte dem Classify-Prompt folgen und **JSON** ausgeben können
   (wir senden `response_format: json_object` und parsen mit Retry wie bei OpenAI)

### Docker → Host-Ollama

Läuft die API/Worker in Docker und Ollama auf dem Host:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

(Linux ggf. Extra-Host/`--add-host=host.docker.internal:host-gateway` oder die
LAN-IP des Hosts.)

### Was bleibt bei OpenAI?

- **Whisper** (Sprachnachrichten) und **Embeddings** (semantische Suche) nutzen
  weiterhin den OpenAI-Client, bis es lokale Adapter gibt.
- Für reinen Text-Capture mit Ollama kannst du `OPENAI_API_KEY` setzen und Voice/
  Embeddings auslassen bzw. `EMBEDDINGS_ENABLED=false` lassen.

## Classify: Rollen vs. Ein-Shot (E7-3)

Standard: **Router → Writer → Linker** (max. 3 LLM-Calls; Linker entfällt bei
leerem Vault). Aggregat bleibt `ClassificationResult` — Vault/API unverändert.

```env
SEITON_LLM_ROLES_ENABLED=true
SEITON_PROMPT_VERSION=v1
```

Prompts: `prompts/router.v1.txt`, `writer.v1.txt`, `linker.v1.txt`.
`SEITON_LLM_ROLES_ENABLED=false` nutzt den Legacy-Ein-Shot `classify.v1.txt`
(weniger Tokens/Kosten).

## Multi-LLM in n8n (E7-4)

Für **gemischte Modelle** (z. B. Ollama vorverarbeiten → Seiton Capture) siehe
[`docs/integrations/n8n-multi-llm.md`](integrations/n8n-multi-llm.md) und Workflow
`examples/n8n/05-multi-llm-enrich-then-capture.json`. Der Core bleibt bei max.
2–3 Rollen (ADR 0003); schwere Orchestrierung gehört nach n8n.

## Umschalten

`LLM_PROVIDER` ändern und API/Worker neu starten. Keine Migration nötig —
`prompt_version` und Vault-Pipeline bleiben gleich.
