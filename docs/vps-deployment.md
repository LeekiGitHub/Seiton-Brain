# VPS-Deployment (E20-2)

Dauerbetrieb auf einem **Linux-VPS** (IONOS, Hetzner, DigitalOcean, …) mit
**Telegram-Webhook** und **HTTPS** — ohne Long-Polling.

> **Heim-Box ohne öffentliche URL?** → [`docs/packaging.md`](packaging.md) (E20-1)

---

## Übersicht

| Schritt | Was |
|---------|-----|
| 1 | VPS + Docker |
| 2 | `./scripts/deploy-vps.sh` |
| 3 | Setup-Wizard per SSH-Tunnel |
| 4 | Caddy (TLS) vor die API |
| 5 | `./scripts/register-telegram-webhook.sh` |

Die API lauscht nur auf **127.0.0.1:8000**. Telegram und Browser erreichen sie
über einen Reverse-Proxy mit gültigem TLS-Zertifikat.

---

## Voraussetzungen

- Linux-VPS (Ubuntu 22.04+ empfohlen), root oder sudo
- [Docker Engine + Compose](https://docs.docker.com/engine/install/)
- Eigene Domain (DNS **A-Record** → VPS-IP)
- Telegram-Bot (@BotFather) und OpenAI-Key (später im Setup-Wizard)

Firewall: Port **443** (HTTPS) und **22** (SSH) öffnen. Port 8000 **nicht**
öffentlich freigeben — nur localhost.

---

## 1. Repository auf dem VPS

```bash
sudo mkdir -p /opt/seiton-brain
sudo chown "$USER":"$USER" /opt/seiton-brain
git clone https://github.com/LeekiGitHub/Seiton-Brain.git /opt/seiton-brain
cd /opt/seiton-brain
chmod +x scripts/*.sh
```

---

## 2. Stack deployen

```bash
./scripts/deploy-vps.sh
```

Optional anderer Vault-Pfad:

```bash
VAULT_DIR=/var/lib/seiton-brain/vault ./scripts/deploy-vps.sh
```

Das Skript:

- legt Vault + `.env` an (`SEITON_DEPLOY_MODE=vps`)
- startet `docker-compose.vps.yml` (Restart-Policies, **kein** Poller)
- führt Alembic-Migrationen aus

---

## 3. Setup-Wizard (Keys eintragen)

Die Web-UI (`/setup`) ist **nur localhost** erreichbar — per SSH-Tunnel von
deinem Rechner:

```bash
ssh -L 8000:127.0.0.1:8000 user@DEINE-VPS-IP
```

Im Browser: **http://localhost:8000/setup** — Vault-Pfad, OpenAI-Key,
Telegram-Token + Webhook-Secret eintragen und speichern. Danach:

```bash
docker compose -f docker-compose.yml -f docker-compose.vps.yml up -d
```

---

## 4. TLS mit Caddy

```bash
sudo apt install -y caddy    # oder siehe caddyserver.com/docs/install
sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
# Domain in Caddyfile anpassen: brain.deine-domain.tld
sudo systemctl reload caddy
```

Caddy holt automatisch ein Let's-Encrypt-Zertifikat.

Test:

```bash
curl -sf https://brain.deine-domain.tld/health
```

---

## 5. Telegram-Webhook

```bash
PUBLIC_URL=https://brain.deine-domain.tld ./scripts/register-telegram-webhook.sh
```

Prüfen:

```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

Testnachricht an den Bot senden → „Wird verarbeitet…".

---

## Diagnose & Betrieb

```bash
./scripts/doctor.sh              # erkennt VPS-Modus via SEITON_DEPLOY_MODE
./scripts/backup.sh              # Postgres + Vault
./scripts/update.sh              # Auto-Update (E20-4)
docker compose -f docker-compose.yml -f docker-compose.vps.yml logs -f api worker
```

### Updates (E20-4)

```bash
./scripts/update.sh --check
./scripts/update.sh
```

Optional systemd-Timer: `deploy/seiton-update.{service,timer}` — siehe [`docs/packaging.md`](packaging.md).

---

## IONOS / typische VPS-Anbieter

1. VPS bestellen (Ubuntu, min. 2 GB RAM empfohlen)
2. SSH-Zugang notieren, optional Floating IP
3. Domain bei IONOS: DNS A-Record auf VPS-IP
4. Schritte 1–5 oben

Kein anbieter-spezifisches SDK nötig — reines Docker + Caddy.

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Bot antwortet nicht | `getWebhookInfo`, Caddy-Logs, `docker compose logs api` |
| 502 von Caddy | API läuft? `curl http://127.0.0.1:8000/health` |
| Setup-UI nicht erreichbar | SSH-Tunnel `-L 8000:127.0.0.1:8000` |
| Poller + Webhook Konflikt | VPS-Modus startet **keinen** Poller — `doctor.sh` prüft das |

Weitere Details: [`docs/setup.md`](setup.md).
