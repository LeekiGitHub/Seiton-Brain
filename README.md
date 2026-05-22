# Seiton Brain

> *5S is a Japanese workplace methodology for creating order from chaos.*
> *Its five principles — Seiri (sort), Seiton (set in order), Seiso (shine),*
> *Seiketsu (standardize), Shitsuke (sustain) — were originally developed*
> *for factory floors, but the underlying idea applies to any system*
> *that tends toward disorder over time.*
>
> *We focus on the second S: **Seiton (整頓)** — putting everything in its place.*
> *Not just storing things, but storing them so they can actually be found*
> *and used again. A thought without a home is a thought that disappears.*

Seiton Brain is a personal AI assistant that turns your raw input — a voice
note on the go, a half-formed idea at midnight, a project thought in the
shower — into structured, linked knowledge inside your Obsidian vault.

Every feature maps directly to the Seiton principle:

| Feature | Seiton principle |
|---------|-----------------|
| Automatic categorization | Every item has a designated place |
| Linking to existing notes | Nothing exists in isolation |
| Structured Markdown + frontmatter | A consistent, findable format |
| Context-aware classification | The right place, not just any place |
| Voice input → structured note | Chaos in, order out |

---

## How it works

```
You → Telegram message or voice note
         ↓
   Webhook receives input
         ↓
   Background task starts (Telegram responds immediately)
         ↓
   Audio → Whisper transcription (if voice)
         ↓
   LLM classifies: category, title, summary, related notes
         ↓
   Entry saved to PostgreSQL
         ↓
   Markdown file written to Obsidian vault (with frontmatter + [[links]])
         ↓
   Telegram confirms: "Saved as [[My App Idea]] under Projects"
```

---

## Features

- Natural language input — text or voice via Telegram
- Automatic categorization: projects, ideas, travel, goals, notes
- Context-aware: links new input to existing notes in your vault
- Writes structured Markdown with frontmatter directly into Obsidian
- Async processing — Telegram responds immediately, processing runs in background
- Pluggable LLM: use OpenAI for quality or Ollama for full local privacy

---

## Privacy

Your Obsidian vault stays on your machine. For LLM processing you have two options:

- **OpenAI / Anthropic** — your text is sent to their API (subject to their privacy policy)
- **Ollama (local)** — everything stays on your machine, nothing leaves your network

Switch between them with one line in your `.env`:

```env
LLM_PROVIDER=openai   # or: ollama
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Pydantic v2 |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| AI | OpenAI API or Ollama (configurable) |
| Transcription | OpenAI Whisper or faster-whisper (local) |
| Queue | Celery + Redis |
| Storage | Obsidian vault (local Markdown files) |
| Infrastructure | Docker Compose |

---

## Quickstart

```bash
# 1. Clone and configure
cp .env.example .env
# Fill in: Telegram bot token, LLM provider + key, Obsidian vault path

# 2. Start everything
docker compose up

# 3. Set your Telegram webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook"

# 4. Send yourself a message and watch it appear in Obsidian
```

---

## Configuration

```env
# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...

# LLM — choose one
LLM_PROVIDER=openai          # or: ollama
OPENAI_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Obsidian — point at your personal vault, not vault.example/
OBSIDIAN_VAULT_PATH=/vault   # mount your vault as a Docker volume

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/seitonbrain
```

---

## Vault structure

Your personal vault (`vault/` locally, gitignored) is separate from the
template in `vault.example/`. Copy the example to get started:

```bash
cp -r vault.example ~/Obsidian/Seiton-Brain
# then set OBSIDIAN_VAULT_PATH to that path
```

```
vault.example/
├── School/
│   └── Example Lecture Notes.md
├── Work/
│   └── Example Project.md
├── Private/
│   └── Example Personal Note.md
├── Ideas/
│   └── Startup Concept.md
├── Travel/
│   └── Japan 2025.md
└── Notes/
    └── Random Thought.md
```

Each file includes frontmatter and Obsidian-style links:

```markdown
---
title: My App Idea
category: project
created: 2025-01-15
tags: [software, idea, mobile]
---

# My App Idea

A mobile app that tracks...

