# ADR 0001: Eigene Async-Engine pro Celery-Task

- **Status:** Accepted
- **Datum:** 2026-05-26
- **Entscheider:** Yannik
- **Phase / Epic:** Phase A · epic:infra

## Kontext

Celery-Worker laufen synchron (Prozess- oder Thread-basiert), wir nutzen aber `SQLAlchemy[asyncio]` mit `asyncpg`. Pro Task wird in `app/worker/tasks.py` mit `asyncio.run(...)` ein neuer Event-Loop gestartet.

Erster Ansatz: die globale Engine aus `app/db/session.py` (Modul-Level `create_async_engine(...)`) auch im Worker verwenden.

Problem: Sobald derselbe Worker-Prozess **zwei** Tasks hintereinander ausführt, hängt die zweite Verbindung. Ursache: `asyncpg`-Connections sind an den Event-Loop gebunden, in dem sie erstellt wurden — der erste `asyncio.run()`-Loop ist beim zweiten Task aber bereits geschlossen.

Symptom: erste Telegram-Nachricht wird verarbeitet, jede weitere bleibt stumm bis Worker-Restart.

## Entscheidung

In Celery-Tasks **immer** `worker_session()` verwenden — ein Async-Context-Manager, der pro Task eine **frische** Engine erzeugt und am Ende explizit `dispose()`-t.

```python
@asynccontextmanager
async def worker_session():
    task_engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(task_engine, ...)
    try:
        async with session_factory() as session:
            yield session
    finally:
        await task_engine.dispose()
```

API-Routen behalten die globale Engine (`get_db()`), weil dort ein FastAPI-eigener Event-Loop läuft, der über die gesamte App-Lebensdauer gleich bleibt.

## Konsequenzen

### Positiv
- Tasks funktionieren zuverlässig auch bei mehrfacher Ausführung
- Klarer Lebenszyklus: Engine entsteht und stirbt mit dem Task
- API-Performance unverändert (Connection-Pool dort weiter aktiv)

### Negativ / Trade-offs
- Connection-Pool im Worker bringt nichts (jeder Task baut neu auf) — bei hohem Durchsatz Performance-Kosten
- Zwei DB-Patterns nebeneinander (`get_db` vs `worker_session`) → leichte Code-Duplizierung in `db/session.py`

### Folgearbeiten
- Wenn Durchsatz mal wirklich relevant wird: synchronen DB-Treiber im Worker erwägen (`psycopg`) oder Celery-eigene Lifecycle-Hooks für Engine-Reuse pro Worker-Prozess

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|-------------|--------------|
| Globale Engine im Worker wiederverwenden | Event-Loop-Konflikt, Tasks hängen ab dem zweiten Aufruf |
| Synchroner SQLAlchemy-Treiber im Worker | Würde funktionieren, aber zweites Stack-Profil (sync ORM) parallel zum Rest pflegen → mehr Komplexität |
| `arq` statt Celery | Async-natives Task-Queue-System; verworfen, weil Celery-Ökosystem reifer und Lerngewinn hier wichtiger |

## Referenzen

- Code: `app/db/session.py:17-28`
- Verwendet in: `app/worker/tasks.py:14-18`
