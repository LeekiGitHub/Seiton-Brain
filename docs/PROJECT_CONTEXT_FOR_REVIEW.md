# Seiton Brain — Projektkontext für externe Zweitmeinung

Kompakter Überblick für einen externen technischen Berater ohne Repo-Zugriff.
Stand **2026-08-29**, Version **v0.3.0**. Keine Secrets, keine personenbezogenen Daten.

---

## Product

**Was es ist:** Ein self-hosted „Second Brain". Der Nutzer schickt einen Gedanken
(Telegram-Text/Sprachnachricht, Web-UI, REST, MCP); ein LLM entscheidet Kategorie,
Titel, Tags und ob eine bestehende Notiz ergänzt oder eine neue angelegt wird.
Ergebnis ist eine Markdown-Datei in einem Obsidian-kompatiblen Vault. Die zweite
Produkthälfte ist Retrieval: semantische Suche, RAG-Antworten (`/ask`), Digest,
REST-API und ein MCP-Server für Cursor/Claude.

**Was heute funktioniert:** Capture-Pipeline (Text, Sprache via Whisper, Fotos,
PDF/Office mit OCR/Vision), Klassifikation, Vault-Schreiben mit File-Locks und
Kompensationslogik, inkrementeller Index-Sync gegen externe Obsidian-Edits,
Keyword- + Vektorsuche (pgvector), RAG, Digest, Web-UI mit Auth, PWA, Backup/
Restore, Offline-Lizenzprüfung (Ed25519), Setup-Wizard, Installer-Skripte,
Outbound-Webhooks.

