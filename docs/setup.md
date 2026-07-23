# Setup

Lokale Entwicklung und Self-Hosting für Seiton Brain.

**Consumer / Heim-Box (einfach):** [`docs/packaging.md`](packaging.md) — `./scripts/install.sh`

**VPS / Dauerbetrieb:** [`docs/vps-deployment.md`](vps-deployment.md) — `./scripts/deploy-vps.sh`

---

## Voraussetzungen

- Docker + Docker Compose
- Telegram-Account
- OpenAI-API-Key ([platform.openai.com](https://platform.openai.com))
  — oder lokal [Ollama](https://ollama.com) (`LLM_PROVIDER=ollama`, siehe
  [`docs/llm-providers.md`](llm-providers.md))
- Obsidian-Vault auf dem Host (oder leeres Verzeichnis als Start)
- Für lokales Telegram-Testing: [ngrok](https://ngrok.com) (kostenlos) oder [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (stabile URL)

---

## 1. Repository klonen

```bash
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
chmod +x scripts/*.sh
./scripts/init.sh    # oder: make init — .env + Vault, keine Secrets
```

---

## 2. Telegram-Bot anlegen

1. In Telegram `@BotFather` öffnen → `/newbot`
2. Namen und Username vergeben → BotFather liefert **Bot-Token** (Format `123456:ABC-…`)
3. Webhook-Secret selbst generieren — beliebige zufällige Zeichenkette:
   ```bash
   openssl rand -hex 32
   ```

---

## 3. `.env` anlegen

Falls noch nicht durch `./scripts/init.sh` / `make init`:

```bash
cp .env.example .env
```

Werte ausfüllen:

```bash
TELEGRAM_BOT_TOKEN=123456:DEIN-TOKEN
TELEGRAM_WEBHOOK_SECRET=das-secret-aus-schritt-2

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

OBSIDIAN_VAULT_HOST_PATH=/Users/<du>/Obsidian/SeitonBrain
OBSIDIAN_VAULT_PATH=/vault
```

> Wenn du noch keinen Vault hast: ein leeres Verzeichnis reicht. Optional `vault.example/` als Vorlage — siehe [`vault.md`](vault.md).

---

## 4. Stack starten

```bash
docker compose up --build
```

Es starten:
- `api` auf [http://localhost:8000](http://localhost:8000)
- `worker` (Celery)
- `db` (Postgres 16)
- `redis` (7-alpine)

Healthcheck testen:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 5. Alembic-Migrationen ausführen

Beim ersten Start oder nach DB-Änderungen:

```bash
docker compose run --rm api alembic upgrade head
```

---

## 6. Webhook bei Telegram registrieren

### Variante A — Lokal mit ngrok (für Entwicklung)

In einem zweiten Terminal:

```bash
ngrok http 8000
```

ngrok zeigt eine `https://xxxxx.ngrok-free.app`-URL. Diese setzen:

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://xxxxx.ngrok-free.app/webhook" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"
```

> **Achtung**: ngrok-Free-URLs ändern sich bei jedem Neustart → `setWebhook` jedes Mal neu aufrufen.

### Variante B — Cloudflare Tunnel (für 24/7-Self-Hosting)

```bash
cloudflared tunnel create seiton-brain
cloudflared tunnel route dns seiton-brain seiton-brain.<deine-domain>
cloudflared tunnel run --url http://localhost:8000 seiton-brain
```

Dann:

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://seiton-brain.<deine-domain>/webhook" \
  -d "secret_token=${TELEGRAM_WEBHOOK_SECRET}"
```

Vorteil: Die URL bleibt stabil.

### Variante C — Long-Polling (kein Webhook, keine öffentliche URL) (E1-5)

Statt einen Webhook zu registrieren, kann ein eigener Prozess Telegram aktiv
per `getUpdates` abfragen. Ideal für lokales Self-Hosting auf einer
Always-on-Box (Mini-PC / Mac Mini / Heimserver): kein Tunnel, kein
`setWebhook`, kein TLS-Zertifikat nötig.

```bash
docker compose --profile polling up --build
```

Das startet zusätzlich den `poller`-Service (`python -m app.telegram.polling`).
Webhook und Polling schließen sich aus — der Poller ruft beim Start
`deleteWebhook` auf. Long-Poll-Fenster über `TELEGRAM_POLLING_TIMEOUT`
(Default 25 s) konfigurierbar.

Lokal ohne Docker:

```bash
python -m app.telegram.polling
```

---

## 7. Erste Nachricht testen

In Telegram dem Bot schreiben:

> Idee: ein Tool, das mir Telegram-Nachrichten in meinen Obsidian-Vault legt.

Erwartung:
1. Bot antwortet sofort: „Wird verarbeitet…"
2. Nach ~2–5 s: „Gespeichert als [[…]] unter Ideas"
3. Im Vault: neue Datei unter `Ideas/`

Bei Voice: Sprachnachricht senden → „Sprachnachricht wird verarbeitet…" → Bestätigung.

Optional in `.env`: `WHISPER_LANGUAGE=de` (ISO-639-1) für schnellere/stabilere
Transkription auf Deutsch — leer lassen = Auto-Detect (E6-3).

---

## Tests lokal ausführen

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
ruff check app tests
```

Tests laufen offline — keine echten API-/DB-Calls.

---

## Troubleshooting

Ausführliche Anleitung: **[`docs/troubleshooting.md`](troubleshooting.md)** (E12-3).

Schnellreferenz:

| Problem | Lösung |
|---------|--------|
| Erste Diagnose | `./scripts/doctor.sh` (Mac/Linux) bzw. `.\scripts\doctor.ps1` (Windows) |
| Bot antwortet nicht (Webhook) | `getWebhookInfo` checken: `curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo` |
| Bot antwortet nicht (Consumer) | Poller läuft? `docker compose ps` → Service `poller` |
| `401 Unauthorized` im Webhook | `secret_token` in `setWebhook` und `.env` stimmen nicht überein |
| `api` startet nicht | `docker compose logs api` — meist fehlende Env-Variable |
| Migrationen schlagen fehl | `docker compose run --rm api alembic upgrade head`; bei kaputter DB: `docker compose down -v` (löscht Daten!) |
| ngrok-URL nach Neustart tot | Webhook neu setzen (neue URL) — siehe [`troubleshooting.md`](troubleshooting.md#telegram) |
| Datei landet nicht im Vault | `OBSIDIAN_VAULT_HOST_PATH` prüfen, muss absoluter Host-Pfad sein |
| `Permission denied` beim Vault-Schreiben | Container läuft als UID 1000 — Vault-Ordner auf dem Host beschreibbar |
| ngrok-URL wechselt ständig | Cloudflare Tunnel verwenden (Variante B) |
| `worker` hängt bei OpenAI | Outage/Quota → `docker compose logs worker` |
| Fehler nur im Log, keine Admin-DM | `TELEGRAM_ADMIN_CHAT_ID` in `.env` setzen (eigene ID via @userinfobot) |

---

## Backups (lokal)

Mit dem Backup-Skript sicherst du Postgres und den Obsidian-Vault in einem
Zeitstempel-Ordner unter `backups/` (gitignored):

```bash
docker compose up -d          # db muss laufen
./scripts/backup.sh
# oder: ./scripts/backup.sh /pfad/zu/backups
```

Pro Lauf entsteht z. B. `backups/seiton-20260608-143000/` mit:

| Datei | Inhalt |
|-------|--------|
| `postgres.sql` | `pg_dump` der Datenbank `seitonbrain` |
| `vault.tar.gz` | Archiv von `OBSIDIAN_VAULT_HOST_PATH` |
| `manifest.txt` | Metadaten (Zeitstempel, Pfade) |

**Wiederherstellen** (manuell, Stack muss laufen):

```bash
# Datenbank (Vorsicht: überschreibt bestehende Daten)
docker compose exec -T db psql -U user -d seitonbrain < backups/seiton-.../postgres.sql

# Vault (Vorsicht: entpackt über den bestehenden Ordner)
tar -xzf backups/seiton-.../vault.tar.gz -C "$(dirname "$OBSIDIAN_VAULT_HOST_PATH")"
```

Empfehlung: Backups regelmäßig auf externes Laufzeug oder Cloud-Sync kopieren
(`backups/` liegt nur lokal im Projektverzeichnis).

---

## Outbound Webhooks (n8n & Co.)

Optional: Seiton sendet nach erfolgreichem Speichern oder bei dauerhaft
fehlgeschlagener Verarbeitung ein JSON-Event per HTTP POST an eine URL:

```env
SEITON_WEBHOOK_URL=https://n8n.example/webhook/seiton-events
```

| Event | Wann |
|-------|------|
| `note.created` | Neue Notiz im Vault angelegt |
| `note.appended` | Bestehende Notiz ergänzt |
| `note.indexed` | Embedding berechnet — semantische Suche/RAG bereit (`EMBEDDINGS_ENABLED`) |
| `entry.failed` | Worker-Task endgültig fehlgeschlagen (nach allen Retries) |

Der Event-Typ steht im JSON-Feld `event` und im Header `X-Seiton-Event`.
Fehler beim Webhook-Versand werden nur geloggt — Capture/Telegram laufen
weiter.

**n8n:** Webhook-Trigger-Node → Switch auf `$json.event` → z. B. Slack,
Kalender, Mail. Details: [`docs/integrations/n8n.md`](./integrations/n8n.md).

---

## Semantische Suche aktivieren (E17-2, optional)

Standardmäßig läuft nur die Keyword-Suche. Für semantische Suche (pgvector):

1. In `.env` setzen:

```bash
EMBEDDINGS_ENABLED=true
EMBEDDING_MODEL=text-embedding-3-small   # 1536 Dimensionen (muss zur DB-Spalte passen)
```

2. Das `db`-Image ist bereits `pgvector/pgvector:pg16`; die Migration legt die
   `vector`-Extension automatisch an (`docker compose run --rm api alembic upgrade head`).
3. Neu erfasste Notizen werden ab sofort embedded. **Bestandsnotizen** einmalig
   nachrüsten (Backfill) per Vault-Sync.

> Embeddings verursachen zusätzliche Embedding-API-Calls (Kosten über deinen
> eigenen OpenAI-Key). Schlägt ein Call fehl, bleibt die Keyword-Suche aktiv.

---

## Saubere Neuinstallation

```bash
docker compose down -v   # entfernt auch DB-Volume!
rm -rf <dein-vault>      # nur wenn du den Vault wirklich löschen willst
docker compose up --build
```

---

## Setup-Wizard (E19-1)

Nach `docker compose up -d` im Browser öffnen:

```
http://localhost:8000/setup
```

Nur von **localhost** erreichbar. Der Wizard hilft bei Vault-Pfad, OpenAI-Key und
optional Telegram; Keys landen ausschließlich in deiner lokalen `.env`. Nach dem
Speichern Container neu starten: `docker compose up -d`.

**Dashboard:** http://localhost:8000/dashboard — letzte Entries, Vault-Aktivität,
Statistik (E19-2).

**Suchen & Fragen:** http://localhost:8000/ask — Vault-Suche und RAG-Chat
(E19-3).

**Notizen verwalten:** http://localhost:8000/notes — öffnen, bearbeiten, löschen
(E19-4).

**Einstellungen:** http://localhost:8000/settings — Keys, Provider, Backup, Edition
(E19-5).

---

## Geplantes Setup (CLI — Phase D)

Vorhanden: **`./scripts/init.sh`** / **`make init`** (E16-1), **`./scripts/doctor.sh`** (E16-2),
**Setup-Wizard** `/setup` (E19-1 / E16-4).
API-Keys werden **nur lokal** in `.env` geschrieben — nie an externe Server gesendet.

Details: [`docs/integrations/setup-onboarding.md`](./integrations/setup-onboarding.md)

Weitere Integrations-Ideen (n8n, Vault-Backends): [`docs/integrations/`](./integrations/)
