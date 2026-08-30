# Current State — Seiton Brain

Kurzer Einstieg für Agents und Menschen. Stand **2026-08-30**, Release **v0.3.0**.

| Frage | Ort |
|-------|-----|
| Was als Nächstes? | [`ROADMAP.md`](../ROADMAP.md) |
| Wie/warum gebaut? | [`ARCHITECTURE.md`](../ARCHITECTURE.md), [`docs/adr/`](adr/) |
| Was wurde geliefert? | Git, [`CHANGELOG.md`](../CHANGELOG.md) |
| Erledigte Phasen A–H | [`docs/archive/roadmap-phases-a-h.md`](archive/roadmap-phases-a-h.md) |
| Geplante Phasen M–O | [`docs/roadmap-phases-m-o.md`](roadmap-phases-m-o.md) |
| Engineering / Ops | [`engineering.md`](engineering.md), [`production-ops.md`](production-ops.md) |

---

## Produkt

Self-hosted Second Brain: Capture → klassifizieren → Markdown-Vault; Retrieve via
Suche, RAG, Digest, REST, MCP. **Kein** Native-Desktop — lokale **Web-UI** + PWA
vom Always-on-Host des Kunden (ADR 0004). Buy-once, BYO-LLM-Key geplant.

## Stack

FastAPI · Postgres 16 + pgvector · SQLAlchemy async · Alembic · Celery + Redis ·
OpenAI (optional Ollama / whisper.cpp) · Jinja2 + Vanilla JS · Docker Compose ·
Installer: `scripts/install.sh` / `install.ps1`

## Was steht

- Capture-Pipeline (Text, Voice, Foto/PDF/Office), Index-Sync, RAG, Digest
- Web-UI: Setup, Dashboard, Ask, Notes, Settings, Login, Auth, PWA, Backup-UI
- REST + MCP + Webhooks; Offline-Lizenz (Ed25519); Packaging Consumer/VPS
- ~561 Tests; CI: ruff, pytest, pip-audit, docker build, Alembic+pgvector-Smoke
- Phase-L-Kern Security/Integrität/Release/Onboarding weitgehend 🟢

## Aktiv / als Nächstes

**Phase L** (Launch-Härtung) + parallel **E45** Engineering.

Nächstes Paket: **E45-5** CodeRabbit (OSS-Plan, kostenlos), danach **E47**
UI-Inventar (**STOP** für Design-Referenzen).

Offen aus G/H (Auswahl): E21-2 Verkaufskanal, E22-5/6, E23-3/4, E26-3…, E20-3/5 kein Nahziel.

## Bewusste Grenzen

Kein Desktop-App-Testing · kein breites E2E · kein Paid-Tooling vor 31.10.2026
(Ausnahme: kostenlose OSS-Pläne) · kein Linear jetzt · Jinja2 bleibt bis klarer UI-Druck.

## Agent-Hinweise

1. Relevante ROADMAP-Story lesen (aktive Datei, nicht das ganze Archiv).
2. Bei Architektur: `ARCHITECTURE.md` + passende ADRs (E45-2).
3. UI-Änderungen: bis E47-3 kein eigenmächtiges Redesign; nach E47-3 Designsystem befolgen.
4. Secrets nur via `app/config.py` / `.env`. Eine Story → ein PR.
