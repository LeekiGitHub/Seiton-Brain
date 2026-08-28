# Engineering-Workflow (Solo Developer + KI)

Schlanke Entwicklungspraxis für **einen** Maintainer mit starker Cursor/KI-
Unterstützung — Zielbild für ein professionelles, öffentliches und später
kostenpflichtiges Self-Hosted-Produkt.

**Roadmap:** Epic **E45** in [`ROADMAP.md`](../ROADMAP.md) · **Budget bis
31.10.2026:** keine neuen laufenden Tool-Kosten (Free Tiers / GitHub / OSS).

---

## Zielbild (langfristig, nicht sofort alles)

```
Idea / Feature
  → Issue (mit Acceptance Criteria + ROADMAP-ID)
  → Feature Branch
  → Implementierung (Cursor/KI)
  → Tests
  → Pull Request
  → CI (automatisch)
  → unabhängiges Review (Mensch und/oder CodeRabbit)
  → manueller Check bei UI/Deploy-relevanten Änderungen
  → Merge nach main
  → Release / Production beim Betreiber
  → Monitoring (später, vor Verkauf)
```

**GitHub** bleibt Source of Truth für Code, Branches, PRs und CI. Issues für
technische und produktnahe Arbeit; die [`ROADMAP.md`](../ROADMAP.md) für
Epics/Phasen und Priorisierung.

---

## Ist-Analyse (Stand 2026-08)

### Bereits vorhanden / ausreichend

