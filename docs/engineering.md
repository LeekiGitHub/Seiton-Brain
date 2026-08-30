# Engineering-Workflow (Solo Developer + KI)

Schlanke Entwicklungspraxis für **einen** Maintainer mit starker Cursor/KI-
Unterstützung — Zielbild für ein professionelles, öffentliches und später
kostenpflichtiges Produkt (zuerst self-hosted ausgeliefert,
[ADR 0008](adr/0008-deployment-models-self-hosted-first.md)).

**Roadmap:** Epics **E45** (Entwicklung) und **E46** (Production Ops) in
[`ROADMAP.md`](../ROADMAP.md) · **Budget bis 31.10.2026:** keine neuen laufenden
Tool-Kosten (Free Tiers / GitHub / OSS).

**Production-Betrieb nach Release:** [`docs/production-ops.md`](production-ops.md)
(Releases, Monitoring, Incidents, Recovery, Wartung).

**UI/UX & Designsystem:** Epic **E47** in der ROADMAP — `docs/ui-inventory.md`
(E47-1) und `docs/design-system.md` (E47-3) entstehen dort und existieren noch nicht.

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
  → Release (Tag, CHANGELOG — siehe production-ops.md)
  → Production / Update beim Betreiber
  → Monitoring → Maintenance → Incidents → Recovery
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
| **Security (Basis)** | [`SECURITY.md`](../SECURITY.md), pip-audit in CI, Threat Model, Private Advisories; Secret Scanning + Push Protection; Dependabot Alerts + Security Updates; CodeQL Default Setup (E45-4) |
| **Branch Protection** | Ruleset *Protect main*: PR-Pflicht, required CI, kein Force-Push; Head-Branches nach Merge auto-löschen (E45-1) |
| **Deployment** | Self-hosted Docker Compose (Consumer/VPS/Dev), `scripts/install.sh`, `update.sh`, `deploy-vps.sh`, [`docs/release.md`](release.md) |
| **Release** | Keep a Changelog, v0.3.0-Schnitt, Tag/Release-Prozess dokumentiert |
| **Architektur-Doku** | [`ARCHITECTURE.md`](../ARCHITECTURE.md), 7 ADRs in [`docs/adr/`](adr/) |
| **Agent Instructions** | [`.cursor/rules/`](../.cursor/rules/) (Projektkontext, Guardrails) |
| **Logging** | Standard-`logging` in Modulen; strukturierte JSON-Logs / zentrale Aggregation **nicht** vorhanden (für Self-Host ok) |

### Lücken / verbesserungswürdig