**Langfristig:** kaufbares Consumer-Produkt (einmal kaufen, Kunde hostet selbst,
eigener LLM-Key). Privacy ist das Verkaufsargument: Daten verlassen die Maschine
des Kunden nur, soweit der Nutzer einen Cloud-LLM wählt (Ollama/whisper.cpp als
lokale Alternative vorhanden). Später optional Cloud-Edition mit Abo (ADR 0007,
noch „Proposed") und Team-Funktionen für kleine Gruppen.

**Desktop/Web/Mobile-Strategie (wichtig, häufig missverstanden):**
Es gibt **keine** Desktop-Anwendung und keine native App. Alles Sichtbare ist eine
lokale **Web-UI**, die vom Always-on-Host des Kunden (Mac Mini, Mini-PC, NAS,
optional VPS) im Browser ausgeliefert wird. Mobile = **PWA**. Eine native
Desktop-App ist explizit kein Nahziel (ADR 0004).

**Entwicklungsstand:** Kernpipeline und Retrieval sind fertig und getestet. Aktuell
läuft „Launch-Härtung" (Security, Datenintegrität, UX, Privacy) vor der
Monetarisierung. Es gibt noch keinen Verkaufskanal und keine zahlenden Nutzer.

---

## Tech Stack

| Bereich | Technologie |
|---------|-------------|
| Backend | Python 3.14, FastAPI, Pydantic/pydantic-settings |
| Async-Jobs | Celery + Redis |
| Datenbank | PostgreSQL 16 + **pgvector**, SQLAlchemy (async), Alembic |
| LLM | OpenAI (Chat, Whisper, Embeddings), optional Ollama / whisper.cpp lokal |
| Frontend | **Jinja2-Templates + Vanilla JS + handgeschriebenes CSS** — kein React/Vue, kein UI-Framework, kein Build-Step, kein Node im Repo |
| PWA | Manifest + Service Worker |
| Deployment | Docker Compose (Varianten: dev, `consumer`, `vps`), self-hosted |
| Installer | `scripts/install.sh` (macOS/Linux) + `install.ps1` (Windows): Vault anlegen, `.env` erzeugen, Compose starten, Migrationen, Browser zum Setup-Wizard. Kein GUI-Installer, keine Code-Signierung |
| Lizenzierung | Offline-Validierung mit Ed25519-Signatur |
| Testing | pytest (+pytest-asyncio), FastAPI-TestClient, alles offline; **keine** Browser-Tests |
| Lint | Ruff (gepinnt 0.15.x) |
| CI | GitHub Actions |

Abhängigkeiten sind gepinnt; Lizenzen permissiv (MIT/BSD/Apache).

---

## Repository

Öffentlich auf GitHub, MIT-Lizenz, ein Maintainer, 0 Stars, ~1 MB.

```
app/
  telegram/    Webhook, Long-Polling, Slash-Commands
  worker/      Celery-Tasks (capture, voice, ask, digest, index-sync)
  llm/         Provider-Abstraktion, Embeddings, Schemas
  services/    process_message, answer, digest
  vault/       Backend-Protocol, Filesystem, Reader/Writer, Index (Keyword+Semantik), Pfad-Sicherheit
  api/v1/      REST (capture, ask, digest, search, …)
  ui/          Jinja2-Templates, statische Assets, UI-APIs
  setup/       Setup-Wizard, Env-Checks
  licensing/   Ed25519-Lizenzprüfung
  webhooks/    Outbound-Events
alembic/       Migrationen
examples/mcp/  MCP-Server für Cursor/Claude
prompts/       versionierte LLM-Prompts
scripts/       install, init, doctor, backup, update, deploy-vps
tests/         66 Testdateien, ~561 Tests
docs/          27 Dokumente inkl. 7 ADRs und 4 Audit-Berichte
```

**Wichtige Dokumente:** `ROADMAP.md` (zentrale Planung), `ARCHITECTURE.md`
(teils veraltet, Fix als E29-5 eingeplant), `CHANGELOG.md`, `docs/adr/0001–0007`,
`docs/engineering.md` (Entwicklungsprozess), `docs/production-ops.md` (Betrieb),
`SECURITY.md` (Threat Model), `.cursor/rules/` (Agent-Instruktionen).

---

## Development Workflow

Ein Entwickler, stark unterstützt durch Cursor/KI-Agenten. Rhythmus: **ein klar
abgegrenztes Arbeitspaket pro Tag**.

```
ROADMAP-Story → Agent analysiert → Feature-Branch → Implementierung + Tests
→ Commit (Conventional Commits) → Push → PR → CI → Mensch merged auf GitHub
```

- **Branches:** `feat/…`, `fix/…`, `chore/…`, `docs/…`; eine Story = ein PR.
  `main` ist per Ruleset geschützt (PR + CI). Head-Branches werden nach Merge
  gelöscht. Kein `develop`/`staging`/`production`.
- **GitHub Issues:** existieren mit Templates, werden faktisch seit Juni 2026 nicht
  mehr genutzt — die ROADMAP ist der Ticket-Ersatz
- **CI (3 Jobs, Push + PR auf `main`):** `pip-audit` → `ruff` → `pytest` →
  MCP-Client-Tests · `docker build` · Alembic `upgrade head` gegen echten
  pgvector-Service-Container + Vector-Smoke-Insert
- **Dependabot:** wöchentlich Patch/Minor gruppiert; **Security Updates** aktiv;
  CodeQL Default Setup aktiv
- **Agent-Regeln:** zwei Cursor-Rules (Projektkontext + „stille" Guardrails zu
  Config/Secrets, Lizenzen, DSGVO, Wartbarkeit); kein `AGENTS.md`

**Bekannte Prozesslücken:** kein unabhängiges Code-Review (als Nächstes CodeRabbit),
kein Type-Checking, kein Staging/Preview, keine Browser-/UI-Prüfung.

---

## UI/UX

**Vorhandene Screens (7 Templates):** `login`, `setup` (mehrstufiger Wizard),
`dashboard` (letzte Captures + Schnell-Capture), `ask` (Suche + RAG-Antwort +
Digest), `notes` (Liste, Ansicht, Bearbeiten, Löschen, Upload), `settings`
(Konfiguration, Backup/Restore, Reindex), plus `base` mit Topnav.

**Geplant:** Notiz-Lesemodus mit Markdown-Preview, Toast/Modal-Feedback-Layer,
Empty-States, Mobile-Politur/A11y, Ask-Verlauf, Integrations-Karte (Epic E30);
später Knowledge-Chat (E40) und Team-Ansichten (Phase O).

**Designsystem:** existiert nicht als Dokument. Es gibt CSS-Custom-Properties in
`app/ui/static/app.css` (609 Zeilen) — Dark-Theme-Farben, ein Radius, semantische
Status-Farben. Keine Typo-/Spacing-Skala, kein Komponentenkatalog, keine
verbindlichen Regeln für Agenten. Eine zweite, separate `setup.css` existiert.

**UI-Libraries:** keine. Bewusst kein Framework bei dieser UI-Größe.

**Visueller Reifegrad:** funktional und aufgeräumt, aber implementierungsgetrieben
gewachsen — jede Story hat ihren Screen mitgebracht. Ein UI-Audit hat u. a.
`alert()`/`confirm()` statt Toasts, gemischte Sprachebenen (technische Rohwerte in
der Oberfläche), fehlende Empty-States und schwaches Mobile-Verhalten benannt.
Der Maintainer hat die Anwendung bisher kaum selbst visuell geprüft.

---

## Current Quality / Security

**Vorhanden:** ~561 Tests (Unit, API, UI-Regression, Doku-Konsistenz, Shell-Syntax);
Ruff; `pip-audit` in CI; Docker-Build und Migrations-Smoke in CI; Secret Scanning
**und** Push Protection; Dependabot Security Updates; CodeQL Default Setup;
Ruleset *Protect main* (PR + required CI); `SECURITY.md` mit Threat Model und
privatem Meldeweg; API-Key-Auth; Session-Auth für die UI; proxy-sichere
localhost-Guards für `/setup` und `/docs`; XSS-Härtung mit Regressionstest;
Pfad-Traversal-Schutz für Vault-Pfade; File-Locks und Kompensation im Schreibpfad;
gepinnte Dependencies.

**Bekannte Lücken:**
- Kein Type-Checking (mypy/pyright)
- Rate-Limits/Brute-Force-Schutz noch offen (eingeplant als E27-5)
- Keine Browser-/Visual-Prüfung, kein Integrationstest mit Redis/Celery in CI
- Kein Monitoring/Error-Tracking (vor Verkauf eingeplant)
- DSGVO-Basis (Voll-Löschung, Export, Log-Hygiene) noch offen
- `ARCHITECTURE.md` veraltet
- Unabhängiges PR-Review (CodeRabbit, E45-5) noch nicht eingerichtet

---

## Roadmap

**Aktuelle Phase: L — Launch-Härtung.** Bedingungen aus einem Produkt-Readiness-Audit
(„GO WITH CONDITIONS") vor jeder Monetarisierung: Security (E27), Datenintegrität
(E28), Release/Ops (E29), UX-Pass (E30), Privacy (E31). Parallel laufen die
Cross-Cutting-Epics E45 (Engineering) und E46 (Production Operations).

Größe: 210 Stories über 47 Epics, davon 144 abgeschlossen. Spätere Phasen sind
bereits geschnitten: M (Interoperabilität), N (Privacy-First Knowledge AI),
O (kleine Teams), I (Cloud/Abo, gated).

**Nächste ~9 Arbeitspakete (je ≈ ein Tag), Stand 2026-08-30:**

1. ~~**E45-13**~~ Roadmap-Hygiene 🟢
2. ~~**E45-1 + E45-4**~~ Branch Protection + GitHub-Security 🟢
3. **E45-5** CodeRabbit einrichten (Open-Source-Plan, kostenlos)
4. **E47-1 + E47-2** UI-Inventar, dann **STOP**: UI-Referenzen vom Entwickler
5. **E45-15** Visual-Smoke-PoC mit `pytest-playwright` (ein Happy-Path + Screenshots)
6. **E45-14** risikobasierte Definition of Done
7. **E31-3 / E31-1** Log-Hygiene und Voll-Löschung (Produktarbeit als Puffer)
8. **E47-3** Designsystem aus den Referenzen ableiten (`docs/design-system.md`)
9. **E30-4 → E30-2 → E30-5/6** UX-Pass auf gemeinsamer Designsprache

Danach: restliche E29-Stories, E27-5, E46 (Monitoring/Backup/Rollback) vor dem
Verkaufskanal E21-2, dann Phase M.

**Wo Engineering-/Quality-/UI-Arbeit eingeordnet wurde:** Engineering-Themen liegen
im Epic E45 und laufen parallel zur Produktarbeit, ohne Phase L zu blockieren.
Betriebsthemen (Monitoring, Backups, Incidents, Rollback, Hotfix, Migrationen) sind
Epic E46 und an konkrete Gates gebunden („vor Beta", „vor Launch", „vor Verkauf").
UI/UX-Grundlagen sind das neue Epic E47 innerhalb von Phase L, bewusst **vor** den
verbleibenden E30-Stories.

**Budgetregel:** bis 31.10.2026 keine neuen laufenden Kosten. Priorität: vorhandene
Tools → GitHub-eigene Funktionen → Open Source → Free Tiers → bessere Prozesse.
Ausnahme: dauerhaft kostenlose Angebote für öffentliche Repos (CodeRabbit OSS-Plan).

---

## Open Questions

Fragen, bei denen eine externe Einschätzung wirklich hilft:

1. **Reihenfolge Härtung vs. Markt:** Das Produkt ist funktional weit, hat aber
   null Nutzer außer dem Entwickler. Ist es richtig, erst E27–E31 + E45–E47
   abzuschließen — oder wäre ein früher Beta-Test mit 3–5 echten Nutzern der
   bessere Reality-Check, auch auf unfertiger Basis?
2. **Self-Hosted-Zielgruppe:** „Consumer, der Docker auf einem Always-on-Rechner
   betreibt" ist eine schmale Schnittmenge. Ist Buy-once-Self-Hosted tragfähig,
   oder führt der Weg realistisch doch zur Cloud-Edition (ADR 0007)?
3. **UI-Stack:** Reicht Jinja2 + Vanilla JS für die geplanten Screens
   (Lesemodus mit Markdown-Preview, Knowledge-Chat, Team-Ansichten) — oder ist ein
   Wechsel jetzt billiger als in zwölf Monaten?
4. **Roadmap-Weite:** Vier Phasen (M/N/O + Cloud) sind bereits detailliert geplant,
   bevor Phase L fertig ist. Ist das nützliche Vorausschau oder gebundene Kapazität?
5. **Testtiefe:** ~561 Tests ohne jede Browser-Prüfung. Ist der geplante schmale
   Visual-Smoke die richtige Dosis, oder ist das für ein UI-Produkt zu wenig?
6. **Vier Audit-Berichte** (~100 KB) treiben die Epics E27–E44. Ist das ein
   gesunder Planungsvorlauf oder Analyse-Übergewicht für einen Solo-Entwickler?

---

## Recommendations from Cursor

Punkte, an denen wir bewusst von gängigen Empfehlungen abweichen:

- **Kein neues Ticketsystem (Linear).** GitHub-Issues werden nicht einmal
  ausgereizt; ein weiteres Tool erzeugt Pflegeaufwand ohne gelöstes Problem.
- **Kein breites E2E-Framework.** Der Nutzen liegt fast vollständig in „Seite lädt,
  keine Console-Errors, Screenshot plausibel". Ein Happy-Path genügt; ein
  Regressionsnetz kostet mehr Pflege, als es einem Solo-Entwickler zurückgibt.
- **Kein Desktop-/Installer-UI-Testing.** Es gibt keine Desktop-App; der Installer
  ist ein Shell-Skript. Skript-Syntax-Checks plus `doctor.sh` decken das ab.
- **Screenshot-Analyse durch einen Agenten wird nicht überverkauft.** Cursor kann
  PNGs lesen und grobe Fehler benennen, ist aber kein Pixel-Diff und kein
  Geschmacksurteil. Der Zwei-Minuten-Handcheck des Menschen bleibt Teil der DoD.
- **Designsystem vor weiterem UI-Ausbau, aber ohne Redesign.** Erst Inventar und
  Referenzen des Entwicklers, dann Tokens und Regeln; die Umsetzung passiert
  inkrementell in den Stories, die den Screen ohnehin anfassen.
- **Kontext-Hygiene zuerst.** Zwei Drittel der ROADMAP sind Historie. Das
  aufzuräumen ist die einzige Maßnahme, die jeden folgenden Arbeitstag günstiger
  macht — deshalb steht sie vor allem anderen.
- **CodeRabbit bleibt beratend.** Es wird nie Merge-Voraussetzung; Ruff, pytest,
  pip-audit, Docker-Build und Migrations-Smoke bleiben die harten Gates.
