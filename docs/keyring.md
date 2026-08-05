# OS-Keystore (E16-5)

Optionale Ablage von API-Secrets im **nativen OS-Keystore** statt Klartext in
`.env` — via [`keyring`](https://pypi.org/project/keyring/) (MIT):

| Plattform | Backend |
|-----------|---------|
| macOS | Keychain |
| Windows | Credential Manager |
| Linux | Secret Service / libsecret |

## Setup

```bash
pip install -r requirements-keyring.txt
./scripts/seiton init --keyring
# interaktiv: Frage „Secrets im OS-Keystore …“ mit Ja beantworten
```

`.env` erhält `SEITON_KEYRING=true`; Secret-Felder bleiben leer. Werte liegen
unter Service-Name `seiton-brain` im Keystore.

## Start

Docker-Container sehen den Host-Keystore **nicht**. Deshalb:

```bash
./scripts/seiton-up.sh          # statt rohem docker compose up
./scripts/seiton-up.sh down
```

Ablauf: `seiton keyring-export --shell` → Env setzen → Compose inkl.
[`deploy/compose.keyring.yml`](../deploy/compose.keyring.yml) (überschreibt
leere `env_file`-Werte).

## Grenzen

- Runtime: Keys sind im Container-Prozess weiterhin als Env sichtbar (nötig für
  API-Calls) — der Keystore schützt **At-Rest** auf der Platte.
- Headless/CI/VPS ohne Keystore: `SEITON_KEYRING=false`, Secrets weiter in `.env`
  (`chmod 600`).
- UI-Setup-Wizard schreibt weiterhin in `.env`; bei Keystore-Modus danach
  `./scripts/seiton init --keyring` erneut oder Secrets manuell migrieren.

## CLI

| Kommando | Zweck |
|----------|--------|
| `seiton init --keyring` | Secrets speichern, `.env` bereinigen |
| `seiton keyring-export` | `KEY=value`-Zeilen |
| `seiton keyring-export --shell` | `export KEY=…` für `eval` |
