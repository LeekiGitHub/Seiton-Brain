# Troubleshooting (E12-3)

Häufige Probleme beim Self-Hosting und in der Entwicklung — nach Modus
gruppiert. **Erster Schritt:** Diagnose-Skript ausführen:

```bash
./scripts/doctor.sh          # macOS / Linux
.\scripts\doctor.ps1         # Windows
```

Weitere Doku: [`self-hosting.md`](self-hosting.md) · [`setup.md`](setup.md) ·
[`packaging.md`](packaging.md) · [`vps-deployment.md`](vps-deployment.md)

---

## Diagnose (Doctor)

| Symptom | Prüfen |
|---------|--------|
| „Alles ok“, aber Bot tot | Doctor prüft Container, nicht OpenAI-Quota — Logs siehe unten |
| Harte Fehler bei `.env` / Vault | Pfad in `.env` korrigieren, `./scripts/install.sh` oder Setup-Wizard |
| VPS: Webhook-Warnung | `./scripts/register-telegram-webhook.sh` mit `PUBLIC_URL=…` |
| Consumer: Poller fehlt | `docker compose -f docker-compose.yml -f docker-compose.consumer.yml --profile polling up -d` |

---

## Docker & Services

| Problem | Lösung |
|---------|--------|
| `Docker-Daemon läuft nicht` | Docker Desktop starten (Mac/Win) oder `sudo systemctl start docker` (Linux) |
| `api` / `worker` startet nicht | `docker compose logs api` — oft fehlende Env-Variable; Vergleich mit `.env.example` |
| `/health` → 503 | DB oder Redis nicht healthy: `docker compose ps`, `docker compose logs db redis` |
| Port 8000 belegt | Anderen Prozess beenden oder Port in Compose ändern |
| Container-Neustart nach `.env`-Änderung | `docker compose up -d` (Settings-Wizard weist darauf hin) |

**Logs:**

```bash
docker compose logs -f api
docker compose logs -f worker --tail 100
docker compose logs -f poller    # Consumer-Modus
```

---

## Telegram

### Webhook-Modus (Entwicklung / VPS)

| Problem | Lösung |
|---------|--------|
| Bot antwortet gar nicht | `curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"` — `url` gesetzt? |
| `401 Unauthorized` | `TELEGRAM_WEBHOOK_SECRET` muss mit `secret_token` bei `setWebhook` übereinstimmen |
| Webhook nach ngrok-Neustart tot | Neue URL setzen: `curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" -d "url=https://NEU.ngrok-free.app/webhook" -d "secret_token=${SECRET}"` |
| ngrok-URL wechselt ständig | [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) für stabile URL (siehe `setup.md`) |
| VPS: 502 hinter Proxy | API nur auf `127.0.0.1:8000` — Caddy/nginx auf HTTPS prüfen (`docs/vps-deployment.md`) |
| Poller + Webhook gleichzeitig | Konflikt — VPS ohne Poller; Consumer nur Poller |

### Long-Polling (Consumer / Heim-Box)

| Problem | Lösung |
|---------|--------|
| Keine Antworten | `docker compose ps` → Service `poller` muss laufen (`--profile polling`) |
| Poller startet nicht | Telegram-Token in `.env`? `docker compose logs poller` |
| „Wird verarbeitet…“, dann nichts | Worker-Logs: `docker compose logs worker` |

### Allgemein

| Problem | Lösung |
|---------|--------|
| Bot ignoriert mich | `TELEGRAM_ALLOWED_USER_IDS` gesetzt? Eigene ID via @userinfobot |
| Doppelte Bestätigungen | Selten — Idempotenz greift; Telegram-Retry ohne Duplikat-Reply ist normal |
| Admin-Fehler-DM fehlt | `TELEGRAM_ADMIN_CHAT_ID` setzen (E10-3) |

---

## Vault & Dateisystem

| Problem | Lösung |
|---------|--------|
| Datei landet nicht im Vault | `OBSIDIAN_VAULT_HOST_PATH` absoluter Host-Pfad; nach Änderung Container neu starten |
| `Permission denied` beim Schreiben | Container-User UID **1000** — Ordner auf Host beschreibbar machen: `chown -R 1000:1000 ./vault` |
| Mac/Win: Pfad nicht gemountet | Docker Desktop → File Sharing → Vault-Ordner erlauben |
| Windows-Pfad | `C:\Users\…` in `.env`; Backslashes oder Forward Slashes konsistent |
| Path-Traversal / 400 bei Notiz | Nur Pfade unterhalb des Vault-Roots (API/UI) |