## Related
- [[Startup Concept]]
- [[Tools I Want to Build]]
```

---

## Roadmap

- [ ] v2: Semantic search over vault (RAG + pgvector) — ask questions across all your notes
- [ ] v2: Web UI for browsing and editing entries
- [ ] v3: Weekly digest — summary of everything saved this week, sent via Telegram

---

---

## Portfolio checklist

*This section is for development reference — tracking which skills are
implemented and how they map to each part of the project.*

---

### 1. API-Backend
**Projektfunktion:** Telegram Webhook empfangen, Eingaben annehmen, Antworten zurückgeben

| Tool | Beschreibung |
|------|-------------|
| FastAPI | Routen, Pydantic-Validation, OpenAPI-Doku automatisch |
| Pydantic v2 | Input/Output-Schemas für alle Endpunkte |
| Uvicorn | ASGI-Server, läuft im Docker Container |

- [ ] `POST /webhook` — Telegram-Nachrichten empfangen
- [ ] `POST /message` — Texteingabe verarbeiten
- [ ] `POST /voice` — Sprachnachricht entgegennehmen
- [ ] `GET /entries` — gespeicherte Einträge abrufen
- [ ] OpenAPI-Dokumentation erreichbar unter `/docs`

---

### 2. Datenbank
**Projektfunktion:** Notizen, Kategorien, Projekte und Verlinkungen strukturiert speichern

| Tool | Beschreibung |
|------|-------------|
| PostgreSQL | Hauptdatenbank, Beziehungen zwischen Einträgen |
| SQLAlchemy 2 | ORM, saubere Models, async-fähig |
| Alembic | Migrationen versionieren und ausführen |

- [ ] Tabellen: `entries`, `categories`, `projects`, `links`
- [ ] Indexes auf `category` und `created_at`
- [ ] Mindestens eine 1:n Beziehung (Projekt → Einträge)
- [ ] Migrationen per Alembic, kein manuelles Schema

---

### 3. Auth
**Projektfunktion:** Webhook absichern, nur autorisierte Anfragen durchlassen

| Tool | Beschreibung |
|------|-------------|
| API-Key-Auth | Header-basiert via FastAPI Depends |
| python-dotenv | Secrets aus `.env`, nie hardcoded |
| Webhook Secret | Telegram-Requests verifizieren |

- [ ] Telegram Bot Token Validierung im Webhook
- [ ] Alle Secrets in `.env`, niemals im Code
- [ ] 401-Fehler korrekt zurückgeben bei falschem Key

---

### 4. AI-Integration
**Projektfunktion:** Eingabe klassifizieren, strukturieren, kategorisieren

| Tool | Beschreibung |
|------|-------------|
| LLMProvider Interface | Austauschbar: OpenAI oder Ollama per `.env` |
| Structured Output | LLM gibt valides JSON zurück, Pydantic validiert |
| Prompt-Versioning | Prompts als `.txt` Dateien, versioniert in Git |

- [ ] `LLM_PROVIDER=openai` oder `ollama` per `.env` wählbar
- [ ] Prompt erzwingt strukturierten Output: `category`, `title`, `summary`
- [ ] Fallback wenn LLM-API nicht erreichbar
- [ ] Prompts in separatem Ordner `/prompts`, nicht inline im Code

---

### 5. Background Jobs
**Projektfunktion:** Sprachtranskription und LLM-Verarbeitung async ausführen

| Tool | Beschreibung |
|------|-------------|
| Celery | Task Queue, bewährter Standard für Python |
| Redis | Message Broker für Celery, läuft in Docker |
| Whisper / faster-whisper | Sprachtranskription im Background Task |

- [ ] Webhook gibt sofort 200 zurück, Task läuft im Hintergrund
- [ ] Task-Flow: Audio → Transkription → LLM → DB → Obsidian-Datei
- [ ] Task-Status loggbar (pending / done / failed)

---

### 6. Testing + CI
**Projektfunktion:** Webhook-Handler, LLM-Output-Parsing und DB-Queries testen

| Tool | Beschreibung |
|------|-------------|
| pytest | Unit Tests für Parser und Kategorisierungs-Logik |
| httpx + TestClient | FastAPI Endpunkte integration-testen |
| GitHub Actions | Linting + Tests bei jedem Push |

- [ ] Test für LLM-Output-Parser (LLM gemockt, kein echter API-Call)
- [ ] Test für `POST /message` Endpunkt
- [ ] Test für Obsidian-Datei-Generierung (Frontmatter korrekt?)
- [ ] GitHub Actions Workflow: ruff lint + pytest

---

### 7. Docker Compose
**Projektfunktion:** Gesamtes System lokal reproduzierbar starten

| Tool | Beschreibung |
|------|-------------|
| docker compose | api + db + redis + worker als Services |
| .env.example | Vorlage für alle Secrets |
| healthchecks | DB und Redis Readiness vor API-Start prüfen |

- [ ] `docker compose up` startet alles, keine manuellen Schritte
- [ ] Services: `api`, `worker`, `db`, `redis`
- [ ] Volumes für Postgres-Daten und Obsidian-Vault persistent
- [ ] `.env.example` vollständig, alle Keys dokumentiert
