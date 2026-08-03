# ADR 0006: Consumer-Stack — kein SQLite-/in-process-Fork (E9-5 Eval)

- **Status:** Accepted
- **Datum:** 2026-08-03
- **Entscheider:** Yannik
- **Phase / Epic:** Phase G · epic:infra (E9-5)
- **Bezug:** schließt die offene Detailfrage in
  [ADR 0004](./0004-commercial-consumer-product.md) („Wie weit Stack-Vereinfachung?")

## Kontext

ADR 0004 verlangt, eine **Stack-Vereinfachung für die Consumer-/Heim-Box** zu
evaluieren: z. B. SQLite statt Postgres, in-process Worker statt Redis/Celery —
weniger bewegliche Teile für Privatkunden. Gleichzeitig gilt dort: Editionen
sind voraussichtlich **ein Stack an verschiedenen Hosting-Orten**, keine zwei
Codebasen.

Seit der ADR ist geliefert:

| Baustein | Status |
|----------|--------|
| Long-Polling (kein öffentlicher Webhook) | E1-5 🟢 |
| Consumer-Installer + Compose-Profil | E20-1 🟢 |
| Web-UI / Setup-Wizard | E19 🟢 |
| Semantische Suche / RAG (pgvector) | E17 🟢 |
| VPS-Pfad (voller Stack + Proxy) | E20-2 / E9-3 🟢 |

Die Evaluationsfrage: Lohnt sich jetzt ein zweiter Persistenz-/Worker-Pfad?

## Entscheidung

1. **Ein Stack bleibt:** PostgreSQL (+ pgvector) + Redis + Celery für
   **Consumer (Heim-Box) und VPS**. Keine parallele SQLite-Edition, kein
   Ersatz von Celery durch einen in-process-Worker im Produktpfad.

2. **Vereinfachung für Endnutzer** passiert über **Packaging & Doku**
   (`install.sh` / `install.ps1`, Setup-Wizard, `doctor`, Compose-Profile) —
   nicht über eine zweite Architektur.

3. **Wiederaufnahme nur bei Messwerten:** Wenn Support-/Install-Reibung klar
   auf „zu viele Container" zurückgeht *und* RAG/pgvector verzichtbar oder
   ersetzt wäre, ADR neu öffnen. Bis dahin: kein Fork.

## Eval-Kriterien (Ergebnis)

### SQLite statt Postgres

| Kriterium | Befund |
|-----------|--------|
| Setup-Komplexität | Für Docker-Nutzer gering (ein Service weniger); Installer versteckt Postgres bereits |
| pgvector / E17 | **Blocker:** Embeddings und kNN hängen an Postgres+pgvector. SQLite bräuchte sqlite-vss o. Ä. oder Feature-Abschaltung |
| Nebenläufigkeit | API + Worker + Poller schreiben parallel — SQLite-Write-Lock erhöht Fehlerrisiko |
| Migrationen / Ops | Zweiter Dialekt (Alembic, Backups, Doctor) = dauerhafte Doppelpflege |
| Nutzen vs. Aufwand | **Negativ** — Produktkern Retrieval würde verwässert oder verdoppelt |

**Fazit SQLite:** nein (jetzt und absehbar).

### In-process Worker statt Redis/Celery

| Kriterium | Befund |
|-----------|--------|
| Weniger Container | Ja (Redis + Worker entfallen) |
| Retries / Backoff (E10-2) | Müssten neu gebaut werden; Whisper/LLM sind lang laufend |
| Prozess-Isolation | LLM-/Whisper-Fehler oder OOM treffen die API |
| ADR 0001 | Async-Engine-pro-Task ist auf Celery-`asyncio.run` zugeschnitten — Umbau nicht trivial |
| Nutzen vs. Aufwand | **Gering** relativ zur Doppelimplementierung; Heim-Box hat RAM für den aktuellen Compose-Stack |

**Fazit in-process:** nein als Produktpfad. Optional später nur als
Dev-/Experiment-Flag, nicht als Consumer-Edition.

### Eine vs. zwei Editionen

Bestätigt ADR 0004: **eine Codebasis**, zwei **Hosting-Profile**
(`SEITON_DEPLOY_MODE=consumer` vs. `vps`) — Polling vs. Webhook, Restart-
Policies, Remote-Zugang. Keine getrennten Produkte „Lite/Pro".

## Konsequenzen

### Positiv

- Keine Feature-Matrix „RAG nur mit Postgres-Edition".
- Keine doppelten Migrationen, Health-Checks, Backup-Skripte.
- Fokus bleibt auf Setup-Reibung (Installer, Doctor, UI) statt Stack-Fork.

### Negativ / Trade-offs

- Consumer-Compose bleibt bei mehreren Services (db, redis, api, worker, poller).
- Wer „eine Binary ohne Docker" will, ist weiterhin nicht bedient (bewusst
  später / anderes Epic, nicht E9-5).

### Folgearbeiten

- E9-5 in der Roadmap auf 🟢 (Eval abgeschlossen).
- ADR 0004 „Offene Detailentscheidungen" um Verweis auf diese ADR bereinigen.
- Weiterhin: Packaging/Doctor/Onboarding verbessern, wenn Support-Themen auftauchen.
- **Nicht** geplant: SQLite-Backend, Celery-Entfernung, zweite Codebasis.

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|-------------|--------------|
| SQLite + Keyword-only (ohne semantische Suche) | Schwächt das Retrieval-Verkaufsargument (E17) |
| SQLite + sqlite-vss / externe Vector-DB | Neue Deps, wenig Reife, doppelte Suchpfade |
| FastAPI `BackgroundTasks` als einziger Worker | Keine robusten Retries; blockiert/gefährdet API |
| Zwei Editions-Repos (consumer-sqlite vs. server-pg) | Wartungslast, ADR 0004 widerspricht |
| Alles in einem Container (Supervisor) | Cosmetik; gleiche Prozesse, schlechtere Isolation/Logs |

## Referenzen

- ADR 0004: [`0004-commercial-consumer-product.md`](./0004-commercial-consumer-product.md)
- ADR 0001 (Celery/async DB): [`0001-async-engine-per-celery-task.md`](./0001-async-engine-per-celery-task.md)
- Consumer-Compose: `docker-compose.consumer.yml`, `docs/packaging.md`
- pgvector / RAG: `docs/integrations/knowledge-retrieval.md`, Epic E17
- Roadmap-Story: E9-5 in [`ROADMAP.md`](../../ROADMAP.md)
