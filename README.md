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

Stand jetzt ist der Kern da:

- Telegram-Bot empfängt Textnachrichten über einen Webhook
- FastAPI-Backend prüft das Webhook-Secret und antwortet direkt
- OpenAI klassifiziert den Text (Kategorie, Titel, Zusammenfassung) — Prompt liegt als Datei in `/prompts`
- Eintrag landet in PostgreSQL (SQLAlchemy + Alembic)
- Eine `.md`-Datei wird in meinen Obsidian-Vault geschrieben (School, Work, Private, Ideas, …)
- Alles läuft lokal in Docker (API + Datenbank)

Wenn ich unterwegs eine Idee habe, landet sie tatsächlich im Vault. Das funktioniert schon.

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

## Was noch fehlt

Das Projekt ist aktiv in Arbeit. Geplant bzw. als Nächstes gedacht:

- Sprachnachrichten (Whisper) und Verarbeitung im Hintergrund (Celery + Redis)
- Ollama als lokale LLM-Alternative
- Notizen mit bestehenden Vault-Dateien verknüpfen
- Semantic Search über den Vault (RAG + pgvector)
- Web-UI zum Durchsuchen
- Weekly Digest per Telegram
- Tests und CI

Manche Sachen aus der ursprünglichen Idee sind schon da, manches kommt noch. Die README wird mitwachsen.

---

## Hinweis

`vault.example/` ist nur eine Vorlage für die Ordnerstruktur. Mein echter Vault liegt lokal und ist nicht im Repo.

Wenn du Setup-Details brauchst: `.env.example` und `docker compose up` — mehr Dokumentation kommt später, wenn das Projekt stabiler ist.

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

As of now, the core is in place:

- Telegram bot receives text messages via a webhook
- FastAPI backend validates the webhook secret and responds immediately
- OpenAI classifies the text (category, title, summary) — prompt lives as a file in `/prompts`
- Entry gets saved to PostgreSQL (SQLAlchemy + Alembic)
- A `.md` file is written to my Obsidian vault (School, Work, Private, Ideas, …)
- Everything runs locally in Docker (API + database)

When I have an idea on the go, it actually ends up in the vault. That part works.

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

## What's still missing

The project is actively in progress. Planned or up next:

- Voice messages (Whisper) and background processing (Celery + Redis)
- Ollama as a local LLM alternative
- Linking notes to existing vault files
- Semantic search over the vault (RAG + pgvector)
- Web UI for browsing
- Weekly digest via Telegram
- Tests and CI

Some things from the original idea are already there, some are still coming. This README will grow with the project.

---

## Note

`vault.example/` is just a template for the folder structure. My actual vault lives locally and is not in the repo.

If you need setup details: `.env.example` and `docker compose up` — more documentation will come later once the project is more stable.
