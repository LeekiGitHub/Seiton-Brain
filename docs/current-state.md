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

Persönliches AI-Second-Brain: Capture → klassifizieren → Markdown-Vault; Retrieve
via Suche, RAG, Digest, REST, MCP. **Kein** Native-Desktop — lokale **Web-UI** +
PWA vom Always-on-Host des Kunden (ADR 0004). Buy-once, BYO-LLM-Key geplant.

**Deployment ([ADR 0008](adr/0008-deployment-models-self-hosted-first.md) — normativ):**
Self-hosting ist ein Deployment-Modell, nicht die Produktidentität. Zuerst
entwickelt und ausgeliefert wird **self-hosted**; eine **Managed Seiton Cloud**
für nicht-technische Nutzer ist ausdrücklich Teil der Produktvision, kommt aber
erst nach stabilem Core und realem Nutzerfeedback (Phase I / E24, gated auf
ADR 0007). Der Product Core bleibt derselbe Code — Unterschiede nur in
Provisionierung, Deployment, Identity, Billing, Secrets, Backup-Ops, Monitoring,
Updates, Support. Isolationsgrenze ist heute die **Instanz**; keine
Multi-Tenant-Architektur, aber auch keine irreversible Festlegung dagegen.

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

Nächstes Paket: **E45-15** Visual-Smoke-PoC (oder **E47-4** Token-Angleichung /
**E31-3** Log-Hygiene als Puffer). Designsystem:
[`docs/design-system.md`](design-system.md) (E47-3 🟢).
CodeRabbit (E45-5) ist eingerichtet — Workflow triggert Reviews unter 10 Stars
automatisch (`@coderabbitai full review`).

Offen aus G/H (Auswahl): E21-2 Verkaufskanal, E22-5/6, E23-3/4, E26-3…, E20-3/5 kein Nahziel.

## Bewusste Grenzen

Kein Desktop-App-Testing · kein breites E2E · kein Paid-Tooling vor 31.10.2026
(Ausnahme: kostenlose OSS-Pläne) · kein Linear jetzt · Jinja2 bleibt bis klarer UI-Druck.

## Agent-Hinweise

1. Relevante ROADMAP-Story lesen (aktive Datei, nicht das ganze Archiv).
2. Bei Architektur: `ARCHITECTURE.md` + passende ADRs (E45-2).
3. UI-Änderungen: [`docs/design-system.md`](design-system.md) befolgen (E47-3);
   Referenzen [`docs/ui-reference-request.md`](ui-reference-request.md);
   Ist [`docs/ui-inventory.md`](ui-inventory.md).
4. Secrets nur via `app/config.py` / `.env`. Eine Story → ein PR.