| Bereich | Status |
|---------|--------|
| **Roadmap & Planung** | Lebendige [`ROADMAP.md`](../ROADMAP.md), Phasen A–O, Story-IDs, Sprint-Vorschläge |
| **GitHub Issues** | Templates (Feature/Bug), Labels/Epics in Doku referenziert; Issues aktuell wenig genutzt (0 offen) — für Solo-Dev noch tragbar |
| **Branch-Workflow** | Feature Branches + manuelle PRs (Cursor); Konvention „eine Story → ein PR“ in [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
| **PR-Workflow** | [PR-Template](../.github/pull_request_template.md), Conventional Commits, CHANGELOG/ROADMAP in Checkliste |
| **CI** | GitHub Actions: `ruff`, `pytest` (~561 Tests, offline), `pip-audit`, MCP-Tests, `docker build`, Alembic + pgvector-Smoke (E29-2) |
| **Linting** | Ruff (gepinnt 0.15.x; Dependabot ignoriert 0.16+) |
| **Tests** | Breite Unit-/API-/UI-Regression-Suite unter `tests/`; Shell-Syntax-Checks |
| **Dependabot** | Wöchentlich, gruppierte Patch/Minor-PRs, separate MCP- und Actions-Updates |
| **Security (Basis)** | [`SECURITY.md`](../SECURITY.md), pip-audit in CI, Threat Model, Private Advisories |
| **Deployment** | Self-hosted Docker Compose (Consumer/VPS/Dev), `scripts/install.sh`, `update.sh`, `deploy-vps.sh`, [`docs/release.md`](release.md) |
| **Release** | Keep a Changelog, v0.3.0-Schnitt, Tag/Release-Prozess dokumentiert |
| **Architektur-Doku** | [`ARCHITECTURE.md`](../ARCHITECTURE.md), 7 ADRs in [`docs/adr/`](adr/) |
| **Agent Instructions** | [`.cursor/rules/`](../.cursor/rules/) (Projektkontext, Guardrails) |
| **Logging** | Standard-`logging` in Modulen; strukturierte JSON-Logs / zentrale Aggregation **nicht** vorhanden (für Self-Host ok) |

### Lücken / verbesserungswürdig

| Bereich | Gap | Priorität |
|---------|-----|-----------|
| **Branch Protection** | `main` vermutlich ohne erzwungene PR/CI-Checks (Repo-Setting, nicht im Code) | hoch · E45-1 |
| **Type Checking** | Kein mypy/pyright | mittel · E45-6 (später, schrittweise) |
| **Integrationstests CI** | Kein Redis/Celery/API-End-to-End in CI (nur DB-Migration-Smoke) | mittel · E45-7 |
| **Unabhängiges Review** | Nur Mensch/Cursor — kein zweiter Reviewer | mittel · E45-5 (CodeRabbit Free) |
| **Issue-Qualität** | Templates ohne explizite Acceptance Criteria | mittel · E45-3 |
| **ARCHITECTURE.md** | Veraltet (Phase C, falsches DB-Image, fehlende Module) | mittel · **E29-5** |
| **Preview/Staging** | Kein automatisches PR-Preview; manuelles `docker compose` auf Branch | akzeptabel bis Cloud · E45-8 |
| **Monitoring** | Kein Sentry/Better Stack/Uptime — `/health` nur Basis | vor Verkauf · E45-9 |
| **Product Analytics** | Kein PostHog o. Ä. | ab Beta · E45-10 |
| **Secret Scanning** | GitHub native Features nicht als Checkliste dokumentiert/aktiviert | hoch · E45-4 |
| **Coverage-Gate** | Kein Coverage-Reporting (bewusst ok — risikobasiert testen) | — |

### Aktuell Overengineering / nicht jetzt

- Linear als Ersatz für GitHub Issues
- Scrum (Story Points, Sprints, Zeremonien)
- Zwei Monitoring-Tools gleichzeitig
- 100 %-Coverage-Zwang
- Paid Preview-Hosting ohne Cloud-Edition (E24)
- Breite E2E-Browser-Tests (bereits in ROADMAP verworfen)
- Prometheus/Grafana-Stack für Single-User-Self-Host

---

## Git & GitHub

### Empfohlene Regeln (E45-1)

Auf `main` in GitHub (Settings → Branches):

- Require pull request before merging
- Require status checks: `lint-and-test`, `docker-build`, `migrate-and-vector-smoke`
- Keine Force-Pushes / kein direktes Pushen für den Alltag (Notfall: Maintainer)

### PR-Größe

- Eine ROADMAP-Story pro PR
- Kleine, reviewbare Diffs — KI-Neigungen zu großen PRs aktiv bremsen

### Rollback

- Git-Tags/Releases (`docs/release.md`)
- Betreiber: `scripts/update.sh` + Backups (`scripts/backup.sh`)

---

## CI / Quality Gates

**Heute in CI (nicht neu bauen):**

1. `pip-audit` — Dependency-Security
2. `ruff check app tests` — Lint
3. `pytest` — Unit/API/UI-Tests
4. MCP-Client-Tests
5. `docker build`
6. `alembic upgrade head` + pgvector-Smoke

**Später optional (E45-6/7):** Typ-Checking, Redis/API-Integration-Smoke.

**Nicht geplant:** Coverage-% als Merge-Blocker.

---

## Dependabot (E29-1 / E45-12)

- Patch/Minor gebündelt (wenige PRs pro Woche)
- Major einzeln und bewusst reviewen
- Dependabot-PRs durch **dieselben** Checks wie Feature-PRs
- Merge erst wenn CI grün + kurzer Blick auf Breaking Changes

---

## CodeRabbit (Evaluation, E45-5)

**Ziel:** Zweite Instanz für KI-generierten Code — ergänzt, ersetzt nicht Ruff/pytest.

**Vorgehen:**

1. Free Tier auf öffentlichem Repo testen
2. Nur sinnvolle Findings umsetzen (Security, Logik, Regression)
3. Paid-Tarif **frühestens ab Nov 2026**, wenn PR-Volumen und False-Positive-Rate es rechtfertigen

**Nicht duplizieren:** Lint-Style, triviale Formatierung (Ruff), bekannte Testlücken die bewusst offen sind.

---

## Linear (bewusst zurückgestellt, E45-11)

**Heute:** GitHub Issues + ROADMAP reichen für Solo-Dev.

**Linear erst erwägen, wenn:**

- Viele parallele Initiativen / Issues unübersichtlich werden
- MCP-Integration echten Kontext über Sessions hinweg liefert
- Klare Trennung Produkt-Roadmap (Linear) vs. Code (GitHub) nötig ist

**Paid Linear frühestens ab Nov 2026.** Kein künstliches Scrum.

---

## Architektur- & Projektgedächtnis

| Dokument | Zweck |
|----------|--------|
| [`ARCHITECTURE.md`](../ARCHITECTURE.md) | Systemüberblick, Module, Datenflüsse |
| [`docs/adr/`](adr/) | Entscheidungen mit langfristiger Wirkung (nicht für jede Kleinigkeit) |
| [`SECURITY.md`](../SECURITY.md) | Threat Model, Meldewege |
| [`ROADMAP.md`](../ROADMAP.md) | Was wann gebaut wird |

**Für Cursor/Agents vor größeren Änderungen:**

1. Relevante ROADMAP-Story
2. `ARCHITECTURE.md` + passende ADRs
3. Bestehende Tests im betroffenen Modul

Geplante Doku-Splits (nur bei Bedarf, nicht proaktiv alles anlegen): `docs/deployment.md` existiert de facto über `self-hosting.md` / `vps-deployment.md`; separates `docs/database.md` erst wenn Schema/Chunks-Komplexität es rechtfertigt (**E29-5** deckt Sync ab).

---

## Tests bei KI-Code

**Prinzip:** Requirements → Implementierung → **Tests** → CI → Review.

- Risikobasiert: Security, Datenintegrität, Capture-Pipeline, Auth, Vault-Pfade = hohe Priorität
- Keine Assert-True-Tests (siehe CONTRIBUTING)
- Manuelle Checks bei sichtbarem UI-/Telegram-Verhalten in PR-Template notieren

---

## Deployment & Preview (E45-8)

**Heute (kostenlos):**

```bash
git checkout feature-branch
docker compose up --build
# oder Consumer/VPS-Compose laut docs/self-hosting.md
```

**PR-Preview automatisch:** erst realistisch mit **E24 Cloud-Edition** oder separatem Staging-Host — nicht vor November 2026 als Paid-Pflicht einplanen.

---

## Production Monitoring (E45-9, vor E21-2 Verkauf)

**Mindestbedarf später:**

- Error Tracking (unhandled Exceptions)
- Uptime/`/health`-Check von außen
- Alerts (E-Mail/Slack) bei Ausfall

**Evaluieren (eine Lösung wählen):** Sentry **oder** Better Stack — nicht beide.

Free Tier zuerst; Paid ab Nov 2026 bei Bedarf.

---

## Product Analytics (E45-10, ab Beta/Launch)

Z. B. PostHog (Cloud Free oder Self-Hosted) — Feature-Nutzung, Funnels, Retention.

**Nicht jetzt:** Self-Hosted-Produkt ohne breite fremde Nutzerbasis; Privacy-by-Design (ADR 0004) beachten.

---

## Security-Checkliste (E45-4)

GitHub (Repository → Settings → Security):

- [ ] Dependabot alerts aktiv
- [ ] Secret scanning (public repo)
- [ ] Push protection für Secrets (falls verfügbar)
- [ ] Optional: CodeQL Analysis (kostenlos für public)

Bereits im Produkt/CI: pip-audit, SECURITY.md, API-Key-Auth, localhost-Guards (E27).

---

## Kostenprinzip

Bis **31.10.2026:**

1. Bestehende Tools besser nutzen (GitHub, Actions, Dependabot)
2. Open Source / Free Tiers
3. Prozess & Doku verbessern (dieses Dokument, E45)

Ab **Nov 2026** optional Paid, wenn klarer Gewinn: CodeRabbit, Linear, Monitoring-Upgrades, Analytics.

**Keine Architekturentscheidung** darf vor November von einem Paid-Plan abhängen.
