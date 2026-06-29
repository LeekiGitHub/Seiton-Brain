# n8n-Integration

> **Produkt-Status (ADR 0004):** Kein eigener **Custom n8n-Node** — Wartungslast
> ohne Consumer-Mehrwert. Die **REST-API (E13)** und **Outbound-Webhooks (E13-3,
> E17-7)** bleiben; Power-User binden n8n per Standard-HTTP-Request-Node an.
>
> **Beispiel-Workflows** unter [`examples/n8n/`](../../examples/n8n/README.md) werden
> weiter gepflegt (Power-User/Community-Referenz, kein Produktversprechen für
> Privatkunden). Siehe auch [ADR 0005](../adr/0005-repo-and-license-strategy.md).

Wie Seiton Brain mit [n8n](https://n8n.io/) zusammenspielen kann — ohne den
Python-Core zu verkomplizieren.

> **Architektur:** Seiton = Engine, n8n = optionale Integrationsschicht. Celery
> bleibt interner Worker. Siehe [ADR 0003](../adr/0003-engine-and-adapters.md).

---

## Drei Stufen (empfohlene Reihenfolge)

### Stufe 1 — HTTP Request (Phase C/D) 🟢

Sobald **REST-API v1** existiert (`E13-1`), reicht der Standard-**HTTP Request**
-Node in n8n. **Kein Custom Node nötig.**

| Operation | Methode | Endpoint |
|-----------|---------|----------|
| Text erfassen + klassifizieren | `POST` | `/v1/capture` |
| Nur klassifizieren (ohne Speichern) | `POST` | `/v1/classify` |
| Letzte Entries | `GET` | `/v1/entries?limit=10` |
| Notiz suchen | `GET` | `/v1/notes/search?q=...&semantic=true` |
| RAG-Antwort | `POST` | `/v1/ask` |
| Themen-Digest | `POST` | `/v1/digest` |

Auth: API-Key im Header (`X-Seiton-Api-Key`), konfiguriert in `.env`
(`SEITON_API_KEY`).

**Deliverable:** [`examples/n8n/`](../../examples/n8n/README.md) — importierbare
Workflow-JSONs (E14-1).

### Stufe 2 — Webhooks / Events (Phase E) 🟢

Seiton sendet Events an `SEITON_WEBHOOK_URL`:

| Event | Wann | n8n-Nutzung |
|-------|------|-------------|
| `note.created` | Neue `.md` angelegt | Slack, Mail, Kalender, … |
| `note.appended` | Bestehende Notiz ergänzt | Review-Workflows |
| `note.indexed` | Embedding berechnet (E17-7) | Retrieval-API, RAG, Knowledge-Backend |
| `entry.failed` | Verarbeitung endgültig fehlgeschlagen | Alert an Admin |

n8n-Workflow startet per **Webhook**-Trigger-Node; Event per `$json.event`
oder Header `X-Seiton-Event` filtern.

**Story:** `E13-3`, `E17-7`.

### Stufe 3 — Custom Community Node · ❌ entfällt (ADR 0004)

~~Eigenes npm-Paket `n8n-nodes-seiton-brain`~~ — **nicht geplant.** HTTP Request +
Beispiel-Workflows decken Power-User ab; ein Custom Node wäre zweites Repo +
npm-CI ohne Mehrwert für die Consumer-Zielgruppe.

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

### A — Seiton als „Brain"-Schritt in n8n

```
Todoist (neue Aufgabe) → n8n Filter → POST /v1/capture → Slack „Neue Idee: [[Titel]]"
```

### B — Seiton triggert n8n

```
Telegram → Seiton → note.created Webhook → n8n → Google Calendar / Reminder
```

### C — Wochenrückblick (Digest)

```
Cron (Sonntag) → POST /v1/digest { "topic": "Ideas", "days": 7 }
              → LLM-Synthese → Mail / Slack
```

### D — Multi-LLM in n8n statt im Python-Core

```
Input → OpenAI (Klassifikation) → Ollama lokal (Tags) → POST /v1/capture
```

---

## Abhängigkeiten (Reihenfolge)

1. Phase B: Append-Logik — sonst ist „Brain" noch zu dünn
2. Phase C: REST-API v1 + API-Key-Auth (`E13-1`, `E13-2`) 🟢
3. Phase D/E: Beispiel-Workflows (`E14-1`) 🟢, Outbound Webhooks (`E13-3`) 🟢
4. Phase F: Retrieval-API (`E17-5`), Digest (`E17-8`), MCP (`E17-6`) 🟢

---

## Offene Fragen (für spätere ADRs)

- Rate-Limiting pro API-Key?
- Soll `/v1/capture` synchron antworten oder async (202 + Job-ID)?