| Bereich | Gap | Priorität |
|---------|-----|-----------|
| **GitHub Issues** | Faktisch seit Juni 2026 nicht mehr genutzt (letztes Issue #77, 0 offen) — der reale Prozess läuft über ROADMAP-Story → Branch → PR | Prozess an Realität anpassen · E45-3 |
| **Agent-Kontext** | ROADMAP geschrumpft (E45-13); Archiv A–H + `docs/current-state.md` + Phasen-M–O-Detail | 🟢 E45-13 |
| **Visuelle Prüfung** | Keine Browser-/Screenshot-Prüfung; 66 Testdateien laufen ausschließlich headless über den FastAPI-TestClient. Kein Node, kein Playwright im Repo | mittel · **E45-15** |
| **Designsystem** | CSS-Variablen in `app/ui/static/app.css`, aber keine dokumentierte Designsprache; UI entstand implementierungsgetrieben | mittel · **Epic E47** |
| **Definition of Done** | Vorhanden, aber pauschal und Telegram-zentriert — nicht risikobasiert | mittel · **E45-14** |
| **Type Checking** | Kein mypy/pyright | mittel · E45-6 (später, schrittweise) |
| **Integrationstests CI** | Kein Redis/Celery/API-End-to-End in CI (nur DB-Migration-Smoke) | mittel · E45-7 |
| **Unabhängiges Review** | Nur Mensch/Cursor — kein zweiter Reviewer | mittel · E45-5 (CodeRabbit Free) |
| **Issue-Qualität** | Templates ohne explizite Acceptance Criteria | mittel · E45-3 |
| **ARCHITECTURE.md** | Veraltet (Phase C, falsches DB-Image, fehlende Module) | mittel · **E29-5** |
| **Preview/Staging** | Kein automatisches PR-Preview; manuelles `docker compose` auf Branch | akzeptabel bis Cloud · E45-8 |
| **Monitoring** | Kein Sentry/Better Stack/Uptime — `/health` nur Basis | vor Verkauf · E45-9 |
| **Product Analytics** | Kein PostHog o. Ä. | ab Beta · E45-10 |
| **Coverage-Gate** | Kein Coverage-Reporting (bewusst ok — risikobasiert testen) | — |

### Aktuell Overengineering / nicht jetzt

- Linear als Ersatz für GitHub Issues
- Scrum (Story Points, Sprints, Zeremonien)
- Zwei Monitoring-Tools gleichzeitig
- 100 %-Coverage-Zwang
- Paid Preview-Hosting ohne Cloud-Edition (E24)
- Breite E2E-Browser-Tests (bereits in ROADMAP verworfen — der schmale Visual-Smoke **E45-15** ist die Ausnahme)
- Prometheus/Grafana-Stack für Single-User-Self-Host
- Visual-Regression-SaaS (Percy/Chromatic) und Design-Tool-Abos vor Nov 2026
- Migration auf React/Tailwind o. Ä. — Jinja2 + Vanilla JS trägt 7 Screens (Neubewertung bei E40)

---

## Git & GitHub

### Branching-Strategie (Trunk / PR)

**Modell:** ein langlebiger Branch — `main`. Arbeit läuft auf **kurzlebigen**
Branches (`feat/…`, `fix/…`, `chore/…`, `docs/…`) → Pull Request → CI → Merge.

**Kein** `develop`, `staging` oder `production` nur aus Konvention. Releases sind
**Git-Tags auf `main`** (`docs/release.md`); Self-Host-Updates ziehen `main` bzw.
einen Tag (`scripts/update.sh`). Es gibt keine zweite Deploy-Pipeline, die einen
zweiten langlebigen Branch bräuchte.

**Umgebungen ≠ Branches:** Preview/Staging/Production (wenn später, z. B. E24/E45-8)
sind Deployments eines Commits/Tags — nicht eigene Git-Linien.

**Hotfixes (E46-2):** gleicher Pfad, nur schmalerer Scope; kein dauerhafter
`hotfix/`-Trunk.

### Branch Protection (E45-1)

Ruleset [Protect main](https://github.com/LeekiGitHub/Seiton-Brain/rules/21859080):

- Pull Request vor Merge (0 Reviewer — Solo-Maintainer merged selbst)
- Required status checks, branch muss aktuell sein: `lint-and-test`,
  `docker-build`, `migrate-and-vector-smoke`
- Kein Force-Push (`non_fast_forward`), `main` nicht löschbar
- Notfall: Ruleset kurz auf *Evaluate* oder Bypass — nicht alltäglich direkt pushen

### Head-Branches nach Merge löschen

**Aktiviert** (`delete_branch_on_merge`): GitHub löscht den PR-Head-Branch nach
Merge. Passt zum kurzlebigen-Branch-Workflow; verhindert die bisherige
Remote-Leiche. Lokale Kopien: `git fetch --prune` und bei Bedarf `git branch -d`.

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

**Ziel:** Zweite, vom Implementierungs-Agenten unabhängige Instanz für
KI-generierten Code — ergänzt, ersetzt nicht Ruff/pytest.

**Eignung (geprüft 2026-08-29):** Das Repo ist öffentlich (MIT) → **Open-Source-Plan**,
dauerhaft kostenlos, kein Paid-Bedarf vor November 2026. Python wird unterstützt;
Ruff kann als bereits vorhandener Linter angebunden werden statt dupliziert zu werden.

**Einschränkung:** Für öffentliche Repos mit **< 10 Stars** verlangt CodeRabbit einen
**manuellen Review-Trigger** (`@coderabbitai review` im PR). Das Repo hat aktuell 0 Stars
— Reviews sind also kein Automatismus, sondern ein bewusster Schritt im PR. Für einen
Solo-Rhythmus von ~1 PR/Tag ist das tragbar.

**Vorgehen:**

1. App auf dem Repo installieren, `.coderabbit.yaml` mit engem Scope (Sprache Deutsch,
   Fokus Security/Logik/Datenintegrität, Ruff als bestehender Linter, Pfad-Ignores für
   `docs/`, `vault.example/`)
2. 5–10 PRs mitlaufen lassen, Signal/Rauschen bewerten
3. Nur sinnvolle Findings umsetzen (Security, Logik, Regression)
4. Entscheidung dokumentieren: behalten oder abschalten

**Darf nichts ersetzen:** `ruff`, `pytest`, `pip-audit`, Docker-Build und
Migrations-Smoke bleiben die verbindlichen Gates — CodeRabbit ist beratend, nie
Merge-Voraussetzung. Ebenso wenig ersetzt es die menschliche Produktprüfung.

**Datenschutz:** Der Dienst sieht Code eines ohnehin öffentlichen Repos — kein
zusätzliches Risiko. Vor einem etwaigen Wechsel auf **privat** neu bewerten
(dann Paid-Frage, frühestens Nov 2026).

---

## Linear (bewusst zurückgestellt, E45-11)

**Heute:** GitHub Issues + ROADMAP reichen für Solo-Dev.

**Linear erst erwägen, wenn:**

- Viele parallele Initiativen / Issues unübersichtlich werden
- MCP-Integration echten Kontext über Sessions hinweg liefert
- Klare Trennung Produkt-Roadmap (Linear) vs. Code (GitHub) nötig ist

**Paid Linear frühestens ab Nov 2026.** Kein künstliches Scrum.

---

## Anwendung ausführen & prüfen (Ist-Stand 2026-08-29)

Grundlage für **E45-15** und **E47-1**. Ohne diesen Abschnitt bleibt „mal selbst
anschauen" eine Absichtserklärung.

| Frage | Antwort |
|-------|---------|
| **Wie startet die App lokal?** | `docker compose up --build` (api, worker, db, redis) oder Consumer-Weg `./scripts/install.sh` → `docker-compose.consumer.yml` mit Telegram-Long-Polling |
| **Was ist Desktop?** | **Nichts.** Es existiert keine Desktop-App; native App (**E20-3/5**) ist ausdrücklich kein Nahziel (ADR 0004) |
| **Was ist Web?** | Alles Sichtbare: `/setup`, `/dashboard`, `/ask`, `/notes`, `/settings`, `/login` — Jinja2-Templates, vom eigenen Host serviert |
| **Mobile?** | PWA (E23-2): Manifest, Service Worker, Icons — installierbar, keine native App |
| **Preview-Deployments?** | Nein. Manuelles Staging über Branch + `docker compose` (E45-8) |
| **Test-/Staging-Umgebung?** | Keine dedizierte; CI hat Service-Container (pgvector, Alembic-Smoke) — die Basis für einen späteren Smoke-Job |
| **Was ist automatisiert öffenbar?** | Die komplette Web-UI, sobald der Stack läuft |
| **Installer?** | `scripts/install.sh` (macOS/Linux) und `scripts/install.ps1` (Windows): Vault anlegen → `.env` erzeugen → Compose starten → Migrationen → Browser zum Setup-Wizard. Dazu `doctor.sh`/`doctor.ps1` als Diagnose. Kein GUI-Installer, keine Signierung |
| **Plattformen heute** | Überall wo Docker läuft: macOS, Linux, Windows (Docker Desktop). Leitbild: Always-on-Box beim Kunden |
| **Plattformen geplant** | VPS als Alternative (E20-2, dokumentiert), Cloud-Edition gated auf ADR 0007. Native Desktop/App: nicht geplant |

---

## Visuelle & funktionale Prüfung (E45-15)

**Ausgangslage:** 66 Testdateien / ~561 Tests laufen offline über den FastAPI-
TestClient. Sie prüfen HTML-Ausgaben und JSON, aber **nie einen echten Browser** —
kaputtes CSS, JS-Fehler oder ein nicht klickbarer Button fallen nicht auf.

**Ist Playwright für diesen Stack geeignet?** Ja, mit Einschränkungen:

| Frage | Bewertung |
|-------|-----------|
| Passt es zur Web-UI? | Ja — normales serverseitiges HTML + Vanilla JS, kein SPA-Framework, keine exotischen Widgets |
| Ohne Node-Toolchain? | Ja — `pytest-playwright` (Apache-2.0) ist Python-nativ und fügt sich in die bestehende pytest-Suite ein. Browser-Binaries kommen per `playwright install` (~Hunderte MB, lokal/CI-Cache) |
| Screenshots automatisiert? | Ja — `page.screenshot()` pro Screen als Artefakt |
| Kann ein Agent die Screenshots auswerten? | Ja, aber **begrenzt**: Cursor kann PNG-Dateien lesen und beschreiben. Das erkennt grobe Fehler (leere Seite, zerschossenes Layout, fehlende Elemente) — es ist **kein** verlässlicher Pixel-Diff und **kein** Ersatz für ein menschliches Urteil über Ästhetik. Deterministischer sind DOM-Assertions; Screenshots sind das Zusatzsignal |
| Console-Errors / fehlgeschlagene Requests? | Ja — `page.on("console")` und `page.on("response")` liefern beides; das ist der wertvollste Teil des PoC |
| Lokal isoliert möglich? | Ja, aber nur mit laufendem Stack: Postgres **mit pgvector** und Redis sind Pflicht (ADR 0006, kein SQLite-Fallback). Praktisch heißt das `docker compose up` vorher |
| Später in CI? | Realistisch — die Service-Container aus `migrate-and-vector-smoke` sind die Vorlage. Erst nach erfolgreichem lokalem PoC, um keinen flaky Job zu erben |
| Desktop-Anwendung? | Entfällt — es gibt keine |
| Installer-Testing? | Playwright hilft nicht bei Shell-Skripten. Vorhanden bleiben Syntax-Checks (`tests/test_scripts.py`) und `doctor.sh`; ein echter Installer-Test wäre ein Container-Durchlauf von `install.sh` — eigene, spätere Story, nicht Teil von E45-15 |

**Grenzen, die ehrlich benannt gehören:**

- Ein Agent, der Screenshots liest, sieht *nicht* wie ein Nutzer. Er erkennt „Seite
  leer", nicht „fühlt sich zäh an" oder „Wortwahl verwirrt".
- Der Nutzen von Screenshots hängt an einem realistischen Datenbestand — eine leere
  Instanz zeigt vor allem Empty-States.
- Deshalb bleibt der **Mini-Handcheck** (E45-14) Bestandteil der DoD für UI-Stories
  und wird nicht wegautomatisiert.

**Bewusst nicht:** breites E2E-Regressionsnetz, Cross-Browser-Matrix,
Visual-Regression-SaaS (Percy/Chromatic — kostenpflichtig, ADR-widrig vor Nov 2026).

---

## Architektur- & Projektgedächtnis

| Dokument | Zweck |
|----------|--------|
| [`ARCHITECTURE.md`](../ARCHITECTURE.md) | Systemüberblick, Module, Datenflüsse |
| [`docs/adr/`](adr/) | Entscheidungen mit langfristiger Wirkung (nicht für jede Kleinigkeit) |
| [`SECURITY.md`](../SECURITY.md) | Threat Model, Meldewege |
| [`ROADMAP.md`](../ROADMAP.md) | Was als Nächstes gebaut wird (aktiv, kompakt) |
| [`docs/current-state.md`](current-state.md) | Kurzstand für Agents |
| [`docs/archive/`](archive/) | Abgeschlossene Roadmap-Historie |

**Für Cursor/Agents vor größeren Änderungen:**

1. Relevante ROADMAP-Story
2. `ARCHITECTURE.md` + passende ADRs
3. Bestehende Tests im betroffenen Modul

### Kontext-Hygiene (E45-13)

Arbeitsteilung, an der sich künftig entschieden wird, wohin eine Information gehört:

| Frage | Ort |
|-------|-----|
| Was machen wir als Nächstes? | `ROADMAP.md` |
| Wie und warum ist das System so gebaut? | `ARCHITECTURE.md`, `docs/adr/` |
| Was wurde tatsächlich implementiert? | Git-Historie, `CHANGELOG.md` |
| Was war früher geplant und ist erledigt? | `docs/archive/` |
| Wo steht das Projekt gerade? | `docs/current-state.md` (Einstieg für Agents) |

**Messbares Problem (gelöst E45-13):** `ROADMAP.md` war auf 1015 Zeilen mit 210
Stories gewachsen. Abgeschlossene Phasen A–H liegen unter
[`docs/archive/roadmap-phases-a-h.md`](archive/roadmap-phases-a-h.md);
Phasen M–O-Detail unter [`docs/roadmap-phases-m-o.md`](roadmap-phases-m-o.md);
Agent-Einstieg: [`docs/current-state.md`](current-state.md). Aktive ROADMAP
zielt auf ≲ 400 Zeilen.

Geplante Doku-Splits (nur bei Bedarf, nicht proaktiv alles anlegen): `docs/deployment.md` existiert de facto über `self-hosting.md` / `vps-deployment.md`; separates `docs/database.md` erst wenn Schema/Chunks-Komplexität es rechtfertigt (**E29-5** deckt Sync ab).

---

## Tests bei KI-Code

**Prinzip:** Requirements → Implementierung → **Tests** → CI → Review.

- Risikobasiert: Security, Datenintegrität, Capture-Pipeline, Auth, Vault-Pfade = hohe Priorität
- Keine Assert-True-Tests (siehe CONTRIBUTING)
- Manuelle Checks bei sichtbarem UI-/Telegram-Verhalten in PR-Template notieren

---

## Definition of Done — risikobasiert (Zielbild, E45-14)

Nicht jede Story braucht jedes Gate. Vorschlag als Matrix nach Change-Typ; die
verbindliche Fassung entsteht in **E45-14** und wandert in `ROADMAP.md`,
`CONTRIBUTING.md` und das PR-Template.

| Gate | Doku | Backend/API | UI | Migration | Security |
|------|------|-------------|----|-----------|----------|
| Acceptance Criteria erfüllt | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ruff` grün | ✓ | ✓ | ✓ | ✓ | ✓ |
| `pytest` grün | ✓ | ✓ | ✓ | ✓ | ✓ |
| Neue/angepasste Tests | — | ✓ | ✓ | ✓ | ✓ (Regression!) |
| CI grün (inkl. Docker-Build, Migrations-Smoke) | ✓ | ✓ | ✓ | ✓ | ✓ |
| CHANGELOG + ROADMAP-Status | ✓ | ✓ | ✓ | ✓ | ✓ |
| Visual-Smoke + Screenshots (E45-15) | — | — | ✓ | — | bei UI-Bezug |
| **Mini-Handcheck durch den Entwickler** | — | bei sichtbarem Verhalten | ✓ | ✓ (Restore/Rollback) | ✓ |
| Unabhängiges Review (CodeRabbit, E45-5) | optional | ✓ | ✓ | ✓ | ✓ |
| ADR erwägen | — | bei Architekturwirkung | — | bei Schemawirkung | ✓ |

**Mini-Handcheck** heißt: der Agent liefert am Ende der Story drei konkrete Schritte,
die in ~2 Minuten prüfbar sind — nicht „bitte teste die App". Beispiel:

```
E30-4 fertig. Automatisch: ruff ✓ · pytest ✓ · CI ✓ · Visual-Smoke ✓ (4 Screenshots)
Bitte kurz selbst prüfen:
1. http://localhost:8000/notes öffnen, eine Notiz löschen
2. Prüfen: Toast erscheint statt Browser-confirm(), Undo funktioniert
3. Seite neu laden — Notiz ist wirklich weg
```

Bei rein technischen Änderungen (Refactor ohne sichtbare Wirkung, Dependency-Bumps,
Doku) entfällt der Handcheck.

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

GitHub (Repository → Settings → Security), Stand 2026-08-30:

- [x] Dependabot alerts
- [x] Dependabot security updates
- [x] Secret scanning (public repo)
- [x] Push protection für Secrets
- [x] CodeQL default setup (kostenlos für public)
- [ ] Optional später: Secret scanning *validity checks* / non-provider patterns

Bereits im Produkt/CI: pip-audit, SECURITY.md, API-Key-Auth, localhost-Guards (E27).

---

## Kostenprinzip

Bis **31.10.2026:**

1. Bestehende Tools besser nutzen (GitHub, Actions, Dependabot)
2. Open Source / Free Tiers
3. Prozess & Doku verbessern (dieses Dokument, E45)

Ab **Nov 2026** optional Paid, wenn klarer Gewinn: CodeRabbit, Linear, Monitoring-Upgrades, Analytics.

**Keine Architekturentscheidung** darf vor November von einem Paid-Plan abhängen.

---

## Production Operations (nach Release)

Entwicklung endet nicht mit dem ersten Release. Langfristiger Betrieb
(Monitoring, Incidents, Rollback, Backup-Verifikation, Hotfixes) ist in
[`production-ops.md`](production-ops.md) und Epic **E46** in der ROADMAP
beschrieben — schrittweise vor Beta, Launch und **E21-2** Verkauf.
