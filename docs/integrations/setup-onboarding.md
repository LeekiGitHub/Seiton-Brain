# Setup & Onboarding (Public Self-Hosting)

Wie Seiton Brain für andere Nutzer **einfach einrichtbar** wird — ohne
Vertrauensprobleme bei API-Keys.

> **Grundregel:** Wir sehen die Keys des Users **nie**. Alles bleibt lokal auf
> seiner Maschine.

> ⚠️ **Produkt-Pivot (ADR 0004):** Für das kommerzielle Consumer-Produkt
> verschiebt sich das Onboarding von **CLI/TUI in einen UI-Setup-Wizard**
> (Epic E19-1). Die hier beschriebenen CLI-Stufen bleiben relevant für die
> **Server-/VPS-Edition** und Power-User; `seiton doctor` (E16-2) bleibt als
> Diagnose nützlich. `seiton init` (E16-3) und der UI-Wizard (E16-4/E19) sind
> parallele lokale Setup-Pfade — CLI für Power-User/VPS, Browser für Consumer.

---

## Was **nicht** tun

| Anti-Pattern | Problem |
|--------------|---------|
| `curl https://…/install.sh \| bash` mit interaktiver Key-Eingabe | Wirkt wie Key-Exfiltration; User vertrauen dem nicht |
| Keys an einen Setup-Server senden | Widerspricht Self-Hosting |
| Keys in Docker-Images oder Git | Sicherheitsdesaster |
| Setup-Skript, das `.env` aus dem Internet lädt | Supply-Chain-Risiko |

---

## Empfohlene Stufen

### Stufe 1 — Dokumentation (Phase D, heute teilweise da)

- [`docs/setup.md`](../setup.md): Bot-Token, Webhook, Vault mounten
- `.env.example` mit Kommentaren zu jedem Feld
- Klare README-Section: *„Copy `.env.example` → `.env`, trage Werte ein“*

**Stories:** `E12-1`, `E11-4`

### Stufe 2 — `scripts/init.sh` / `make init` (Phase D)

Idempotent, **keine Secrets abfragen**:

```bash
cp -n .env.example .env    # nur wenn .env fehlt
mkdir -p vault             # oder Hinweis auf OBSIDIAN_VAULT_HOST_PATH
docker compose pull
echo "Bearbeite jetzt .env und starte mit: docker compose up -d"
```

Optional: Prüfung ob Docker läuft.

**Story:** `E16-1` 🟢 — [`scripts/init.sh`](../../scripts/init.sh), `make init`

### Stufe 3 — `seiton doctor` (Phase D)

CLI-Kommando (Python-Entry-Point oder `./scripts/doctor.sh`):

| Check | Erfolg | Fehler-Hinweis |
|-------|--------|----------------|
| `.env` vorhanden | ✅ | „Kopiere .env.example“ |
| Pflichtfelder gesetzt | ✅ | Welches Feld fehlt (E8-2-Richtung) |
| Postgres erreichbar | ✅ | Connection-String / Compose |
| Redis erreichbar | ✅ | … |
| Vault-Pfad existiert + beschreibbar | ✅ | Mount-Hinweis |
| OpenAI (optional Ping) | ✅/⚠️ | Key ungültig / Netzwerk |
| Telegram Webhook (optional) | ✅/⚠️ | getWebhookInfo |

Exit-Code ≠ 0 bei harten Fehlern — gut für CI und Support.

**Story:** `E16-2`

### Stufe 4 — `seiton init` (Phase D/E) 🟢

Interaktiver Wizard (stdlib `input()`, kein Extra-UI-Paket):

```bash
./scripts/seiton init
# oder: python -m app.cli init
# CI/Skript: python -m app.cli init --non-interactive --vault ./vault --openai-api-key …
```

1. Vault-Pfad (Default: `./vault`)
2. OpenAI API Key
3. Telegram Bot Token (optional) + Webhook Secret / Allowlist
4. Seiton API Key (leer = generieren)
5. Embeddings an/aus
6. Schreibt **nur** lokale `.env`, legt Vault-Ordner an
7. Zeigt: `install.sh` / `doctor.sh` / UI-Setup

**Wichtig:** Läuft **lokal**, kein Netzwerk-Upload.

**Story:** `E16-3` — `app/cli/`, `scripts/seiton`

### Stufe 5 — Browser-Setup auf localhost (Phase E, optional)

Erster Start ohne `.env`: `http://localhost:8000/setup` (nur localhost-Bind,
einmalig, danach deaktiviert). Alternative zur TUI für weniger CLI-affine User.

**Story:** `E16-4` (Backlog, niedrige Priorität)

### Stufe 6 — OS-Keystore (Phase E) 🟢

At-Rest-Schutz statt Klartext-`.env`: `seiton init --keyring` legt Keys via
[`keyring`](https://pypi.org/project/keyring/) ab; Start mit
`./scripts/seiton-up.sh`. Details: [`docs/keyring.md`](../keyring.md).

**Story:** `E16-5`

---

## Bewusst nicht: universeller Dependency-Installer

Kein Auto-Install von Python/Docker/Obsidian über Paketmanager (brew/winget/
choco/apt/dnf/pacman). Zu fragil (Sudo-Prompts, Versions-Edge-Cases, pro-OS-
Pflege) und durch das Docker-Modell grösstenteils überflüssig — die einzige
echte Host-Abhängigkeit ist **Docker** selbst.

Stattdessen **detect + guide**: OS erkennen (`platform.system()`), prüfen ob
Docker läuft, sonst OS-spezifischen Hinweis + Download-Link zu Docker Desktop
zeigen. Obsidian wird vom User separat installiert (und ist laut `E15-2`
optional — jeder Markdown-Ordner reicht).

---

## Vertrauenskommunikation (Public Repo)

Im README prominent:

> **Deine Secrets bleiben bei dir.** Seiton Brain ist 100 % self-hosted. API-Keys
> und Bot-Tokens werden nur in deiner lokalen `.env` gespeichert. Es gibt keinen
> Telemetrie- oder Cloud-Setup-Dienst.

Ergänzend: [`SECURITY.md`](../../SECURITY.md) (`E11-2` 🟢) — wo Schwachstellen melden, Threat-Model in
Kürze (Bot privat halten, Allowlist, Vault-Rechte).

---

## Technische Anknüpfung

- Settings: `app/config.py` (pydantic-settings) — `E8-1` ✅
- Fehlermeldungen bei fehlender Env: `E8-2`
- Docker: `E9-1` (non-root, HEALTHCHECK)

---

## Definition of Done (Setup-Epic)

- Neuer Selfhoster: README → `init` → `.env` editieren → `doctor` → `compose up`
  → Telegram-Test in unter 30 Minuten (Zielmetrik, nicht harte SLA)