---

## Datenbank & Migrationen

| Problem | Lösung |
|---------|--------|
| Migration schlägt fehl | `docker compose run --rm api alembic upgrade head` — Fehltext lesen |
| „relation does not exist“ | Migrationen nicht gelaufen — siehe oben |
| Frische DB gewünscht | **Datenverlust:** `docker compose down -v` dann neu starten |
| pgvector / Embedding-Fehler | `EMBEDDINGS_ENABLED=true` nur mit pgvector-Image (`pgvector/pgvector:pg16`) |

---

## OpenAI & Worker

| Problem | Lösung |
|---------|--------|
| Worker hängt / Timeout | OpenAI-Status, Quota, Key gültig — `docker compose logs worker` |
| Klassifikation schlägt fehl | JSON-Parsing — Retry in Logs; Prompt in `prompts/classify.txt` |
| Whisper-Fehler (Voice) | Dateigröße, API-Key, Netzwerk aus Container |
| Sprachnachricht zu groß | `TELEGRAM_VOICE_MAX_BYTES` (Default 10 MB, E6-1) — kürzer aufnehmen |
| Voice-Retry lädt erneut von Telegram | Cache prüfen: `TELEGRAM_VOICE_CACHE_DIR` / Docker-Volume `seiton-voice-cache` (E6-2) |
| Transkript oft falschsprachig | `WHISPER_LANGUAGE=de` (oder `en`) in `.env` setzen (E6-3) |
| Embeddings teuer / Fehler | `EMBEDDINGS_ENABLED=false` deaktiviert semantische Suche; Keyword bleibt |
| Celery-Task „failed“ endgültig | Nach Retries — ggf. `entry.failed`-Webhook; Admin-DM wenn konfiguriert |

---

## REST-API & OpenAPI

| Problem | Lösung |
|---------|--------|
| `/v1/*` → 503 | `SEITON_API_KEY` in `.env` setzen |
| `/v1/*` → 401 | Header `X-Seiton-Api-Key` muss exakt passen |
| `/docs` → 404 | API-Key setzen oder `SEITON_DEBUG=true`; nur **localhost** |
| `/docs` → 403 | Von externer IP — absichtlich blockiert; SSH-Tunnel auf VPS |

Lokal testen:

```bash
curl -H "X-Seiton-Api-Key: $SEITON_API_KEY" http://localhost:8000/v1/entries?limit=3
```

---

## Web-UI (localhost)

| Problem | Lösung |
|---------|--------|
| `/setup` → 403 | Nur von localhost — auf VPS: `ssh -L 8000:127.0.0.1:8000 user@vps` |
| Setup „unvollständig“ | OpenAI-Key + Vault-Pfad im Wizard; danach `docker compose up -d` |
| Settings speichern ohne Wirkung | Neustart erforderlich (Hinweis in UI) |
| Semantische Suche leer | `EMBEDDINGS_ENABLED=true` + Backfill / neue Notizen |

---

## Updates & Backups

| Problem | Lösung |
|---------|--------|
| Update schlägt fehl | `./scripts/update.sh --check`; Git-Konflikte manuell lösen |
| Nach Update Migration | `update.sh` führt Alembic aus — bei Fehler Logs des `api`-Containers |
| Backup leer | `./scripts/backup.sh` — `db` muss laufen |
| Restore | Siehe [`setup.md` — Backups](setup.md#backups-lokal) |

---

## Lizenz (kommerziell, E21)

| Problem | Lösung |
|---------|--------|
| Prozess startet nicht | `SEITON_LICENSE_REQUIRED=true` ohne gültigen Key — Key in Settings oder `.env` |
| Key abgelehnt | Format `SEITON1.…`; siehe [`licensing.md`](licensing.md) |

---

## Saubere Neuinstallation

**Achtung: löscht DB-Daten.**

```bash
docker compose down -v
# optional: Vault-Inhalt manuell sichern
docker compose up --build
docker compose run --rm api alembic upgrade head
```

Consumer: `./scripts/install.sh` · VPS: `./scripts/deploy-vps.sh`

---

## Immer noch hängen?

1. `./scripts/doctor.sh` Ausgabe + relevante Logs sammeln (ohne Secrets)
2. [GitHub Issue — Bug](https://github.com/LeekiGitHub/Seiton-Brain/issues/new?template=bug_report.yml) (keine Keys posten)
3. Sicherheitsprobleme: [`SECURITY.md`](../SECURITY.md)
