# Mitwirken

Danke für dein Interesse an Seiton Brain! Das Projekt ist ein **öffentliches
Portfolio-Repo (MIT)** mit geplanter kommerzieller Edition — siehe
[ADR 0005](docs/adr/0005-repo-and-license-strategy.md).

---

## Bevor du startest

1. **Roadmap prüfen:** [`ROADMAP.md`](ROADMAP.md) — gibt es schon eine Story?
2. **Größere Änderungen:** kurz als Issue anlegen oder im PR referenzieren
3. **Sicherheitslücken:** nicht als öffentliches Issue — siehe [`SECURITY.md`](SECURITY.md)

Für reine Self-Hosting-Fragen (Setup, Docker): zuerst
[`docs/self-hosting.md`](docs/self-hosting.md) und [`docs/setup.md`](docs/setup.md).

---

## Entwicklungsumgebung

```bash
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # Werte für lokale Tests anpassen
```

Tests und Lint:

```bash
pytest
ruff check app tests
```

Optional mit Docker: [`docs/setup.md`](docs/setup.md).

---

## Pull Requests

### Scope

- **Eine Story → ein PR** (ROADMAP-ID im Titel oder Body nennen, z. B. `E11-3`)
- Kleine, fokussierte Diffs — kein „Refactor nebenbei“
- Neue Features: zuerst ROADMAP-Eintrag und/oder Issue, dann Code

### Commit-Messages

Conventional Commits, z. B.:

```
feat(ui): E19-2 Dashboard unter /dashboard
fix(api): Path-Traversal bei vault_path
docs(security): E11-2 SECURITY.md
```

### PR-Checkliste

- [ ] `ruff check app tests` grün
- [ ] `pytest` grün (CI führt dasselbe aus)
- [ ] [`CHANGELOG.md`](CHANGELOG.md) unter `[Unreleased]` ergänzt
- [ ] [`ROADMAP.md`](ROADMAP.md) Status aktualisiert (🟢 wenn Story fertig)
- [ ] Bei Architektur-Entscheidungen: ADR in `docs/adr/` erwägen
- [ ] Manuell getestet, wenn Verhalten sichtbar ändert (Telegram, UI, API)

GitHub füllt beim PR-Erstellen eine Template-Checkliste vor
([`.github/pull_request_template.md`](.github/pull_request_template.md)).

---

## Code-Konventionen

| Thema | Regel |
|-------|--------|
| Config | Secrets nur via `app/config.py` / `.env` — nicht hartcodieren |
| Celery/DB | Immer `worker_session()` in Tasks (ADR 0001) |
| Vault-Pfade | `app/vault/paths.py` — Path-Traversal vermeiden |
| Prompts | Versionierte Dateien unter `prompts/`, nicht inline |
| Migrationen | Alembic unter `alembic/versions/` committen |
| `.gitignore` | `/vault/` und `/models/` (root) — nie `app/vault/` ignorieren (ADR 0002) |
| Sprache | Code/Kommentare oft DE; README DE+EN; User-facing Doku bevorzugt DE |

Details: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`.cursor/rules/seiton-brain.mdc`](.cursor/rules/seiton-brain.mdc).

---

## Tests

- Tests liegen unter `tests/` und laufen **offline** (conftest setzt Test-Env)
- Sinnvolle Tests für echtes Verhalten — keine trivialen Assert-True-Tests
- Shell-Skripte: Syntax-Check in `tests/test_scripts.py`

---

## Dokumentation

Bei user-sichtbaren Änderungen mitdenken:

- `docs/setup.md`, `docs/self-hosting.md`, `docs/packaging.md`
- `ARCHITECTURE.md` bei Modul-/Datenfluss-Änderungen
- `docs/adr/` bei nicht-offensichtlichen Entscheidungen

---

## Lizenz

Mit deinem Beitrag stimmst du zu, dass er unter der [MIT-Lizenz](LICENSE) des
Repos veröffentlicht wird.
