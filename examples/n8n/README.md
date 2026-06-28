# n8n Beispiel-Workflows (E14-1)

Importierbare Workflows für [n8n](https://n8n.io/) — Seiton Brain als Engine,
n8n als Integrationsschicht. Architektur: [ADR 0003](../../docs/adr/0003-engine-and-adapters.md).

## Voraussetzungen

1. Seiton Brain läuft (`docker compose up -d`), Migrationen applied
2. In `.env` gesetzt:
   - `SEITON_API_KEY` — für Workflows mit HTTP Request
   - `SEITON_WEBHOOK_URL` — nur für Workflow **02** (siehe unten)
3. n8n erreichbar (lokal oder Docker)

**Base-URL:** In den Workflows steht `http://host.docker.internal:8000` — passt,
wenn n8n in Docker läuft und Seiton auf dem Host (Port 8000). Sonst anpassen:

| Setup | URL |
|-------|-----|
| n8n + Seiton beide Docker Compose (gleiches Netz) | `http://api:8000` |
| n8n Docker, Seiton auf Host | `http://host.docker.internal:8000` |
| Beides lokal ohne Docker | `http://localhost:8000` |

## Import

1. n8n → **Workflows** → **Import from File**
2. JSON aus diesem Ordner wählen
3. Platzhalter `REPLACE_WITH_SEITON_API_KEY` im HTTP-Request-Node durch deinen Key ersetzen
4. Workflow aktivieren (nur Webhook/Todoist-Trigger)

Details: [`docs/integrations/n8n.md`](../../docs/integrations/n8n.md)

---

## 01 — Capture via API

**Datei:** `01-capture-via-api.json`

Manueller Test: Beispiel-Text → `POST /v1/capture` → Antwort mit Klassifikation.

```
[Manual Trigger] → [Beispiel-Text] → [Seiton Capture]
```

**Test:** „Execute Workflow“ klicken — in Obsidian sollte eine neue Notiz erscheinen.

---

## 02 — Seiton Webhook Events

**Datei:** `02-seiton-webhook-events.json`

Seiton sendet Events an n8n (Stufe 2 der Integration).

**Setup:**

1. Workflow importieren und **aktivieren**
2. Im Webhook-Node die **Production URL** kopieren (z. B. `https://n8n.example/webhook/seiton-events`)
3. In Seiton `.env`: `SEITON_WEBHOOK_URL=<diese URL>`
4. Seiton-Stack neu starten (`docker compose up -d`)

```
[Seiton Webhook] → [Event Router] → note.created / note.appended / entry.failed / note.indexed
```

Jeder Ausgang landet in einem **Set**-Node mit einer Kurzinfo — dort Slack, E-Mail
oder Kalender anschließen.

**Test:** Telegram-Nachricht an den Bot → n8n Execution sollte `note.created` zeigen.
Mit `EMBEDDINGS_ENABLED=true` folgt kurz danach `note.indexed` (semantische
Suche bereit).

---

## 04 — Knowledge Backend (nach `note.indexed`)

**Datei:** `04-knowledge-backend-on-indexed.json`

Simuliert ein `note.indexed`-Event und ruft `GET /v1/notes/search?semantic=true`
auf — Muster für „Brain als Wissensquelle" in n8n.

```
[Manual Trigger] → [Simuliert note.indexed] → [Semantische Suche] → [Ergebnis]
```

**Live-Anbindung:** Ausgang **Indexed — Retrieval hier** in Workflow **02** an
diesen HTTP-Request (oder `POST /v1/ask`) anschließen. Details:
[`docs/integrations/knowledge-retrieval.md`](../../docs/integrations/knowledge-retrieval.md)
(Abschnitt „Brain als Knowledge-Backend").

**Voraussetzung:** `EMBEDDINGS_ENABLED=true`, Vault-Sync/Backfill gelaufen.

---

## 03 — Todoist → Seiton

**Datei:** `03-todoist-to-capture.json`

Neue Todoist-Aufgabe → Text an Seiton Capture.

```
[Todoist New Task] → [Seiton Capture]
```

**Setup:** Todoist-Credentials in n8n verbinden (OAuth). Optional: im Todoist-Trigger
ein Projekt filtern.

**Hinweis:** Aufgaben-Inhalt (`content` + `description`) wird als Capture-Text gesendet;
Seiton klassifiziert und legt die Notiz im Vault ab.

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `401` / `503` von Seiton | `SEITON_API_KEY` prüfen, Header `X-Seiton-Api-Key` im Node |
| Connection refused | Base-URL / Docker-Netzwerk (siehe Tabelle oben) |
| Webhook kommt nicht an | Workflow aktiv? Production-URL in `SEITON_WEBHOOK_URL`? |
| Todoist triggert nicht | Credentials + Workflow aktiv |
