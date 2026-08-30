# Production Operations & Maintenance

Langfristiger Betrieb eines echten Produkts — **nach** dem ersten Release, mit
aktiven und potenziell zahlenden Nutzern. Ergänzt den Entwicklungs-Workflow in
[`engineering.md`](engineering.md); Releases siehe [`release.md`](release.md).

**Roadmap:** Epic **E46** in [`ROADMAP.md`](../ROADMAP.md) · **Budget bis
31.10.2026:** Free Tiers / Open Source / dokumentierte manuelle Prozesse.

---

## Vollständiger Lebenszyklus (Zielbild)

```
Idea / Planning (ROADMAP, Issues)
  → Development (Branch, Cursor/KI)
  → Testing + CI
  → Review (Mensch / CodeRabbit)
  → Staging / manueller Check
  → Merge → Release (Tag, CHANGELOG)
  → Production Deployment (Betreiber / Referenz-Instanz)
  → Monitoring & Alerts
  → Maintenance (Deps, Security, Backups)
  → Incidents → Recovery → Postmortem
  → weitere Entwicklung
```

**Self-Hosted (ADR 0004):** „Production“ beim **Endkunden** = seine Docker-Instanz
+ `scripts/update.sh`. Unsere Ops-Stories sichern **Release-Qualität**, Runbooks
und (später **E24**) optional managed Hosting — nicht 24/7-Betrieb für alle Kunden.

---

## 1. Release- und Update-Prozess (E46-1)

### Standard-Release (Feature / normales Bugfix)

| Schritt | Aktion |
|---------|--------|
| 1 | ROADMAP-Story / Issue mit Acceptance Criteria |
| 2 | Feature Branch |
| 3 | Implementierung + Tests |
| 4 | PR → CI grün (`lint-and-test`, `docker-build`, `migrate-and-vector-smoke`) |
| 5 | Review (Mensch / CodeRabbit E45-5) |
| 6 | Staging: `docker compose up --build` auf Branch (E45-8) |
| 7 | Merge `main` |
| 8 | Release: CHANGELOG schneiden, Tag `vX.Y.Z`, GitHub Release ([`release.md`](release.md)) |
| 9 | Production: Betreiber führt `update.sh` / `deploy-vps.sh` aus |
| 10 | Monitoring: Fehler/Uptime nach Deploy prüfen (E46-3) |

### Bereits vorhanden

- SemVer + Keep a Changelog
- [`docs/release.md`](release.md) (Tag, GitHub Release)
- `scripts/update.sh`, `scripts/deploy-vps.sh`, `scripts/backup.sh`
- CI inkl. Migrations-Smoke (E29-2)

### Bewusst später / optional

| Thema | Wann |
|-------|------|
| **Automatisiertes Deploy** | Erst **E24** Cloud-Edition oder eigener Staging-Host |
| **Feature Flags** | Nur bei hohem Rollout-Risiko (Cloud); nicht Standard Self-Host |
| **PR-Preview-URLs** | Erst mit hosted Staging (E24); bis dahin manuelles Compose |

---

## 2. Hotfix-Prozess (E46-2)

Für **kritische** Production-Probleme (P0): Datenverlust, Auth-Bypass, kompletter
Ausfall, Sicherheitslücke.

```
Critical Bug / Incident
  → Issue mit Label/Severity P0
  → Hotfix-Branch von main (oder letztem stabilen Tag)
  → Minimaler Fix + gezielte Regressionstests
  → PR → CI (alle required checks)
  → Expedited Review (selbst oder CodeRabbit)
  → Merge → Patch-Release vX.Y.Z+1
  → Deploy + Monitoring
  → Root-Cause / Postmortem (E46-10) wenn nötig
```

**Quality Gates bleiben** — kein Skip von CI; Scope und Review-Zeit sind kürzer.

---

## 3. Monitoring & Alerting (E46-3, Synergie E45-9)

### Minimum vor öffentlichem Launch

| Signal | Zweck |
|--------|--------|
| **Uptime** | `GET /health` von außen (Referenz-Instanz / später Cloud) |
| **Error Tracking** | Unhandled Exceptions (API, Worker) |
| **Logs** | Docker `json-file` + Rotation (E29-6); zentrale Aggregation optional später |
| **Health erweitert** | Worker erreichbar, Vault schreibbar (E29-6) |
| **Background Jobs** | Wiederholte Celery-Failures (`entries.status=failed`) |

### Sinnvolle Alerts (kein Spam)

**Alarmieren:**

- API/Health nicht erreichbar
- Deutlich erhöhte Error-Rate vs. Baseline
- Kernflows broken (Capture, Login, Suche)
- Worker/DB dauerhaft down
- Backup fehlgeschlagen (wenn automatisiert)

**Nicht alarmieren:**

- Einzelne 4xx, einzelne LLM-Rate-Limits mit Retry
- Erwartete Validierungsfehler
- Jeder Celery-Retry

**Tool:** eine Lösung wählen (Sentry **oder** Better Stack) — Free Tier; Paid ab
Nov 2026.

---

## 4. Incident Management — Solo (E46-4)

Kein Enterprise-ITSM. Kurzes Runbook:

1. **Alert** oder User-Report
2. **Bestätigen** — echtes Problem vs. Flapping?
3. **Impact** — wer betroffen, welche Daten?
4. **Untersuchen** — Logs, `/health`, `docker compose ps`, DB, Worker-Queue
5. **Entscheiden** — Rollback (E46-5) oder Hotfix (E46-2)
6. **Wiederherstellen** — Service ok, Nutzer informieren wenn nötig
7. **Follow-up Issue** — Fix-Härtung, Test, Monitoring
8. **Postmortem** bei relevantem Incident (E46-10)

