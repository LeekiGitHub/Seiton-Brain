# Seiton Brain

Ziel:

Ich schreibe dem Bot eine Nachricht — eine halbe Idee, ein Gedanke unterwegs, irgendwas das sonst in einer Notiz-App vergessen würde. Das LLM sortiert es ein, legt eine Markdown-Datei in meinem Obsidian-Vault ab und schickt mir eine kurze Bestätigung zurück. Fertig.

Der Name kommt von **Seiton** (整頓) — alles an seinen Platz legen, damit man es wiederfindet. Genau das soll das Projekt für meine Gedanken machen.

---

## Warum das existiert

Ich verliere ständig Ideen, weil ich sie irgendwo hinmurmle und nie wieder draufschaue. Obsidian nutze ich schon — aber der Schritt von „roher Input" zu „ordentliche Notiz" ist mir zu oft zu viel Aufwand.

Seiton Brain soll diesen Schritt wegnehmen. Gleichzeitig ist es für mich kein Tutorial-Projekt, das nach zwei Wochen in der Ecke liegt. Ich baue etwas, das ich wirklich nutzen will.

---

## Was schon läuft

Stand jetzt (v0.1.0):

- Telegram-Bot: Text **und** Sprachnachrichten über Webhook
- Sofortige Antwort, Verarbeitung async via Celery + Redis
- OpenAI klassifiziert (Kategorie, Titel, Summary) — Prompt in `/prompts`
- OpenAI Whisper transkribiert Voice
- PostgreSQL + Alembic, Obsidian-Vault mit `[[links]]` zu bestehenden Notizen
- Docker Compose (api, worker, db, redis), pytest + GitHub CI

Vollständige Historie: [`CHANGELOG.md`](./CHANGELOG.md).
Was als nächstes kommt: [`ROADMAP.md`](./ROADMAP.md).
Langfristige Integrations-Ideen (n8n, REST-API, Setup-CLI): [`docs/integrations/`](./docs/integrations/).
Wie es gebaut ist: [`ARCHITECTURE.md`](./ARCHITECTURE.md).
Wie selbst betreiben: [`docs/setup.md`](./docs/setup.md).

---

## Was ich damit lernen wollte

Das Projekt ist absichtlich so aufgebaut, dass ich Backend- und AI-Themen nicht nur lese, sondern anfasse:

- **API-Design** — FastAPI, Routen, Request-Handling
- **Webhooks** — externe Services (Telegram) anbinden, absichern, schnell antworten
- **Datenbank** — Postgres, async SQLAlchemy, Migrationen mit Alembic
- **LLM-Anbindung** — strukturierter Output, Prompts versionieren, Provider austauschbar halten
- **Automatisierung** — Input rein, Verarbeitung, Output raus, ohne manuell was anklicken zu müssen
- **Infrastruktur** — Docker Compose, Services sauber starten, Volumes, Env-Variablen

Ich wollte ein System bauen, das sich wie ein kleines echtes Backend anfühlt — nicht wie fünf lose Skripte.

---

## Was noch fehlt (v2)

- Ollama als lokale LLM-Alternative
- Semantic Search über den Vault (RAG + pgvector)
- Web-UI zum Durchsuchen
- Weekly Digest per Telegram

---

## Hinweis

`vault.example/` ist nur eine Vorlage für die Ordnerstruktur. Mein echter Vault liegt lokal und ist nicht im Repo.

Setup-Details: [`docs/setup.md`](./docs/setup.md).

---

# English

Goal:

I send the bot a message — half an idea, a thought on the go, something that would otherwise get lost in a notes app. The LLM sorts it, writes a Markdown file into my Obsidian vault, and sends me a short confirmation. Done.

The name comes from **Seiton** (整頓) — putting everything in its place so you can actually find it again. That's what this project is supposed to do for my thoughts.

---

## Why this exists

I keep losing ideas because I mumble them somewhere and never look at them again. I already use Obsidian — but going from raw input to a proper note is often too much effort for me.

Seiton Brain is meant to remove that step. At the same time, this isn't a tutorial project that sits in a corner after two weeks. I'm building something I actually want to use.

---

## What works already

v0.1.0:

- Telegram bot: text **and** voice via webhook
- Immediate reply, async processing via Celery + Redis
- OpenAI classification — prompt in `/prompts`
- OpenAI Whisper for voice transcription
- PostgreSQL + Alembic, Obsidian vault with `[[links]]` to related notes
- Docker Compose (api, worker, db, redis), pytest + GitHub CI

Full history: [`CHANGELOG.md`](./CHANGELOG.md).
What's next: [`ROADMAP.md`](./ROADMAP.md).
Long-term integrations (n8n, REST API, setup CLI): [`docs/integrations/`](./docs/integrations/).
How it's built: [`ARCHITECTURE.md`](./ARCHITECTURE.md).
How to self-host: [`docs/setup.md`](./docs/setup.md).

---

## What I wanted to learn

The project is deliberately set up so I don't just read about backend and AI topics — I actually touch them:

- **API design** — FastAPI, routes, request handling
- **Webhooks** — connecting external services (Telegram), securing them, responding fast
- **Database** — Postgres, async SQLAlchemy, migrations with Alembic
- **LLM integration** — structured output, versioning prompts, keeping providers swappable
- **Automation** — input in, processing, output out, without manually clicking through things
- **Infrastructure** — Docker Compose, starting services cleanly, volumes, env variables

I wanted to build something that feels like a small real backend — not five loose scripts.

---

## What's still missing (v2)

- Ollama as a local LLM alternative
- Semantic search over the vault (RAG + pgvector)
- Web UI for browsing
- Weekly digest via Telegram

---

## Note

`vault.example/` is just a template for the folder structure. My actual vault lives locally and is not in the repo.

Setup details: [`docs/setup.md`](./docs/setup.md).
