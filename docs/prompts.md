# Prompts

LLM-Prompts liegen versioniert unter `prompts/`.

## Classify (Capture)

| Datei | Bedeutung |
|-------|-----------|
| `classify.v1.txt` | Aktuelle Version **v1** (Default) |
| `classify.txt` | Legacy-Fallback (Inhalt identisch zu v1) |

Neue Version anlegen:

1. `cp prompts/classify.v1.txt prompts/classify.v2.txt` und anpassen
2. In `.env`: `SEITON_PROMPT_VERSION=v2`
3. API/Worker neu starten

Die verwendete Version wird bei jedem Capture in `entries.prompt_version`
gespeichert (E4-4) — nützlich für Audit und Prompt-A/B-Vergleiche.

## Answer / Digest

`answer.txt` und `digest.txt` sind vorerst unversioniert (können später demselben
Schema folgen).

## Platzhalter (classify)

- `{category_list}` / `{category_guide}` — aus `vault_config.yaml` (E4-3)
- `{existing_notes}` — vorgefilterter Vault-Kontext (E5-2)
- `{input}` — Nutzertext