---

## 5. Rollback & Recovery (E46-5)

### Deployment-Rollback (Self-Host)

| Methode | Wann |
|---------|------|
| `git checkout vX.Y.Z` + `docker compose build` + `update.sh` | Code-Rollback auf letzten Tag |
| Vorheriges Docker-Image (wenn versioniert) | Schneller Rollback |
| Backup-Restore | Daten kaputt / Migration fehlgeschlagen |

### Datenbank-Migrationen

- **Vor Production:** Migration in CI (`alembic upgrade head`) + Staging
- **Rollback-Limit:** Alembic `downgrade` nicht immer sicher — bevorzugt **forward-fix**
  + Backup vor Migration
- **KI-generierte Migrationen:** immer manuell reviewen (E46-7)

### Kompatibilität

- App-Version und Schema-Version zusammen denken
- Breaking Changes nur mit Migrationspfad + CHANGELOG-Hinweis

---

## 6. Backups & Restore (E46-6, Synergie E29-4, E25-1)

| Frage | Ist / Ziel |
|-------|------------|
| **Was?** | Postgres (`pg_dump`), Vault (`tar`), optional `.env` (manuell, secrets!) |
| **Wie oft?** | Vor Updates (`update.sh`), UI One-Click (E25-1), optional Cron |
| **Retention?** | Rotation konfigurierbar (**E29-4** — heute unbegrenzt) |
| **Automatisiert?** | Teilweise (`backup.sh`, UI); Cron-Doku für Betreiber |
| **Restore getestet?** | **Pflicht vor E21-2** — automatisierter Roundtrip (E29-4) |

> Ein Backup zählt erst, wenn ein Restore einmal erfolgreich war.

Dieser Abschnitt deckt den **Betrieb** ab (eine Instanz, ein Backup-Ziel). Die
spätere nutzersichtbare Produktfähigkeit mit mehreren Zielen, 3-2-1-Policy und
Backup-Health ist **E48 Backup Guardian** ([`ROADMAP.md`](../ROADMAP.md), nach
V1.5) — sie baut hierauf auf und ersetzt es nicht.

---

## 7. Datenbank-Migrationen (E46-7)

Checklist vor Merge einer Alembic-Migration (bes. KI-generiert):

- [ ] `upgrade` und ggf. `downgrade` auf leerer DB getestet (CI)
- [ ] Auf Staging mit **echten** Datenmustern getestet
- [ ] Nullable/default für neue Spalten wo möglich (expand)
- [ ] Lange Locks vermieden (große Tabellen)
- [ ] Datenmigration idempotent oder backfill-Plan
- [ ] CHANGELOG + ggf. Betreiber-Hinweis („Backup vor Update“)

---

## 8. Dependency- & Security-Maintenance (E46-8)

| Quelle | Cadence |
|--------|---------|
| Dependabot (grouped PRs) | wöchentlich prüfen |
| `pip-audit` in CI | jeder PR |
| GitHub Security Advisories | bei Meldung |
| Python/Postgres EOL | ROADMAP/ADR planen |

**Priorität:** CVE mit Exploit / Auth / RCE sofort; Minor-Patches gebündelt;
Major bewusst (wie openai 2→3).

Secrets: `.env` nie committen; Rotation bei Verdacht; Keyring optional (E16-5).

---

## 9. Production-Bug-Flow (E46-9)

```
User Report / Error Tracking / eigener Fund
  → GitHub Issue (Severity, Repro, Version/Tag)
  → Priorisierung (P0 Hotfix vs. normaler Sprint)
  → Reproduktion (lokal / Staging)
  → Fix + Regressionstest
  → PR → CI → Review
  → Release + Deploy
  → Verifikation in Production / Monitoring
```

Wichtige Bugs: **Regressionstest** verhindert Wiederkehr.

---

## 10. Post-Incident Learning (E46-10)

Nur bei **relevanten** Incidents (Ausfall, Datenrisiko, Security) — kein Theater
bei Tippfehlern.

Kurz dokumentieren (Issue-Kommentar oder `docs/incidents/YYYY-MM-DD-slug.md`):

1. Was ist passiert?
2. Warum (Root Cause)?
3. Warum haben Schutzmechanismen nicht geholfen?
4. Wie erkannt?
5. Wie behoben?
6. Was verhindert Wiederholung? (Issue/Test/Alert/Architektur)

---

## Zeitliche Einordnung

| Meilenstein | E46-Stories (Minimum) |
|-------------|------------------------|
| **Jetzt (laufend)** | E46-8 Dependabot-Cadence · E46-1 Doku |
| **Vor Beta** | E46-9 Production-Bug-Flow · E46-1 Release-Prozess verfeinert |
| **Vor öffentlichem Launch** | E46-3 Monitoring · E46-4 Incidents · E46-5 Rollback · E46-7 Migrationen · E46-10 Postmortem |
| **Vor kostenpflichtigem Verkauf (E21-2)** | E46-6 Backup/Restore verifiziert |
| **Ab Nov 2026** | Paid Monitoring/Logging-Upgrades nur bei Bedarf |

---

## Kosten

Wie E45: bis **31.10.2026** keine neuen Ops-SaaS-Kosten. Free Tiers für
Monitoring/Errors. Paid ab **November 2026** nur mit klarem ROI — nicht vorsorglich
kaufen.
