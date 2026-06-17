# n8n-Integration

Wie Seiton Brain mit [n8n](https://n8n.io/) zusammenspielen kann — ohne den
Python-Core zu verkomplizieren.

> **Architektur:** Seiton = Engine, n8n = Integrationsschicht. Celery bleibt
> interner Worker. Siehe [ADR 0003](../adr/0003-engine-and-adapters.md).

---

## Drei Stufen (empfohlene Reihenfolge)

### Stufe 1 — HTTP Request (Phase C/D)

Sobald **REST-API v1** existiert (`E13-1`), reicht der Standard-**HTTP Request**
-Node in n8n. **Kein Custom Node nötig.**

Beispiel-Operationen (geplant):

| Operation | Methode | Endpoint (Entwurf) |
|-----------|---------|-------------------|
| Text erfassen + klassifizieren | `POST` | `/v1/capture` |
| Nur klassifizieren (ohne Speichern) | `POST` | `/v1/classify` |
| Letzte Entries | `GET` | `/v1/entries?limit=10` |
| Notiz suchen | `GET` | `/v1/notes/search?q=...` |
| An bestehende Notiz anhängen | `POST` | `/v1/notes/{id}/append` |

Auth: API-Key im Header (z. B. `X-Seiton-Api-Key`), konfiguriert in `.env`
(`SEITON_API_KEY`). Nur lokaler Self-Host — kein Cloud-Dienst von uns.

**Deliverable Phase D:** Ordner `examples/n8n/` mit exportierten Workflow-JSONs
(`E14-1`) — 🟢 siehe [`examples/n8n/`](../../examples/n8n/README.md).

### Stufe 2 — Webhooks / Events (Phase E) 🟢

Seiton sendet nach erfolgreichem Speichern Events an `SEITON_WEBHOOK_URL`:

| Event | Wann | n8n-Nutzung |
|-------|------|-------------|
| `note.created` | Neue `.md` angelegt | Slack, Mail, Kalender, … |
| `note.appended` | Bestehende Notiz ergänzt | Review-Workflows |
| `entry.failed` | Verarbeitung endgültig fehlgeschlagen | Alert an Admin |

n8n-Workflow startet per **Webhook**-Trigger-Node; Event per `$json.event`
oder Header `X-Seiton-Event` filtern.

**Story:** `E13-3` in ROADMAP.

### Stufe 3 — Custom Community Node (Phase E, separates Repo)

Eigenes npm-Paket, z. B. `n8n-nodes-seiton-brain` (eigenes GitHub-Repo), das die
HTTP-API wrappt:

- Credentials: Base URL + API Key
- Nodes: Capture Text, Capture Voice, Search Notes, Append, Get Entry
- Release unabhängig vom Python-Repo (npm-Versionierung, n8n Community Guidelines)

**Story:** `E14-2` in ROADMAP.

**Bewusst nicht:** Custom Node ins Python-Repo mischen (andere Toolchain, CI,
Review-Prozess bei n8n).

---

## Was n8n **nicht** ersetzen soll

| Bereich | Bleibt in Seiton | Grund |
|---------|------------------|-------|
| Idempotenz (`telegram_update_id`) | ✅ | DB-Unique, Webhook-Retries |
| Celery Worker + Retries | ✅ | Zuverlässigkeit, Backoff |
| Vault-Schreiben + Kollisionen | ✅ | Source of Truth auf Disk |
| LLM-Output-Validierung (Pydantic) | ✅ | Einheitliches Schema |

n8n eignet sich für **alles danach** und **alles drumherum**: andere Inputs
(Todoist, E-Mail), Multi-Tool-Ketten, Benachrichtigungen, optionale Multi-LLM-
Graphen *außerhalb* des Cores.

---

## Beispiel-Szenarien

### A — Seiton als „Brain“-Schritt in n8n

```
Todoist (neue Aufgabe) → n8n Filter → POST /v1/capture → Slack „Neue Idee: [[Titel]]“
```

### B — Seiton triggert n8n

```
Telegram → Seiton → note.created Webhook → n8n → Google Calendar / Reminder
```

### C — Hybrid (Alltag + Review)

- **Schnell erfassen:** Weiterhin Telegram → Seiton (Default-Adapter)
- **Wöchentlich:** n8n-Workflow ruft `/v1/entries`, LLM in n8n fasst zusammen,
  optional manueller Approve-Step

### D — Multi-LLM in n8n statt im Python-Core

```
Input → OpenAI (Klassifikation) → Ollama lokal (Tags) → POST /v1/capture
```

Sinnvoll auf Mac Mini mit Ollama — Seiton speichert nur das finale Ergebnis.

---

## Abhängigkeiten (Reihenfolge)

1. Phase B: Append-Logik (`E3-2`, `E4-1`) — sonst ist „Brain“ noch zu dünn
2. Phase C: REST-API v1 + API-Key-Auth (`E13-1`, `E13-2`) 🟢
3. Phase D: Beispiel-Workflows (`E14-1`) 🟢
4. Phase E: Outbound Webhooks (`E13-3`) 🟢, Custom Node (`E14-2`)

---

## Offene Fragen (für spätere ADRs)

- Soll `/v1/capture` synchron antworten (klassifiziertes JSON) oder async
  (202 + Job-ID wie Telegram)?
- Rate-Limiting pro API-Key?
- n8n-Node: eine Operation pro Node vs. „Resource + Operation“-Pattern?
