# Setup & Onboarding (Public Self-Hosting)

Wie Seiton Brain für andere Nutzer **einfach einrichtbar** wird — ohne
Vertrauensprobleme bei API-Keys.

> **Grundregel:** Wir sehen die Keys des Users **nie**. Alles bleibt in der
> lokalen `.env` auf seiner Maschine.

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

**Story:** `E16-1`

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

### Stufe 4 — `seiton init` TUI (Phase D/E, optional)

Interaktiver Wizard (`questionary`, `textual` oder einfaches `input()`):

1. Vault-Pfad (Default: `./vault`)
2. Telegram Bot Token
3. Telegram Webhook Secret
4. OpenAI API Key
5. Optional: Allowlist-User-IDs
6. Schreibt **nur** lokale `.env`
7. Zeigt: `docker compose up -d` + `seiton doctor`

**Wichtig:** Script läuft **lokal**, kein Netzwerk-Upload. Im README und in der
TUI explizit kommunizieren.

**Story:** `E16-3`

### Stufe 5 — Browser-Setup auf localhost (Phase E, optional)

Erster Start ohne `.env`: `http://localhost:8000/setup` (nur localhost-Bind,
einmalig, danach deaktiviert). Alternative zur TUI für weniger CLI-affine User.

**Story:** `E16-4` (Backlog, niedrige Priorität)

### Stufe 6 — OS-Keystore (Phase E, optional)

At-Rest-Schutz statt Klartext-`.env`: `seiton init` legt Keys via
[`keyring`](https://pypi.org/project/keyring/) im nativen OS-Store ab (macOS
Keychain, Windows Credential Manager, libsecret). Ein Launcher liest sie beim
`docker compose up` und injiziert sie als Env — es liegt nichts Klartext auf der
Platte.

**Docker-Vorbehalt:** Ein Container kann **nicht** direkt auf den OS-Keystore
zugreifen; der Key muss zur Laufzeit als Env in den Container. Der Keystore löst
daher nur den At-Rest-Teil, nicht die Laufzeit-Sichtbarkeit (unvermeidbar — die
App muss OpenAI aufrufen). `.env` bleibt die Baseline (headless/Server, CI).

**Referenz-Pattern:** Docker Credential Helpers (`osxkeychain`, `wincred`,
`secretservice`) machen exakt das. Kein OAuth-/Device-Flow für OpenAI/Telegram
verfügbar — die Provider bieten ihn nicht.

**Story:** `E16-5` (Backlog, niedrige Priorität)

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

Ergänzend: `SECURITY.md` (`E11-2`) — wo Schwachstellen melden, Threat-Model in
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
