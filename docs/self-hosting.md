# Multi-Plattform Self-Hosting (E9-2)

Seiton Brain läuft **self-hosted** auf deiner Hardware — ohne dass wir Server
betreiben (ADR 0004). Diese Seite ist der **Einstieg**: welcher Weg passt zu
deiner Plattform, und welche Compose-Profile/Skripte du nutzt.

> **Entwickler-Setup** (Webhook, ngrok, eigener Vault): [`docs/setup.md`](setup.md)

---

## Welcher Weg passt?

| Situation | Plattform | Telegram | Anleitung |
|-----------|-----------|----------|-----------|
| Heim-Box, kein öffentlicher Zugang | macOS / Linux | Long-Polling | [`packaging.md`](packaging.md) → `install.sh` |
| Heim-Box unter Windows | Windows | Long-Polling | [`packaging.md`](packaging.md) → `install.ps1` |
| Linux-Desktop / Mini-PC | Linux | Long-Polling | wie macOS — `install.sh` |
| VPS mit Domain (IONOS, Hetzner, …) | Linux | Webhook + HTTPS | [`vps-deployment.md`](vps-deployment.md) |
| Lokale Entwicklung | beliebig | Webhook oder Polling | [`setup.md`](setup.md) |

**Faustregel:** Keine feste öffentliche URL → **Consumer** (Long-Polling).
Dauerbetrieb mit Domain → **VPS** (Webhook).

---

## Compose-Profile & Deploy-Modi

Alle Modi bauen auf `docker-compose.yml` auf. Zusatzdateien und Profile:

| Modus | `SEITON_DEPLOY_MODE` | Compose-Dateien | Profile | Telegram |
|-------|----------------------|-----------------|---------|----------|
| **Entwicklung** | — (unset) | `docker-compose.yml` | optional `polling` | Webhook *oder* Polling |
| **Consumer** | `consumer` | `+ docker-compose.consumer.yml` | `polling` | Long-Polling (Poller) |
| **VPS** | `vps` | `+ docker-compose.vps.yml` | — | Webhook |

Skripte setzen Modus und Compose automatisch:

| Skript | Modus | Plattform |
|--------|-------|-----------|
| `./scripts/install.sh` | consumer | macOS, Linux |
| `.\scripts\install.ps1` | consumer | Windows |
| `./scripts/deploy-vps.sh` | vps | Linux-VPS |
| `./scripts/doctor.sh` / `doctor.ps1` | erkennt aus `.env` | alle |
| `./scripts/update.sh` | erkennt aus `.env` | alle |

Manueller Consumer-Start:

```bash
docker compose -f docker-compose.yml -f docker-compose.consumer.yml --profile polling up -d
```

Manueller VPS-Start:

```bash
docker compose -f docker-compose.yml -f docker-compose.vps.yml up -d
```

---

## Plattform-Hinweise

### macOS

- [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) installieren und starten
- Vault unter deinem Home-Verzeichnis (`~/Obsidian/…` oder `./vault`) — in Docker Desktop **File Sharing** muss der Pfad erlaubt sein
- Nach dem Install: Setup-Wizard unter http://localhost:8000/setup
- Diagnose: `./scripts/doctor.sh`

### Windows

- [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) mit **WSL2-Backend**
- Vault am besten unter `C:\Users\<Du>\…` (nicht auf langsamen Netzlaufwerken)
- PowerShell im Repo: `.\scripts\install.ps1`
- Diagnose: `.\scripts\doctor.ps1`
- Pfade in `.env` als Windows-Pfad (`C:\…`); Docker mappt auf `/vault` im Container

### Linux (Desktop / Mini-PC)

- [Docker Engine + Compose Plugin](https://docs.docker.com/engine/install/)
- Nutzer in der `docker`-Gruppe oder `sudo` für Compose
- `./scripts/install.sh` — gleicher Ablauf wie macOS
- Optional: systemd-Timer für Updates — siehe [`packaging.md`](packaging.md#updates-e20-4)

### Linux-VPS

- Nur **Webhook-Modus** (kein Poller)
- API bindet auf `127.0.0.1:8000`; TLS über Caddy/nginx
- Vollständige Schritte: [`vps-deployment.md`](vps-deployment.md)

---

## Nach der Installation

1. **Setup-Wizard** — http://localhost:8000/setup (Keys, Vault, Telegram)
2. **Dashboard** — http://localhost:8000/dashboard
3. **Diagnose** — `doctor.sh` / `doctor.ps1`
4. **Backup** — `./scripts/backup.sh`
5. **Updates** — `./scripts/update.sh`

Web-UI ist absichtlich **nur localhost** erreichbar (Sicherheit). Auf dem VPS:
SSH-Tunnel `ssh -L 8000:127.0.0.1:8000 user@vps` für `/setup` und `/settings`.

---

## Häufige Probleme

| Symptom | Prüfen |
|---------|--------|
| `Docker-Daemon läuft nicht` | Docker Desktop / `systemctl start docker` |
| Vault nicht beschreibbar | Pfad existiert, Rechte, Docker File Sharing (Mac/Win) |
| Telegram antwortet nicht (Consumer) | Poller läuft? `docker compose … ps` → `poller` |
| Telegram antwortet nicht (VPS) | Webhook registriert? `./scripts/register-telegram-webhook.sh` |
| `/health` nicht erreichbar | `docker compose … ps`, Logs `docker compose … logs api` |
| Setup unvollständig | http://localhost:8000/setup — OpenAI-Key + Vault |

Mehr: [`troubleshooting.md`](troubleshooting.md) und `./scripts/doctor.sh`.

---

## Referenzen

- Consumer-Installer: [`packaging.md`](packaging.md) (E20-1)
- VPS: [`vps-deployment.md`](vps-deployment.md) (E20-2)
- Updates: [`packaging.md#updates`](packaging.md#updates-e20-4) (E20-4)
- Lizenz (kommerzielle Edition): [`licensing.md`](licensing.md) (E21)
- Architektur: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
