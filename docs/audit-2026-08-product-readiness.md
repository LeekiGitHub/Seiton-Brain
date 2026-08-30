# Product Readiness & Optimization Audit — August 2026

> **Klassifikation: HISTORISCH** (Snapshot August 2026). Nicht als geltende
> Entscheidung lesen. Aktuelle Wahrheit: [`docs/current-state.md`](current-state.md)
> und [`docs/adr/`](adr/) — für Produktidentität und Deployment insbesondere
> [ADR 0008](adr/0008-deployment-models-self-hosted-first.md).

Vollständiger Review vor Hosting/Cloud, Monetarisierung und Go-to-Market.
Basis: Ist-Code auf `main` (Stand nach PR #125, 505 Tests), vier vertiefte
Teil-Audits (Architektur/Backend, Security/Privacy, UI/UX, Tests/Ops/Doku)
plus Markt-Recherche. Kein Produktivcode wurde geändert.

> **Ergebnis in einem Satz:** Die Engine ist solide und breit getestet, aber
> es gibt **einen kritischen Security-Befund (Localhost-Guard hinter
> Reverse-Proxy wirkungslos)**, eine Handvoll Launch-Blocker in Security/
> Datenintegrität sowie eine klare Consumer-Lücke im UI — alles behebbar in
> überschaubaren Story-Paketen (→ neue Epics E27–E31 in der ROADMAP).
>
> **Empfehlung: GO WITH CONDITIONS** (Details am Ende).

---

## Executive Summary

**Stärken (verifiziert im Code):**

- Klare Architektur: Adapter (Telegram/UI/REST/MCP) → Worker/Services →
  Vault als Source of Truth → Postgres nur als Index/Audit-Log. Atomare
  Vault-Writes, Telegram-Idempotenz über UNIQUE `telegram_update_id`,
  Celery-Retries mit Backoff, timing-safe API-Key-Vergleich, Non-root-Image,
  Path-Traversal-Schutz an den UI/API-Lesepfaden.
- 505 disziplinierte Offline-Tests + Ruff-Gate in CI; saubere PR-/CHANGELOG-
  Hygiene; Feature-Doku aktuell.
- Funktional fast vollständige Capture-Pipeline (Text, Voice, Foto, Dokument,
  UI, REST, MCP) plus Retrieval (Suche, RAG, Digest) und Ops-Grundlagen
  (Setup-Wizard, Backup-UI, Lizenz, PWA, UI-Auth).

**Schwächen (nach Gewicht):**

1. **Security-Annahme „localhost = vertrauenswürdig" bricht hinter dem
   dokumentierten Reverse-Proxy** — `/setup` (schreibt Secrets in `.env`)
   und die ganze UI sind auf dem dokumentierten VPS-Pfad remote erreichbar.
2. **Stored XSS im Dashboard** (Titel/Pfade ungeescaped in `innerHTML`).
3. **Disk/DB-Konsistenz:** Vault wird vor der DB geschrieben, ohne
   Kompensation; parallele Captures können Orphans/Doppelnotizen erzeugen;
   Create/Append ohne File-Locks; REST/UI-Captures ohne Idempotenz.
4. **Index-Drift:** Externe Obsidian-Edits landen nie im Index (Full-Sync nur
   bei leerem Index; kein inkrementeller Sync, kein Reindex-Button).
5. **UI ist ein sehr fähiges Power-User-Tool, kein Consumer-Produkt:** kein
   Onboarding nach Setup, Suchtreffer nicht klickbar, Notizen nur als
   Roh-Markdown, `alert()`-Fehler, englische API-Meldungen, Env-Variablen als
   Formular-Labels.
6. **Ops-Lücken vor kommerziellem Betrieb:** ungepinnte Dependencies, kein
   Docker-/Migrations-Test in CI, kein Release seit 0.2.0, Backups ohne
   Retention, kein Restore-Test, README/ARCHITECTURE stark veraltet.
7. **DSGVO-Basis unvollständig:** keine Voll-Löschung, kein strukturierter
   Export, PII in Logs (Transkript-Snippets), Voice-Cache/Backups ohne TTL.

---

## Top 10 Findings

| # | Finding | Kategorie | Severity | Aufwand |
|---|---------|-----------|----------|---------|
| 1 | Localhost-Guard hinter Reverse-Proxy wirkungslos (`request.client.host` = Proxy-IP); Caddy/nginx-Beispiele proxyen alles → `/setup`, UI, `/docs` remote offen | Security | **P0** | S |
| 2 | Stored XSS: `dashboard.js` rendert `title`, `folder`, `vault_path`, `err.message` ohne `escapeHtml` (`login.js`/`setup.js` latent) | Security | **P0/P1** | XS |
| 3 | Capture: Vault-Write vor DB-Commit ohne Kompensation; parallele Tasks → Orphan-Dateien/Doppelnotizen; keine File-Locks bei Create/Append | Datenintegrität | **P1** | M |
| 4 | Index-Drift: externe Vault-Edits werden nie nachindexiert (kein inkrementeller Sync, kein Reindex-Trigger) — Suche/RAG liefern stale Ergebnisse | Produkt/Daten | **P1** | M |
| 5 | Ungepinnte Prod-Dependencies (`requirements.txt` komplett ohne Versionen) + Python 3.14-slim; kein Dependabot/Audit | Ops | **P1** | S |
| 6 | Kein UI-Loop-Schluss: Suchtreffer/Ask-Quellen nicht klickbar, Notes ohne Markdown-Preview/Wikilinks, `alert()`-Fehler, EN-Fehlertexte | UX | **P1** | M |
| 7 | Unsichere Remote-Defaults: Compose bindet `0.0.0.0:8000`, Session-Cookie ohne `Secure`, Telegram-Allowlist default leer, kein Rate-Limit auf Login//v1 | Security | **P1** | S |
| 8 | Keine Voll-Löschung / kein strukturierter Datenexport (DSGVO Art. 17/20-Basis); PII in Logs; Voice-Cache & Backups ohne Retention | Privacy | **P1** | M |
| 9 | CI testet weder Docker-Build noch Alembic-Migrationen gegen echte pgvector-DB; Backup-Restore nie als Roundtrip verifiziert; kein Release/Tag seit 0.2.0 | Ops/QA | **P1** | M |
| 10 | Frontmatter-Injection: `title:`/Tags landen roh im YAML (Newline/`---` zerstören Notizstruktur); `resolve_vault_file` mit `startswith` ohne Separator; Append umgeht `resolve_vault_file` | Security/Integrität | **P2** | S |

## Launch Blocker (vor zahlenden Kunden zwingend)

1. **Proxy-sichere Zugriffskontrolle** (Finding 1) — Setup/OpenAPI dürfen
   remote nie erreichbar sein; UI remote nur mit `UI_PASSWORD`. Lösung:
   Guard härten (Trusted-Proxy-Konzept) **und** Deploy-Beispiele so ändern,
   dass `/setup` + `/docs` nicht durch den Proxy laufen.
2. **XSS-Fixes** (Finding 2) — zentrales Escaping, alle `innerHTML`-Stellen.
3. **Sichere Defaults** (Finding 7) — `127.0.0.1`-Bind im Standard-Compose,
   `Secure`-Cookie hinter TLS, Setup-Wizard erzwingt/empfiehlt Allowlist,
   Rate-Limit auf Login und `/v1`.
4. **Capture-Konsistenz** (Finding 3) — mindestens: File-Locks, Orphan-
   Vermeidung, Idempotency-Key für REST/UI.
5. **Dependencies pinnen + CI-Härtung** (Findings 5, 9) — reproduzierbare
   Builds, Migrations-/Docker-Job, ein echter Release-Schnitt (v0.3.0).
6. **Löschung & Export** (Finding 8) — ohne DSGVO-Basisfunktionen kein
   kommerzieller Betrieb in DE/EU.

## High-Impact Improvements (größter Produktnutzen)

- **Retrieval-Loop schließen:** Suchtreffer/Quellen → Notiz öffnen
  (Deep-Link), Markdown-Preview mit klickbaren `[[Wikilinks]]`, Editor als
  Zweitmodus. Das ist die Kern-Journey „wiederfinden → lesen → weiterdenken".
- **Index-Sync:** inkrementeller mtime-Sync + „Neu indexieren"-Button in
  Settings — macht Obsidian-Koexistenz (Kernversprechen!) real.
- **Post-Setup-Onboarding:** Neustart-Checkliste, geführte erste Notiz,
  Setup aus der Nav, wenn abgeschlossen.
- **Feedback-Layer:** Toasts/Dialoge statt `alert()`/`confirm()`, deutsche
  Fehlertexte durchgängig, Undo beim Löschen (Papierkorb).
- **Chat-/Ask-Verlauf persistieren** (heute nur im DOM) — bei Wettbewerbern
  Standard, geringer Aufwand, hoher Alltagsnutzen.

## Quick Wins (Aufwand XS–S, gute Wirkung)

| Quick Win | Aufwand |
|-----------|---------|
| `escapeHtml` in `dashboard.js`/`login.js`/`setup.js` | XS |
| `requirements.txt` pinnen + Dependabot aktivieren | S |
| Compose-Standard-Bind `127.0.0.1:8000:8000` | XS |
| Session-Cookie `Secure`-Flag (config-abhängig) | XS |
| `resolve_vault_file`: `Path.relative_to`/`is_relative_to` statt `startswith`; Append über `resolve_vault_file` | XS |
| Frontmatter-Sanitizing für Titel/Tags (Newlines/Steuerzeichen strippen) | S |
| `APIError` aus Celery-Retry-Liste nehmen (kein Retry bei 4xx) | XS |
| Webhook-Secret timing-safe vergleichen | XS |
| `entries.status = failed` bei permanenten Fehlern wirklich setzen | S |
| Suchtreffer → `/notes?path=…`-Deep-Link | S |
| README-Feature-Liste + Testzahl aktualisieren | S |

## Technical Debt (bereinigen)

- ARCHITECTURE.md auf Ist-Stand (Phase H, pgvector-Image, ui/, Chunks,
  document/photo-Kinds, korrekte Write-Reihenfolge).
- `KIND_VALUES`/`STATUS_VALUES` vs. Realität (`document`, `photo`; `failed`
  nie gesetzt); Note-Level-`embedding`-Spalte ist Legacy.
- Doppelte Capture-Pfade REST/UI zusammenführen; ungenutztes `embed_batch`
  im Index-Sync verwenden (Batch-Embeddings statt seriell).
- CHANGELOG: „Unreleased"-Berg in Release v0.3.0 schneiden.
- Celery: Concurrency/Prefetch konfigurierbar machen.

## Product Gaps (funktional)

| Gap | Bewertung |
|-----|-----------|
| Kein Reindex nach externen Vault-Edits | **Must-have** (Kernversprechen Obsidian-Koexistenz) |
| Suche/Quellen nicht klickbar; kein Markdown-Rendering | **Must-have** |
| Kein persistenter Ask-/Chat-Verlauf | **Should-have** |
| Kein Import (Notion/Evernote/Apple Notes) | **Should-have** (Onboarding-Hürde für Wechsler) |
| Keine Voice-Capture in der Web-UI (nur Telegram) | Should-have (PWA-Story) |
| Kein Daily-Note/Journal-Einstieg | Nice-to-have (bei Reflect/Logseq zentral, passt aber nicht zwingend zu unserem Capture-first-Modell) |
| Auto-Linking/„Related notes" beim Lesen | Nice-to-have (Related existiert beim Capture; Surfacing beim Lesen fehlt) |
| E-Mail-Capture (E22-5), Share-Target (E23-4), Offline-Queue (E23-3) | Später (geplant, richtig priorisiert) |
| Kollaboration/Multi-User | Nicht sinnvoll jetzt (ADR 0004: Single-User-Produkt; erst mit Cloud-Edition E24 neu bewerten) |

## UX/UI Improvements

Priorisierte Liste (aus dem UI-Audit, verifiziert):

1. Post-Setup-Abschluss + Onboarding; Setup aus der Hauptnav.
2. Klickbare Treffer/Quellen (Deep-Link in Notizen).
3. Markdown-Preview + Edit-Toggle; Speichern-Feedback.
4. Einheitlicher Feedback-Layer (Toasts/Modals), deutsche Fehlertexte.
5. Terminologie-Pass: eine Sprache (keine „Entries", Env-Namen, „E26" in UI).
6. Mobile-Nav (Wrap/Hamburger) + Touch-Targets ≥ 44 px.
7. Empty-States mit CTA; 8. Undo/Papierkorb beim Löschen;
9. Integrations-Karte (API-Key/MCP/Webhooks erklärt); 10. Wikilink-Klicks.

Accessibility: heute ~WCAG-A-Niveau; für Kaufprodukt AA-Basis nachziehen
(Fokus-Styles auf Buttons, `aria-current`, `<main>`-Landmark, Kontraste).
i18n: alles hartcodiert deutsch — vor einem englischen Markt-Launch
Extraktion der UI-Strings einplanen (mittlerer Aufwand, wächst mit jedem
Feature).

## Security & Privacy

Vollständige Liste im Security-Teilaudit; die Essenz:

- **P0:** Localhost-Guard hinter Proxy (siehe Launch Blocker 1).
- **P1:** XSS Dashboard; `0.0.0.0`-Bind; leere Telegram-Allowlist als
  Default; Cookie ohne `Secure`; kein Rate-Limit (Login, `/v1`, LLM-Kosten).
- **P2:** Frontmatter-Injection; `startswith`-Path-Check + Append-Lücke;
  Upload-Typprüfung nur per Endung + PDF-Parse-DoS; Default-DB-Passwort;
  Lockout nicht proxy-/multi-worker-tauglich; Outbound-Webhook erhält
  `raw_input_preview`.
- **Gut:** API-Key timing-safe + API off-by-default, HMAC-Sessions korrekt,
  keine Shell-Injection (alle Subprozesse mit Argumentlisten), `.env` nicht
  im Image, Non-root-Container, Notizinhalt wird nicht als HTML gerendert.

## EU/Germany Readiness (technisch; juristische Prüfung separat)

**Jetzt bauen (teuer nachzurüsten):**

1. **Voll-Löschung:** ein Befehl/Endpunkt löscht DB (Entries, Index, Chunks,
   Embeddings), Vault optional, Voice-Cache, Backups — Art.-17-Basis.
2. **Strukturierter Export:** Vault ist schon portabel (Markdown!), aber
   Entries/Metadaten/Einstellungen fehlen — Art.-20-Basis.
3. **Log-Hygiene + Retention:** kein Notiz-/Transkript-Text in Logs,
   Voice-Cache-TTL, Backup-Rotation.
4. **Datenfluss-Doku:** OpenAI (Notiztext, Audio, Embeddings), Telegram,
   optional Ollama lokal — als `docs/privacy.md`, wird später AVV/Privacy-
   Policy-Grundlage. OpenAI-EU-Datenresidenz bzw. lokale Modelle (Ollama/
   whisper.cpp existieren schon!) sind ein echtes Verkaufsargument in DE.

**Organisatorisch (später, vor Verkauf):** Impressum/AGB/Widerruf,
AV-Verträge (OpenAI, Hoster, Payment), Datenschutzerklärung — juristisch
prüfen lassen. **Für die Cloud-Edition (E24/ADR 0007)** kommt deutlich mehr
dazu (Auftragsverarbeitung, TOMs, Hosting-Region) — spricht dafür, mit
Self-Hosted + Buy-Once zu starten.

## Competitive Insights

Markt 2026 (Quellen: Vergleichstests/Blogs zu Notion AI, Mem, Reflect, Tana,
NotebookLM, Obsidian; GitHub/Reviews zu Khoj, Reor):

| Produkt | Modell | Relevanz für uns |
|---------|--------|-------------------|
| **Khoj** (AGPL, ~36k Stars) | Self-hosted AI-Brain, RAG über eigene Dateien, Obsidian-/WhatsApp-Clients, Agents, Automationen; Cloud mit Free Tier | **Direktester Konkurrent.** Stärker bei: Multi-Client, Automationen/Newsletter, Agent-Builder. Schwächer bei: Capture-first-Telegram-Flow, One-Stack-Einfachheit. AGPL schreckt kommerzielle Weiternutzer ab — unser MIT+Buy-Once ist ein Differenzierer. |
| **Obsidian + AI-Plugins** | Local-first Standard, riesiges Ökosystem | Wir konkurrieren nicht — wir **ergänzen** (Vault-Koexistenz ist unser Versprechen → Index-Sync-Gap ist deshalb kritisch). |
| **Reflect** (~10 $/Monat) | E2EE, daily-note-first, schnell | Lernen: Polish + klare Privacy-Positionierung verkauft. |
| **Mem** (~15 $/Monat) | AI-first, Auto-Organisation ohne Ordner | Lernen: „Zero-Structure-Capture" ist genau unser Flow — wir müssen ihn nur so reibungslos erzählen/zeigen. |
| **Notion AI / Tana** | Team-Workspaces, Datenbanken/Supertags | Andere Zielgruppe (Teams/Struktur-Fans); nicht nachbauen. |
| **NotebookLM** | Source-grounded Research, kostenlos | Erwartungsanker für RAG-Qualität mit Quellen — unsere `/ask`-Quellen müssen klickbar und vertrauenswürdig sein. |

**Standard bei mehreren Wettbewerbern, bei uns offen:** persistenter
Chat-Verlauf, klickbare Quellen, Auto-Linking beim Lesen, Import-Tools,
Mobile-Capture-Politur. **Unser USP-Dreieck:** (1) Capture-first über
Telegram/überall, (2) echter Obsidian-Vault statt Datensilo, (3) ein
Docker-Stack, buy-once, MIT — Privacy-orientiert bis hin zu komplett lokalen
Modellen. Pricing-Anker: Abos 10–15 $/Monat → ein Buy-Once-Preis um
49–79 € wirkt attraktiv (Verkaufskanal = E21-2).

## Future Opportunities (interessant, jetzt nicht nötig)

- Automationen/Agenten (Khoj-Stil: geplante Digests als Newsletter/Telegram
  existieren fast schon — `/digest` + Scheduler wäre E22-6-artig).
- Graph-Ansicht der Notizen; Auto-Linking beim Lesen.
- E2E-Verschlüsselung des Vaults (Reflect-Positionierung).
- Cloud-Edition (E24) — bewusst gated auf ADR 0007; erst nach Launch-Härtung
  sinnvoll bewertbar.
- Native Apps (E20-3/5) — PWA-Weg bestätigt sich als richtig.

---

## Challenge-Log (verworfene/abgestufte Empfehlungen)

- **Multi-User/Rollenmodell jetzt bauen:** verworfen — ADR 0004 definiert
  Single-User; Cloud-Edition würde das neu aufrollen (Single-Tenant-Instanzen
  brauchen kein Multi-User im Code).
- **HNSW/ANN-Index sofort:** abgestuft auf „bei Bedarf" — exakter kNN ist bei
  typischen Vault-Größen (<10k Chunks) unkritisch; erst bei Cloud/great
  Vaults relevant. Dokumentiert als bewusste Entscheidung.
- **i18n sofort umsetzen:** abgestuft — erst bei EN-Markteintritt; jetzt nur
  keine neuen Hürden einbauen (Server-Fehlertexte zentralisieren hilft schon).
- **Daily Notes/Journal:** nicht übernommen — Wettbewerber-Feature, das
  unserem Capture-first-Modell widerspricht; erst bei Nutzer-Nachfrage.
- **Feature-Flags-System, Observability-Stack (Prometheus/Grafana):**
  verworfen für Self-Hosted-Single-User — `/health` + Admin-Notify + Sentry
  (optional) reichen; Metrics erst für Cloud-Edition.
- **E2E-Browser-Tests breit:** abgestuft auf 3–4 kritische Flows (Login,
  Capture, Backup) — Kosten/Nutzen.

## GO / NO-GO-Empfehlung

### GO WITH CONDITIONS

Das Produkt ist **strukturell bereit**, die nächste Phase (Hosting/Cloud-
Entscheidung, Monetarisierung, Vertrieb) zu **planen** — die Architektur
trägt, das Feature-Set ist wettbewerbsfähig differenziert, die Testbasis ist
überdurchschnittlich. **Bedingungen** (parallel bzw. vor dem ersten
zahlenden Kunden abzuarbeiten):

1. **Security-Härtung E27** (P0-Guard, XSS, sichere Defaults, Rate-Limits) —
   nicht verhandelbar, überschaubarer Aufwand (~1 Sprint).
2. **Datenintegrität E28** (Locks, Idempotenz, Index-Sync) — das
   Obsidian-Koexistenz-Versprechen muss halten, bevor Geld fließt.
3. **Release-/Ops-Readiness E29** (Pins, CI-Härtung, v0.3.0-Release,
   Backup-Retention + Restore-Test) — Voraussetzung für Support-Fähigkeit.
4. **DSGVO-Basis E31** (Löschung, Export, Log-Hygiene) — Pflicht für DE/EU.
5. **UX-Consumer-Pass E30** mindestens bis „Retrieval-Loop geschlossen +
   Onboarding" — sonst rechtfertigt das UI keinen Kaufpreis.

Die Cloud-/Abo-Entscheidung (ADR 0007) kann parallel diskutiert werden,
sollte aber erst **nach** E27–E29 umgesetzt werden — jeder der obigen Punkte
wird in einer Hosted-Umgebung teurer statt billiger.

*Neue Epics E27–E31 mit Stories, Prioritäten und Reihenfolge: siehe ROADMAP.*
