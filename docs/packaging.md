# Packaging & Consumer-Installation (E20)

Vereinfachtes Setup für die **Heim-Box** (Mac Mini, Mini-PC, Always-on-Rechner)
— ohne ngrok, ohne Webhook-Tunnel. Telegram läuft per **Long-Polling**; Keys
trägst du im **Setup-Wizard** ein (`http://localhost:8000/setup`).

> **Vertrauen:** Der Installer fragt **keine Secrets ab** und sendet nichts ins
> Internet. Alles bleibt lokal in `.env` und deinem Vault.

---

## Voraussetzung

| Plattform | Docker |
|-----------|--------|
| macOS | [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) |
| Windows | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) |
| Linux | [Docker Engine + Compose](https://docs.docker.com/engine/install/) |

Obsidian ist **optional** — jeder Markdown-Ordner reicht als Vault.

---

## Schnellstart (Consumer)

### macOS / Linux

```bash
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
chmod +x scripts/install.sh scripts/doctor.sh
./scripts/install.sh
```

Der Installer:

1. legt `./vault` an (oder `VAULT_DIR=…` setzen)
2. erstellt `.env` aus `.env.example` (Vault-Pfad wird gesetzt)
3. startet Docker Compose im **Consumer-Modus** (`docker-compose.consumer.yml` + Long-Polling)
4. führt Alembic-Migrationen aus
5. öffnet den Setup-Wizard im Browser

### Windows (PowerShell)

```powershell
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
.\scripts\install.ps1
```

Optional: `$env:VAULT_DIR = "C:\Users\Du\SeitonBrain\vault"`

---

## Diagnose

```bash
./scripts/doctor.sh          # macOS / Linux
.\scripts\doctor.ps1         # Windows
```

Prüft Docker, `.env`, Vault-Pfad, laufende Services und `/health`.

---

## Was der Consumer-Modus anders macht

| Aspekt | Entwickler-Setup | Consumer (E20-1) |
|--------|------------------|------------------|
| Telegram | Webhook + Tunnel | Long-Polling (`--profile polling`) |
| Restart | manuell | `unless-stopped` (Consumer-Compose) |
| Keys | `.env` manuell | Setup-Wizard `/setup` |
| Vault | eigener Obsidian-Pfad | Default `./vault` |

Compose-Befehl manuell:

```bash
docker compose -f docker-compose.yml -f docker-compose.consumer.yml --profile polling up -d
```

---

## Backup

```bash
./scripts/backup.sh
```

Siehe [`docs/setup.md`](setup.md#backups-lokal).

---

## Später (E20-4+)

- **E20-4:** Auto-Update-Mechanismus
- **E20-3/5:** Native Desktop-App / Code-Signing — kein Nahziel (Web-UI reicht, ADR 0004)

---

## VPS (Dauerbetrieb)

Server mit öffentlicher Domain und Telegram-Webhook: [`docs/vps-deployment.md`](vps-deployment.md) (E20-2).

```bash
./scripts/deploy-vps.sh
PUBLIC_URL=https://deine-domain.tld ./scripts/register-telegram-webhook.sh
```

Power-User und Entwickler: vollständige Anleitung in [`docs/setup.md`](setup.md).
