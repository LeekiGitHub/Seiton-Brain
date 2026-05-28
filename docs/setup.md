# Setup

Lokale Entwicklung und Self-Hosting für Seiton Brain.

---

## Voraussetzungen

- Docker + Docker Compose
- Telegram-Account
- OpenAI-API-Key ([platform.openai.com](https://platform.openai.com))
- Obsidian-Vault auf dem Host (oder leeres Verzeichnis als Start)
- Für lokales Telegram-Testing: [ngrok](https://ngrok.com) (kostenlos) oder [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) (stabile URL)

---

## 1. Repository klonen

```bash
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
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

> Wenn du noch keinen Vault hast: ein leeres Verzeichnis reicht. Optional `vault.example/` als Vorlage rüberkopieren.

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

---

## 7. Erste Nachricht testen

In Telegram dem Bot schreiben:

> Idee: ein Tool, das mir Telegram-Nachrichten in meinen Obsidian-Vault legt.

Erwartung:
1. Bot antwortet sofort: „Wird verarbeitet…"
2. Nach ~2–5 s: „Gespeichert als [[…]] unter Ideas"
3. Im Vault: neue Datei unter `Ideas/`

Bei Voice: Sprachnachricht senden → „Sprachnachricht wird verarbeitet…" → Bestätigung.

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

| Problem | Lösung |
|---------|--------|
| Bot antwortet nicht | `getWebhookInfo` checken: `curl https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo` |
| `401 Unauthorized` im Webhook | `secret_token` in `setWebhook` und `.env` stimmen nicht überein |
| `api` startet nicht | `docker compose logs api` — meist fehlt eine Env-Variable |
| Migrationen schlagen fehl | `docker compose down -v` (löscht DB-Volume!) und neu starten |
| Datei landet nicht im Vault | `OBSIDIAN_VAULT_HOST_PATH` prüfen, muss absoluter Host-Pfad sein |
| ngrok-URL wechselt ständig | Cloudflare Tunnel verwenden (Variante B) |
| `worker` hängt bei OpenAI | Outage/Quota → `docker compose logs worker` zeigt Stacktrace |

---

## Saubere Neuinstallation

```bash
docker compose down -v   # entfernt auch DB-Volume!
rm -rf <dein-vault>      # nur wenn du den Vault wirklich löschen willst
docker compose up --build
```
