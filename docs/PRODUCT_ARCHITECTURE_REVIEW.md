# Product, Architecture & Technology Review

> **Stand:** 2026-08-30 · Release v0.3.0 · Basis: Code-Audit des Repositories,
> nicht Annahmen.
> **Status:** Analyse und Empfehlung. **Nichts davon ist umgesetzt.** Roadmap,
> ADRs und Code wurden für dieses Dokument **nicht** verändert.
> **Zweck:** Grundlage für Produktentscheidungen und externe Zweitmeinung.
>
> **Nachtrag 2026-08-30 — teilweise entschieden.** Die Deployment- und
> Positionierungsfrage aus Abschnitt 18–21 ist inzwischen normativ geklärt:
> [**ADR 0008**](adr/0008-deployment-models-self-hosted-first.md). Self-hosting
> ist ein Deployment-Modell und die zuerst ausgelieferte Betriebsform, **nicht**
> die Produktidentität; eine Managed Seiton Cloud ist ausdrücklich Teil der
> Produktvision. Formulierungen unten, die Self-Hosting als Produktdefinition
> oder als „Bedingung" lesen (u. a. Abschnitt 5), sind dadurch überholt.
> Bei Abweichungen gilt ADR 0008.

Belege sind als `pfad:zeilen` notiert. Wo dieses Dokument von `ARCHITECTURE.md`
abweicht, gilt der Code — siehe [Abschnitt 8](#8-current-gaps--misunderstandings).

---

## Inhalt

1. [Executive Summary](#1-executive-summary)
2. [Product Origin](#2-product-origin)
3. [Product Today](#3-product-today)
4. [Intended Product Vision](#4-intended-product-vision)
5. [Product Identity](#5-product-identity)
6. [Core vs Extensions](#6-core-vs-extensions)
7. [Product Layers](#7-product-layers)
8. [Current Gaps / Misunderstandings](#8-current-gaps--misunderstandings)
9. [Capture Architecture](#9-capture-architecture)
10. [Knowledge / Memory Architecture](#10-knowledge--memory-architecture)
11. [Obsidian / Vault Decision](#11-obsidian--vault-decision)
12. [Connector Architecture](#12-connector-architecture)
13. [Retrieval / RAG](#13-retrieval--rag)
14. [Provenance / Trust](#14-provenance--trust)
15. [Read / Assist / Action Model](#15-read--assist--action-model)
16. [Security & Privacy Model](#16-security--privacy-model)
17. [Prompt Injection / Untrusted Data](#17-prompt-injection--untrusted-data)
18. [Deployment Models](#18-deployment-models)
19. [Self-hosting / VPS](#19-self-hosting--vps)
20. [Managed Cloud](#20-managed-cloud)
21. [Managed AI / BYOK](#21-managed-ai--byok)
22. [Backend Technology Review](#22-backend-technology-review)
23. [Frontend Technology Review](#23-frontend-technology-review)
24. [Monolith / Service Boundaries](#24-monolith--service-boundaries)
25. [Web / PWA / Mobile / Desktop](#25-web--pwa--mobile--desktop)
26. [LLM Strategy](#26-llm-strategy)
27. [UX Principles](#27-ux-principles)
28. [Monetization Hypotheses](#28-monetization-hypotheses)
29. [Roadmap Conflicts](#29-roadmap-conflicts)
30. [Overengineering Risks](#30-overengineering-risks)
31. [Proposed V1 / V1.5 / V2](#31-proposed-v1--v15--v2)
32. [Decisions Required Now](#32-decisions-required-now)
33. [Decisions That Can Wait](#33-decisions-that-can-wait)
34. [Recommended Next Steps](#34-recommended-next-steps)

Anhänge: [A Technologie-Entscheidungstabelle](#anhang-a--technologie-entscheidungstabelle) ·
[B Produkt-Scope-Tabelle](#anhang-b--produkt-scope-tabelle) ·
[C Zielarchitektur](#anhang-c--empfohlene-zielarchitektur)

---

## 1. Executive Summary

**Der Kern ist gesund. Die Reihenfolge ist es nicht.**

Seiton Brain hat eine funktionierende, sauber getestete Capture-Pipeline
(~561 Tests), einen echten Retrieval-Stack und ein durchdachtes
Self-Hosting-Setup. Der Stack (Python/FastAPI/Postgres/pgvector/Celery) ist für
dieses Produkt die **richtige** Wahl — es gibt **keinen** Rewrite-Grund, weder
Backend noch Frontend, weder heute noch absehbar.

Die Probleme sind produktstrategischer, nicht technischer Natur:

1. **Der Hauptkanal kann am wenigsten.** ADR 0004 erklärt die Web-UI zur
   Hauptoberfläche und Telegram zum optionalen Power-Feature. Im Code ist es
   umgekehrt: Voice, Fotos und Dokumente funktionieren **ausschließlich** über
   Telegram. Web-UI, REST und MCP nehmen nur Text an — es gibt im gesamten Repo
   keinen Datei-Upload und keine Mikrofon-Nutzung
   (`app/ui/templates/dashboard.html:13-16`, kein `UploadFile` in `app/api/`).
   Telegram ist damit faktisch Kernbestandteil, nicht Option.

2. **Der beworbene „Magic Moment" ist strukturell nicht möglich.** Die Vision
   nennt `Projects/Fitness App/Ideas`. Der Code kennt genau eine Ordnerebene und
   sechs feste Kategorien aus einer YAML-Datei; die KI kann keine Ordner anlegen
   und keine Hierarchie bilden (`app/vault/categories.py:18-25,122-124`,
   `app/vault/filesystem.py:235-237`).

3. **Der Capture-Pfad benutzt die semantische Suche nicht.** Ob eine bestehende
   Notiz ergänzt wird, entscheidet ein Token-Overlap-Prefilter über maximal 200
   nach mtime sortierte Kandidaten (`app/vault/prefilter.py:99-146`,
   `app/vault/index.py:373-380`). Die Vektorsuche existiert — im wichtigsten
   Produktmoment wird sie nicht verwendet. Das ist der größte
   Qualitätshebel im Bestand.

4. **Semantische Suche ist im Auslieferungszustand aus.**
   `EMBEDDINGS_ENABLED` ist per Default `false` (`app/config.py:158`). Ein neuer
   Nutzer bekommt „Second Brain" als Keyword-Suche.

5. **Der RAG-Kontext ist zu dünn für das Versprechen.** Top-5 **Notizen** mit je
   ~400 Zeichen Snippet ≈ 2.000 Zeichen Kontext — obwohl die Vektorsuche auf
   Chunk-Ebene arbeitet und die passende Passage kennt
   (`app/services/answer.py:21,28-33`, `app/vault/index.py:29`). Bei PDFs und
   langen Notizen landet der relevante Absatz oft gar nicht im Prompt.

6. **Es gibt keine Herkunftsschicht.** Weder `source` noch `source_id` noch
   `actor` existieren. Die Identität eines Wissenselements ist der Dateipfad
   (`vault_note_index.vault_path` UNIQUE). Solange alles aus dem Vault kommt,
   trägt das. Ab dem ersten Connector (E-Mail, Kalender, Notion) trägt es nicht
   mehr. Die Roadmap weiß das (E33-1: *„jetzt billig, nachträglich teuer"*) und
   plant es trotzdem hinter Phase L ein.

7. **Es wird viel für hypothetische Nutzer geplant.** Die Phasen M/N/O umfassen
   rund 50 durchdachte Stories — inklusive Teams, Rollen und
   Permission-Layer —, während das Produkt noch keine externe
   Nutzerrückmeldung hat. Das ist derzeit das größte Projektrisiko.

**Empfehlung in einem Satz:** Keine Technologie ändern, keine Vision
verkleinern — stattdessen die Reihenfolge korrigieren: Kanalparität,
Ablagestruktur, Retrieval-Qualität und Provenance vor einer privaten Beta;
Connectoren, Teams und Cloud danach.

---

## 2. Product Origin

Die ursprüngliche Idee (rekonstruiert aus ADR 0003, `ARCHITECTURE.md` und der
Archiv-Roadmap A–H): *Gedanke rein über Telegram → KI versteht → Markdown landet
sinnvoll im Obsidian-Vault.*

| Ursprüngliche Fähigkeit | Heute | Beleg |
|---|---|---|
| Text erfassen | **vollständig** | `app/services/process_message.py:73-201` |
| Sprachnachricht erfassen | **vollständig, aber nur Telegram** | `app/worker/tasks.py:115-149`, `app/transcription/whisper.py` |
| Bild erfassen | **teilweise, nur Telegram**, OCR/Vision opt-in (Vision Default `false`) | `app/services/document_capture.py:30-32`, `app/config.py:177-178` |
| Dokument erfassen | **teilweise, nur Telegram**; `.md/.txt/.pdf/.docx/.pptx`, kein `.doc` | `app/vault/extractors.py` |
| Datei erfassen (beliebig) | **fehlt** — Originaldatei wird bewusst nicht abgelegt | `app/services/document_capture.py:5-6` |
| Inhalt verstehen | **vollständig** (Router→Writer→Linker, Pydantic-validiert) | `app/llm/openai_provider.py:88-132`, `app/llm/roles.py:17-32` |
| Kontext/Kategorie erkennen | **vollständig innerhalb fixer Kategorien** | `app/llm/schemas.py:42-73` |
| Entscheiden, wohin | **stark eingeschränkt** — flaches Mapping Kategorie→Ordner | `app/vault/categories.py:122-124` |
| Strukturieren | **vollständig** (Frontmatter, Template, Tags, Related) | `app/vault/filesystem.py:233-254`, `app/vault/templates.py` |
| Bestehendes Wissen ergänzen | **vollständig implementiert, schwach im Finden** | `app/services/process_message.py:109-122`, `app/vault/prefilter.py` |
| Speichern | **vollständig** (atomar, Locks, Kollisionsschutz, Kompensation) | `app/vault/filesystem.py:33-49,129-142`, `process_message.py:60-70` |
| Wiederfinden | **vollständig, Qualität begrenzt** | `app/vault/index.py:393-490`, `app/services/answer.py` |

### Später hinzugekommen (implementiert)

REST-API v1 · MCP-Server · Web-UI mit Setup-Wizard, Dashboard, Ask, Notes,
Settings, Login · PWA · Outbound-Webhooks · Offline-Lizenz (Ed25519) ·
Git-Vault-Backend · Ollama- und whisper.cpp-Pfad · Consumer-/VPS-Packaging ·
Digest · Vault-Index mit Chunks und pgvector.

### Später hinzugekommen (nur geplant)

Connectoren (E-Mail/Notion/Kalender) · Permission-Layer `ai_access` (E38) ·
Hybrid Search (E37-1) · Knowledge Chat mit Verlauf (E40) · Teams (Phase O) ·
Cloud-Edition mit Abo (E24, ADR 0007 *Proposed*) · Native Desktop (E20-3,
„kein Nahziel") · Mobile-Wrapper (E23-5).

### Veraltete Ursprungsannahmen

| Annahme | Status heute |
|---|---|
| „Telegram ist der Default-Eingang" (ADR 0003) | Von ADR 0004 revidiert — **im Code aber weiterhin wahr** für alles außer Text |
| „n8n wird Integrationsschicht" (ADR 0003) | Gestrichen (ADR 0004); REST + Beispiel-Workflows |
| „Ein Markdown-Ordner reicht als Wissensspeicher" | Trägt für Notizen; trägt **nicht** für Connector-Objekte ohne Datei |
| „Die DB ist reiner Audit-Spiegel" (`ARCHITECTURE.md`) | Überholt: Postgres hält Index, Chunks und Embeddings — den Retrieval-Kern |
| „Sechs Kategorien genügen" | Skaliert nicht auf projektbezogenes Wissen (`Projects/X/Ideas`) |
| „Vault ist Source of Truth" | Weiterhin richtig **für Notizinhalte** — aber nicht für Beziehungen, Provenance und Sync-Zustand |

---

## 3. Product Today

### Was nachweislich funktioniert

- **Capture-Pipeline** mit Idempotenz (`telegram_update_id` UNIQUE),
  File-Locks, atomarem Schreiben, Orphan-Kompensation und differenzierter
  Retry-Semantik. Das ist solide Ingenieursarbeit.
- **Klassifikation** über drei spezialisierte Prompt-Rollen mit
  Pydantic-Validierung, Retry und Nachbereinigung (`related` und `target_title`
  werden gegen den echten Vault geprüft — Halluzinationen können nicht
  durchschlagen, `app/llm/openai_provider.py:176-226`).
- **Vault-Index** mit inkrementellem mtime-Sync, Celery-Beat (60 s), Chunking
  (1500/200) und pgvector-kNN.
- **Retrieval** über Keyword (ILIKE auf Titel → Snippet → Chunk) und semantisch,
  mit Fallback; `/ask` und `/digest` liefern validierte Quellen zurück.
- **Web-UI** mit sechs Screens, Session-Auth, Brute-Force-Lockout,
  localhost-Guard mit Proxy-Härtung, maskierten Secrets, Backup-UI.
- **Betrieb**: Docker Compose in drei Profilen, Installer für macOS/Linux/Windows,
  `doctor.sh`, `update.sh`, Alembic-Migrationen, CI mit ruff/pytest/pip-audit/
  Docker-Build/pgvector-Smoke.

### Was nicht existiert (verifiziert)

Keine native Desktop-App, kein Electron, kein Tauri, keine native Mobile-App,
kein Capacitor, **kein `package.json`** im gesamten Repo. Kein Streaming
(SSE/WebSocket) irgendwo. Kein Datei-Upload in UI oder API. Keine Spracheingabe
im Browser. Kein Share-Target, keine Push-Benachrichtigungen, kein
Offline-Capture in der PWA (`app/ui/static/sw.js:5-6,25-49`). Keine `users`-Tabelle,
keine Rollen, keine Zugriffskontrolle auf Wissensebene.

### Reifegrad nach Fähigkeit

| Fähigkeit | Reife | Begründung |
|---|---|---|
| Text-Capture | ●●●●● | Alle Kanäle, robust |
| Voice-Capture | ●●●○○ | Funktioniert, aber nur ein Kanal |
| Datei-/Bild-Capture | ●●○○○ | Nur Telegram, Vision opt-in, Original geht verloren |
| Verstehen/Klassifizieren | ●●●●○ | Gut — begrenzt durch flaches Zielschema |
| Ablegen/Strukturieren | ●●●○○ | Technisch exzellent, Struktur zu flach |
| Wiederfinden (Suche) | ●●●○○ | Kein Hybrid, Embeddings default aus |
| Fragen (RAG) | ●●○○○ | Kontextfenster zu klein, One-Shot ohne Verlauf |
| Verbinden (Relationen) | ●●○○○ | Nur Wiki-Links im Markdown, kein Graph in der DB |
| Vertrauen/Korrektur | ●●○○○ | `/undo` nur in Telegram, bei Append unvollständig |
| Self-Hosting | ●●●●○ | Gut automatisiert; ein manueller Neustart bleibt |
| Security-Grundlage | ●●●●○ | Für Single-User angemessen; kein Least-Privilege bei Keys |
| Privacy-Substanz | ●●●○○ | Lokal ja; Löschung/Export/Log-Hygiene offen (E31) |

---

## 4. Intended Product Vision

Die Vision aus der Aufgabenstellung ist **tragfähig und sollte nicht reduziert
werden**. Präzisierung, damit sie entscheidbar wird:

> Seiton Brain ist die **intelligente Zwischenschicht über den persönlichen
> Daten eines Menschen** — nicht der Ort, an dem diese Daten leben, sondern der
> Ort, an dem sie verstanden, verknüpft und beantwortet werden.

Daraus folgen drei harte Abgrenzungen:

1. **Seiton besitzt Bedeutung, nicht Daten.** Notizinhalte gehören in Markdown
   (portabel, Obsidian-kompatibel). E-Mails gehören ins Postfach. Termine in den
   Kalender. Seiton besitzt: Verständnis, Index, Beziehungen, Herkunft,
   Vertrauensstufen, Antworten.
2. **Seiton ersetzt keine Oberfläche, die es nicht besser kann.** Eine eigene
   Oberfläche ist nur dort gerechtfertigt, wo Seiton etwas kann, das die
   Quellanwendung nicht kann.
3. **Seiton ist ein Gedächtnis, kein Agent.** Der Antwortpfad bleibt
   grundsätzlich lesend. Aktionen sind eine separate, explizit freigegebene
   Ebene.

**Ist das Bild „Obsidian/Notion/Files/Email/Calendar → Seiton → Web/Mobile/AI"
tragfähig?** Ja, mit einer Korrektur: Der Pfeil ist heute in beide Richtungen
gedacht, obwohl Seiton **in** den Vault schreibt. Seiton ist für Notizen also
nicht nur Leser, sondern Autor. Diese Doppelrolle ist ein Feature
(Capture-Ziel), muss aber bewusst begrenzt bleiben: **Seiton schreibt in genau
eine Quelle (den eigenen Vault) und liest aus allen anderen.** Alles andere wäre
Two-Way-Sync — die teuerste und fehleranfälligste Klasse von Integration, und
laut Integrations-Audit bereits bewusst ausgeschlossen.

---

## 5. Product Identity

> **Überholt durch [ADR 0008](adr/0008-deployment-models-self-hosted-first.md).**
> Geltende Definition: *Seiton Brain ist ein persönliches AI-gestütztes Second
> Brain. Self-hosting ist die zuerst ausgelieferte Betriebsform und ein starkes
> Privacy-/Control-Angebot — nicht die Produktidentität. Eine Managed Seiton
> Cloud ist Teil der Produktvision, kommt aber nach stabilem Core und realem
> Nutzerfeedback.* Die Analyse unten bleibt als Herleitung erhalten.

**Was ist Seiton?**
Ein selbst betriebenes persönliches Wissenssystem, das Gedanken, Sprachnotizen
und Dokumente entgegennimmt, mit einem Sprachmodell versteht und einsortiert,
als portables Markdown ablegt und später auf natürliche Fragen mit belegten
Antworten aus dem eigenen Wissen reagiert.

**Für wen?**
Menschen, die (a) viel unstrukturiertes persönliches Wissen produzieren,
(b) es heute in Notiz-Apps oder Chat-Verläufen verlieren, und (c) genug
Datenschutzbewusstsein haben, um dafür eine eigene Box zu betreiben oder
betreiben zu lassen. Konkret: technikaffine Wissensarbeiter, Selbstständige,
Studierende, Obsidian-Nutzer mit chronisch unsortiertem Inbox-Ordner.

**Welches Problem?**
Erfassen ist billig, Einsortieren ist teuer. Deshalb landet alles im Inbox-Ordner
und wird nie wieder gelesen. Seiton macht die teure Hälfte automatisch und macht
das Ergebnis abfragbar.

**Warum nicht einfach Obsidian?**
Obsidian ist ein exzellenter Editor ohne Verstand. Es sortiert nichts ein,
transkribiert nichts, beantwortet keine Fragen über den Gesamtbestand. Seiton
schreibt **in** Obsidian — die beiden konkurrieren nicht.

**Warum nicht einfach Notion?**
Notion verlangt, dass man vorher weiß, in welche Datenbank etwas gehört, und die
Daten liegen auf fremden Servern in einem proprietären Format. Seiton verlangt
kein Vorwissen und speichert in Dateien, die man morgen mit jedem Editor öffnen
kann.

**Warum nicht einfach ChatGPT?**
ChatGPT hat kein durchsuchbares, wachsendes, überprüfbares Gedächtnis der eigenen
Dokumente, keine Ablage in eigenem Besitz und keine Quellenangaben aus den
eigenen Dateien. Wo es Gedächtnis anbietet, liegt es beim Anbieter.

**Warum nicht Apple Notes / Google Keep?**
Beide sind gute Eingabefelder und schlechte Bibliotheken: keine automatische
Struktur, keine Verknüpfung über Themen hinweg, keine Frage-Antwort über den
Gesamtbestand, kein Export in ein offenes Format mit erhaltener Struktur.

**Warum selbst hosten?**
Weil die Daten Bewerbungen, Gesundheitsnotizen, Verträge und Gedanken enthalten,
die man einem Anbieter nicht anvertrauen möchte. Self-Hosting ist hier kein
Hobby, sondern die Bedingung dafür, dass man das System überhaupt ehrlich füttert.

**Warum stattdessen für eine Cloud zahlen?**
Weil eine Always-on-Box, Backups, Updates, Zertifikate und ein LLM-Konto für
viele mehr Arbeit sind als der Nutzen — und weil ein zweites Gehirn wertlos ist,
wenn es nachts ausgeschaltet ist. **Diese Antwort ist bewusst schwächer als die
vorige.** Das ist ehrlich und sollte die Priorisierung von ADR 0007 prägen.

---

## 6. Core vs Extensions

Bewertungsmaßstab: Ohne welche Fähigkeit würde ein Nutzer nach zwei Wochen
aufhören?

### CORE — ohne das ist Seiton kein Second Brain

Reibungsloses Capture über **mindestens einen mobilen und einen stationären
Kanal, jeweils mit Text, Sprache und Datei** · Verstehen und Einsortieren ohne
Nutzerentscheidung · Portable Ablage (Markdown + Frontmatter) · Index mit
Volltext **und** Semantik · Suche · Frage-Antwort mit Quellenangabe · Herkunft
und Nachvollziehbarkeit · Korrekturmöglichkeit · Self-Hosting mit Backup und
Export.

### ADJACENT — verstärkt den Kern erheblich

Knowledge Chat mit Verlauf und Kontext-Inspektor (E40) · Hierarchische, lernende
Ablagestruktur · Ähnliche Notizen / Duplikatswarnung vor dem Schreiben (E37-4) ·
Version History über Git (E43-2) · Templates pro Kategorie · Permission-Layer
`ai_access` (E38) · Lokale Modelle (E39).

### EXTENSIONS / CONNECTORS — echte Erweiterungen, unabhängig baubar

**Read-only zuerst:** Web-/URL-Capture (E33-2) · E-Mail-Ingestion (E22-5,
Anbieter/Protokoll offen) · Kalender lesen (CalDAV/Google/Microsoft) · Notion lesen · lokale
Ordner außerhalb des Vaults · Cloud-Storage über Ordnersync (kein eigenes
OAuth). **Ausgehend:** Webhooks, MCP, REST — bereits vorhanden.

### LATER — sinnvoll, aber nicht vor echten Nutzern

Assist (Entwürfe, Zusammenstellungen) · Kontrollierte Aktionen (Termin anlegen,
E-Mail-Entwurf) · Teams/Shared Instance (Phase O) · Managed Cloud (E24) ·
Managed AI · Native Mobile-App · Automatisierungsrezepte.

### OUT OF SCOPE — bewusst nicht bauen

Obsidian-Ersatz (Editor, Graph-View, Plugin-System) · Notion-Ersatz (Datenbanken,
Boards, Formeln) · E-Mail-Client · Kalender-Anwendung · Projektmanagement mit
Kanban/Sprints/Due-Dates · Dateisynchronisationsdienst · allgemeiner Chatbot ohne
eigene Datenbasis · mandantenfähige Datenarchitektur *(im aktuellen Horizont —
siehe [Abschnitt 18](#18-deployment-models))* · unbeaufsichtigt schreibender
Agent in fremden Systemen · eigenes Modell-Hosting/GPU-Betrieb · Custom-n8n-Node
(bereits per ADR 0004 gestrichen).

Vollständige Klassifikation: [Anhang B](#anhang-b--produkt-scope-tabelle).

---

## 7. Product Layers

Das vorgeschlagene Schichtmodell (Capture → Organize → Remember → Retrieve →
Connect → Assist → Act) ist als **Reifegrad-Modell** richtig und als
**Bauplan-Reihenfolge falsch**.

**Kritik 1 — Layer 2 und 4 sind dieselbe Technik.**
„Ergänze bestehendes Wissen" ist eine Retrieval-Frage *innerhalb* des
Capture-Pfads. Genau daran krankt der Code: Der Capture-Pfad findet Kandidaten
per Token-Overlap, obwohl der Vektorindex daneben liegt
(`app/vault/prefilter.py:99-146` vs. `app/vault/index.py:450-490`). Layer 4 muss
also **vor** der Perfektionierung von Layer 2 kommen, nicht danach.

**Kritik 2 — Layer 3 („Remember") ist keine eigene Phase, sondern eine
Datenmodell-Entscheidung.** Persistenz existiert. Was fehlt, sind Provenance und
eine quellenneutrale Identität — und die gehören ins Fundament, nicht in eine
spätere Schicht.

**Kritik 3 — Layer 5 („Connect") ist der teuerste Schritt und steht zu weit
vorn.** Jeder Connector bringt Authentifizierung, Rate Limits, Sync-Zustand,
Löschsemantik, untrusted content und Berechtigungen mit. Der erste Connector ist
zehnmal teurer als der zehnte Prozentpunkt Retrieval-Qualität.

**Empfohlene Reihenfolge:**

```
Fundament   Provenance + quellenneutrale Identität + Ablagestruktur
   ↓        (klein, jetzt billig, später teuer)
Layer 1+2   Capture überall (Kanalparität) + Organize
   ↓        gemeinsam, nicht nacheinander
Layer 4     Retrieve (Hybrid, Chunk-Kontext, Eval-Harness)
   ↓        speist Layer 2 zurück
── PRIVATE BETA ──────────────────────────────────
Layer 6a    Assist light (Chat mit Verlauf, Zusammenfassen)
   ↓
Layer 5     Connect (ein Connector, read-only, end-to-end)
   ↓
Layer 6b/7  Assist voll / Act — nur mit Freigabe-Modell
```

Der Schnitt bei der privaten Beta ist der wichtigste Teil dieses Modells.

---

## 8. Current Gaps / Misunderstandings

### 8.1 Dokumentation weicht vom Code ab

`ARCHITECTURE.md` ist auf dem Stand „0.2.0+, Phase C begonnen" und beschreibt in
wesentlichen Punkten ein älteres System:

| Aussage in `ARCHITECTURE.md` | Realität |
|---|---|
| „Retrieval / Q&A: teilw. (E17-1), geplant" (Z. 332) | Vollständig implementiert inkl. Chunks, pgvector, `/ask`, Digest |
| DB-Abschnitt kennt nur `entries` (Z. 193-207) | Es gibt `vault_note_index` und `vault_chunk` mit Embeddings |
| `kind`: nur `text`, `voice` (Z. 213) | Auch `document`, `photo` (`app/worker/tasks.py:62,190`) |
| `status`: ohne `appended` (Z. 214) | `appended` wird gesetzt (`process_message.py:163`) |
| „Service-Layer befüllt `vault_path` … noch nicht" (Z. 216-218) | Seit E3-1 erledigt |
| „Frontmatter wird in E3-2 noch nicht aktualisiert" (Z. 261) | E3-3 erledigt (`filesystem.py:268-274`) |
| High-Level-Diagramm zeigt nur Telegram | UI-Capture, REST und MCP fehlen |

**Warum das zählt:** Die Cursor-Rule und E45-2 weisen Agents an, vor
Architekturänderungen `ARCHITECTURE.md` zu lesen. Sie lesen dann eine veraltete
Beschreibung. Das ist ein konkretes, heute wirksames Problem — E29-5 (Doku-Sync)
sollte deutlich weiter nach vorn.

### 8.2 Strategie widerspricht Implementierung

| ADR/Doku | Code |
|---|---|
| ADR 0004: „UI wird die Hauptoberfläche", „Telegram wird zum optionalen Power-Feature" | Web-UI kann nur Text; Voice/Foto/Dokument ausschließlich Telegram |
| Vision: `Projects/Fitness App/Ideas` | Eine Ordnerebene, sechs feste Kategorien |
| „Second Brain" | Semantische Suche standardmäßig deaktiviert |
| ADR 0003: „Vault als Interface, weitere Backends pluggen ein" | `VaultBackend`-Protokoll existiert; das Datenmodell ist aber über `vault_path` fest an Dateipfade gebunden |
| ADR 0003: „Postgres ist Audit" | Postgres hält den kompletten Retrieval-Kern |

### 8.3 Funktionale Lücken mit Produktwirkung

1. **Kein Datei-Upload außerhalb Telegrams.** Der wahrscheinlichste
   Second-Brain-Anwendungsfall überhaupt („Rechnung von Anbieter Y") erfordert
   den Umweg über einen Chat-Dienst.
2. **Originaldateien werden verworfen.** Nur der extrahierte Text landet im
   Vault (`document_capture.py:5-6`). Die Frage „Habe ich die Rechnung noch?"
   kann Seiton damit strukturell **nicht** mit Ja beantworten.
3. **Korrektur nur über Telegram.** `/undo` existiert nur dort und lässt bei
   `append` den Update-Block in der Datei stehen (`app/telegram/commands.py:127-131`).
   Die UI zeigt nach dem Speichern zwar den Pfad, bietet aber keine Korrektur.
4. **Append-Ziel wird über `Entry.title` in der DB gesucht**, nicht über den
   Vault-Index (`process_message.py:37-42`). Bei gleichnamigen Notizen kann an
   die falsche Datei angehängt werden.
5. **Kategorie wird im Code nicht validiert.** Liefert das LLM eine unbekannte
   Kategorie, landet sie im Frontmatter, während die Datei im Default-Ordner
   liegt — Label und Ablage divergieren.
6. **Beziehungen existieren nur als Wikilink-Text.** „Hatte ich schon einmal eine
   ähnliche App-Idee?" ist ohne Graph oder kNN-Vorschlag nicht beantwortbar.

### 8.4 Was ausdrücklich **kein** Problem ist

Python · FastAPI · Celery/Redis · Postgres · Jinja2 · Vanilla JS · Docker
Compose · Monolith-Struktur · fehlende Desktop-App · fehlende native Mobile-App ·
fehlender ANN-Index (bei aktuellen Datenmengen irrelevant) · fehlendes n8n-Node.

---

## 9. Capture Architecture

### Ist-Zustand

```
Telegram ──► Text ─┐
             Voice ─┤ (Whisper: OpenAI | whisper.cpp)
             Photo ─┤ (OCR/Vision, opt-in)
             Doc ───┤ (md/txt/pdf/docx/pptx)
                    │
REST /v1/capture ───┤ nur Text
UI /api/ui/capture ─┤ nur Text
MCP capture_note ───┘ nur Text (via REST)
                    │
                    ▼
        process_text_message()
          1 classify (Router→Writer→Linker)
          2 Kandidaten: 200 nach mtime → 30 per Token-Overlap
          3 append-Ziel prüfen (DB-Titel + Datei existiert)
          4 Entry anlegen, UNIQUE-Claim
          5 Vault schreiben (Lock, atomar)
          6 Index + Chunks + Embeddings
```

### Bewertung des „Magic Moments"

| Anspruch | Erfüllt? |
|---|---|
| Nutzer muss keinen Titel wählen | **ja** |
| Nutzer muss keine Kategorie wählen | **ja** |
| Nutzer muss keine Tags wählen | **ja** |
| Nutzer muss kein Format wählen | **ja** |
| Nutzer muss nicht wissen, wo es landet | **ja** |
| Bestehendes Wissen wird erkannt und ergänzt | **teilweise** — Kandidatenfindung ist lexikalisch, nicht semantisch |
| Ablage ist projektbezogen (`Projects/X/Ideas`) | **nein** — flach |
| Von unterwegs mit Sprache erfassbar | **nur über Telegram** |
| Foto/Dokument von unterwegs | **nur über Telegram** |
| Nutzer sieht, was passiert ist | **ja** (UI: voller Pfad; Telegram: nur Ordner) |
| Nutzer kann korrigieren | **fast nicht** |

**Fazit:** Für Text ist der Moment nahezu erreicht — ein Feld, ein Klick, fertig.
Die Lücke ist nicht die Intelligenz, sondern die **Kanal- und
Strukturabdeckung**.

### Empfehlung

1. **Kanalparität herstellen** (V1-kritisch): Datei-Upload in UI und REST
   (multipart, mit Größenlimit und Extractor-Wiederverwendung); Mikrofon-Aufnahme
   im Browser (`MediaRecorder` → vorhandener Whisper-Pfad). Beides nutzt
   ausschließlich bereits existierende Server-Logik — der Aufwand liegt im
   Transport, nicht in der Pipeline.
2. **Semantische Kandidatenfindung im Capture-Pfad**: kNN über die vorhandenen
   Chunk-Vektoren statt Token-Overlap, mit Token-Overlap als Fallback bei
   deaktivierten Embeddings. Größter Qualitätsgewinn pro Aufwand im gesamten
   Bestand.
3. **Ablagestruktur entscheiden** (siehe Abschnitt 32): Kategorie bleibt als
   Label, aber der Zielpfad wird mehrstufig und aus dem vorhandenen Vault
   gelernt, statt aus einer festen Liste zu stammen.
4. **Originaldatei optional behalten**: Anhang neben der Notiz
   (`_attachments/`), im Frontmatter referenziert. Ohne das bleibt „Habe ich die
   Rechnung noch?" unbeantwortbar.

---

## 10. Knowledge / Memory Architecture

### Was „Memory" in Seiton bedeutet — Definition

Neun Klassen mit unterschiedlicher Verbindlichkeit. Die Trennung ist der
eigentliche Kern der Vertrauensfrage:

| # | Klasse | Heute | Verbindlichkeit | Wer darf schreiben |
|---|---|---|---|---|
| 1 | **Source Data** — Originalinhalt | Vault-`.md`; Originaldateien verworfen | **Fakt** | Nutzer + Capture |
| 2 | **Knowledge Objects** — normalisierte Einheit | `vault_note_index` (dateigebunden) | Fakt | System |
| 3 | **Search Index** — Volltext | ILIKE auf Snippet/Chunk | Ableitung, verwerfbar | System |
| 4 | **Vector Embeddings** | `vault_chunk.embedding` | Ableitung, verwerfbar | System |
| 5 | **Conversation History** | existiert nicht (bewusst, E40-1) | flüchtig | — |
| 6 | **User Preferences** | `.env` + `vault_config.yaml` | Fakt | nur Nutzer |
| 7 | **Derived Knowledge** — KI-Schlüsse | `summary`, `tags` — **im Notiztext, nicht getrennt** | **Vermutung** | KI, kennzeichnungspflichtig |
| 8 | **Relationships** | `related` als Wikilinks im Markdown | Vermutung | KI |
| 9 | **AI Summaries** | Digest/Answer, nicht persistiert | Vermutung | KI |

**Der kritische Befund:** Klasse 7 ist heute nicht von Klasse 1 unterscheidbar.
Der KI-generierte `summary` steht als Fließtext in derselben Datei wie der
Originalgedanke, und bei `append` wird er zum `## Update`-Block. Nach einem Jahr
kann niemand mehr sagen, welcher Satz vom Nutzer und welcher vom Modell stammt —
und ab dann wird das Modell auf seinen eigenen Interpretationen weiterarbeiten.

**Empfehlung (billig, jetzt):** Zwei Frontmatter-Felder als Konvention —
`source: telegram|ui|rest|mcp|email|web` und `generated_by: <modell>@<prompt-version>`
für abgeleitete Blöcke, plus Beibehaltung des Rohtexts in `entries.raw_input`
(existiert bereits). Das ist eine Konvention, kein Subsystem. Es macht später
jede Vertrauens-, Lösch- und Korrekturfunktion möglich, und rückwirkend ist es
nicht rekonstruierbar.

### Braucht Seiton ein neutrales Knowledge Object?

**Ja — aber als schmale Erweiterung des vorhandenen Modells, nicht als neues
Subsystem.**

Argumentation nach Entscheidungsdisziplin:

- *Problem existiert heute?* **Nein.** Alles kommt aus dem Vault; `vault_path`
  als Identität funktioniert.
- *Problem entsteht später?* **Ja, mit Sicherheit, beim ersten Connector.** Eine
  E-Mail hat keinen Vault-Pfad. Der Unique-Constraint auf `vault_path` und die
  Vault-`rglob`-Sync-Logik sind dann strukturelle Blocker.
- *Rein theoretisch?* Nein.
- *Wäre eine spätere Migration realistisch?* Teilweise. Die Spalten
  nachzuziehen ist eine Alembic-Migration. Aber die Annahme „ein Wissenselement
  ist eine Datei" steckt in `sync_vault_index`, `upsert_vault_note_index`,
  `retrieve_vault_notes`, `_resolve_sources`, in der Notes-API und der UI. Je
  mehr darauf aufbaut, desto teurer.

**Konkret empfohlen (drei Spalten, kein Datenmodell-Neubau):**

```
vault_note_index  →  knowledge_item (Umbenennung optional, nicht nötig)
  + source        VARCHAR   'vault' | 'email' | 'calendar' | 'notion' | 'web'
  + source_id     VARCHAR   externe stabile ID; für Vault = vault_path
  + source_url    VARCHAR   NULL
  UNIQUE (source, source_id)   statt UNIQUE (vault_path)
  vault_path bleibt NULLABLE — für Nicht-Datei-Objekte leer
```

Das ist **eine Migration und ein Refactoring von etwa sechs Aufrufstellen**.
Heute ist es ein halber Tag. Nach dem ersten Connector ist es ein Umbau mit
Datenmigration. Die Roadmap enthält mit E33-1 bereits die Capture-Hälfte davon;
sie sollte um die Index-Hälfte ergänzt und vorgezogen werden.

**Was ausdrücklich Overengineering wäre:** Eine generische
`Permissions`-Struktur, ein Relationship-Graph als eigene Tabelle, ein
`sync_state`-Subsystem oder ein abstraktes Type-System für Knowledge Objects,
bevor der erste Connector existiert. Diese Teile kommen mit dem Connector, der
sie tatsächlich braucht.

---

## 11. Obsidian / Vault Decision

### Bewertung der drei Modelle

| Kriterium | A Vault-centric | B Seiton Knowledge Core | C Hybrid |
|---|---|---|---|
| Local-first | ●●●●● | ●●○○○ | ●●●●● |
| Datenportabilität | ●●●●● | ●●○○○ | ●●●●● |
| Vendor Lock-in (Seiton) | ●●●●● keiner | ●○○○○ hoch | ●●●●○ gering |
| Privacy | ●●●●● | ●●●○○ | ●●●●● |
| Obsidian-Kompatibilität | ●●●●● | ●●○○○ | ●●●●● |
| Notion/E-Mail/Kalender | ●○○○○ erzwingt Fake-Dateien | ●●●●● | ●●●●○ |
| Attachments | ●●●●○ | ●●●●● | ●●●●● |
| RAG-Qualität | ●●●○○ | ●●●●● | ●●●●● |
| Metadaten/Beziehungen | ●●○○○ Frontmatter-Grenzen | ●●●●● | ●●●●● |
| Cloud-Betrieb | ●●●○○ | ●●●●● | ●●●●○ |
| Multi-Device | ●●●○○ (Ordnersync) | ●●●●● | ●●●●○ |
| Backup/Restore | ●●●●● Dateien + Git | ●●●○○ DB-Dump | ●●●●● |
| Teams später | ●●○○○ | ●●●●○ | ●●●●○ |
| Migration von heute | keine | **groß, riskant** | **klein** |

### Empfehlung: **Modell C (Hybrid) — und zwar durch Präzisierung, nicht durch Migration**

**Begründung:** Seiton ist heute bereits Hybrid, nur unausgesprochen. Der Vault
hält Notizinhalte; Postgres hält Index, Chunks, Vektoren und Audit. Der Satz in
`ARCHITECTURE.md`, die DB sei „Audit/Cache, kein Ersatz für die Markdown-Dateien",
beschreibt nicht mehr die Realität — Chunks und Embeddings sind kein Cache,
sondern der Retrieval-Kern.

Modell C festzuschreiben bedeutet also **keine disruptive Migration**, sondern:

1. **Vertragliche Klarstellung**, die auch als Marketingversprechen taugt:
   *„Alles, was du geschrieben hast, ist eine Markdown-Datei, die du behältst.
   Alles, was Seiton daraus ableitet, ist reproduzierbar und wegwerfbar."*
   Testbar als CI-Invariante: Nach `DROP DATABASE` + Reindex muss der Nutzer
   inhaltlich nichts verloren haben (`entries.raw_input` und Provenance sind die
   einzige Ausnahme — deshalb gehören diese ins Frontmatter, nicht nur in die DB).
2. **Quellenneutrale Identität** in der Index-Schicht (Abschnitt 10).
3. **Vault bleibt Schreibziel für Notizen; alle anderen Quellen bleiben
   read-only.** Keine Fake-Markdown-Dateien für E-Mails oder Termine — die würden
   Portabilität vortäuschen und Sync-Konflikte erzeugen.

Modell A scheitert am ersten Connector. Modell B opfert das stärkste
Verkaufsargument des Produkts (portable Dateien, Obsidian parallel nutzbar) für
Eigenschaften, die Modell C ebenfalls liefert.

### Braucht Seiton eine eigene Knowledge-Oberfläche?

**Ja, aber nur für vier Dinge**, und die stehen bereits:

| Oberfläche | Berechtigt? | Warum |
|---|---|---|
| Capture | **ja** | Muss kanalunabhängig und reibungslos sein — kann kein Fremdtool |
| Suche & Chat über alle Quellen | **ja** | Genau das kann keine Quellanwendung |
| Quellen-Inspektion („was wurde gesendet, woher kam das") | **ja** | Vertrauensfunktion, gibt es sonst nirgends |
| Integrationen & Einstellungen | **ja** | Systemverwaltung |
| Notiz-Editor | **nur minimal** | Existiert (`/notes`); für Schnellkorrekturen legitim, darf nie mit Obsidian konkurrieren |
| Dateibrowser | **nein** | Betriebssystem und Obsidian können das besser |
| Kalenderansicht, Mailansicht | **nein** | Klare Nachbauten |

Die Aussage „Seiton kann allein oder mit verbundenen Tools genutzt werden" ist
tragfähig — mit der Präzisierung: **Allein genutzt schreibt Seiton in seinen
eigenen Vault; verbunden liest es zusätzlich aus fremden Quellen.**

---

## 12. Connector Architecture

### Ist die Architektur vorbereitet?

**Teilweise — die Ausgangsseite ja, die Eingangsseite nein.**

| Baustein | Vorhanden | Bewertung |
|---|---|---|
| Worker/Queue für periodische Jobs | ja (Celery Beat, `celery_app.py:15-23`) | trägt |
| Extractor-Interface für Formate | ja (`extractors.py`, ABC + Registry) | trägt, aber vault-dateigebunden |
| VaultBackend-Protokoll | ja | irrelevant für Connectoren (Ausgang) |
| Index-/Chunk-/Embedding-Pipeline | ja | trägt, sobald Identität quellenneutral ist |
| Provenance (`source`, `source_id`) | **nein** | **Blocker** |
| Sync-State pro Quelle (Cursor, Tokens, Fehler) | **nein** | Blocker |
| Credential-Speicher für OAuth-Tokens | **nein** (nur `.env` + optional OS-Keyring) | Blocker für OAuth-Connectoren |
| Berechtigungsfilter vor Retrieval | **nein** (E38 geplant) | Blocker für gemischte Sensibilität |
| Löschsemantik/Tombstones für externe Objekte | **nein** | Blocker |
| Idempotenz für externe Objekte | nur `telegram_update_id` | Blocker |

### Empfohlenes neutrales Connector-Modell

```
┌────────────┐
│ Connector  │  Deklaration: id, Typ, Fähigkeiten (read|write), Trust-Klasse
└─────┬──────┘
      ▼
  Authentication   Passwort/App-Passwort | OAuth | Dateipfad
      ▼            → Tokens verschlüsselt, getrennt von .env, widerrufbar
  Permissions      Scopes beim Verbinden; Default read-only; fail-closed
      ▼
  Sync             Cursor/Delta, Rate-Limit, Fehlerzustand sichtbar in Settings
      ▼
  Normalization    Quellformat → einheitliche Felder + `source`/`source_id`
      ▼
  Knowledge Item   (source, source_id) UNIQUE · Inhalt · Zeitstempel · Trust
      ▼
  Index            Chunks + Embeddings, gefiltert nach ai_access
      ▼
  Retrieval        Filter VOR der Suche, nie danach
```

**Zwei nicht verhandelbare Invarianten:**

1. **Ein Connector ist read-only, bis er es explizit nicht ist.** Schreibende
   Connectoren sind ein separates Feature mit eigener Freigabe (Abschnitt 15).
2. **Der Berechtigungsfilter sitzt vor dem Retrieval, nicht nach der Antwort.**
   Das ist bereits die dokumentierte Invariante aus dem Knowledge-AI-Audit und
   sollte bei jedem Connector gelten.

**Was heute zu tun ist:** Nur `source` und `source_id` (Abschnitt 10). Alles
andere entsteht mit dem ersten realen Connector — vorher fehlen die
Anforderungen. Ein Connector-Framework auf Vorrat wäre exakt der
Overengineering-Fall, den das Integrations-Audit bereits ausgeschlossen hat.

**Erster Connector — Kategorie ja, Technologie noch offen.** Ein **read-only
E-Mail-Connector** ist der überzeugendste Kandidat für V2: sofortiger
Alltagsnutzen („Wann habe ich mich bei Firma X beworben?"), und er erzwingt genau
die drei Fähigkeiten, die alle späteren Connectoren brauchen — Sync-State,
Provenance und Umgang mit untrusted content.

**Anbieter und Protokoll werden hier ausdrücklich nicht festgelegt.** Generisches
IMAP ist für manche Anbieter der einfachste Weg, aber die verbreitete Annahme
„IMAP spart OAuth" gilt für die größten Anbieter nicht: Gmail und Microsoft
verlangen für IMAP-Zugriff in der Regel OAuth beziehungsweise
anbieterspezifische Authentifizierung, teils mit eigenem Freigabeprozess. Die
Wahl zwischen Gmail, Microsoft, generischem IMAP oder etwas anderem sollte
deshalb **anhand der Anbieter realer Beta-Nutzer** getroffen werden, nicht
vorab am Schreibtisch. Bis dahin gilt: Credential-Speicher und Sync-State so
entwerfen, dass sowohl Passwort- als auch OAuth-Authentifizierung möglich
bleiben.

---

## 13. Retrieval / RAG

### Ist-Zustand

| Baustein | Umsetzung | Urteil |
|---|---|---|
| Keyword-Suche | ILIKE auf Titel → Snippet → Chunk, Dedup nach Pfad | funktioniert; kein Ranking, kein Stemming |
| Semantische Suche | pgvector Cosine, exakter Scan, `limit*4` Kandidaten, Dedup auf bestes Chunk | solide |
| Kombination | **Entweder-oder mit Fallback** (`index.py:572-589`) | **Schwachstelle** — kein Hybrid |
| Chunking | 1500 Zeichen / 200 Overlap, Whitespace-Breaks | angemessen |
| Embeddings | OpenAI `text-embedding-3-small`, 1536 fix, **sequenziell** pro Chunk | Kosten/Latenz bei Massenimport |
| Metadaten pro Chunk | nur `chunk_index` | zu wenig für PDF-Seiten, Mail-Header |
| Index-Sync | mtime-inkrementell, Beat 60 s, Löschung per Abgleich | trägt für Dateien |
| RAG-Kontext | 5 **Notizen** × ~400 Zeichen | **Schwachstelle** |
| Quellen | LLM nennt Titel → gegen Treffer validiert | gut, Halluzination unmöglich |
| Kein Treffer | feste Antwort ohne LLM-Call | vorbildlich |
| Berechtigungen | **keine** | ok für Single-User, Blocker ab Connector/Team |
| Modellwechsel | keine Metadaten, keine Re-Index-Routine | Blocker für lokale Embeddings |

### Die drei wirksamsten Verbesserungen

1. **Chunk-Kontext statt Snippet-Kontext.** Die semantische Suche kennt den
   passenden Chunk und wirft ihn weg, um ein 400-Zeichen-Präfix der Notiz zu
   senden. Den Treffer-Chunk plus Nachbar-Chunks zu übergeben ist eine kleine
   Änderung in `answer.py` mit großer Wirkung. In der Roadmap steckt das in
   E40-1 („Chat-Seite") — es sollte davon getrennt und als reine
   Retrieval-Story vorgezogen werden.
2. **Hybrid statt Entweder-oder** (E37-1, RRF über `tsvector` + kNN). Löst genau
   die Fälle, an denen ein persönliches Gedächtnis sonst scheitert: Eigennamen,
   Rechnungsnummern, Firmennamen.
3. **Eval-Harness** (E37-3). Ohne Messung ist jede weitere Retrieval-Änderung
   Meinung. 30–50 deutsche Goldfragen gegen einen Fixture-Vault, Hit-Rate@5 in
   CI, ohne LLM-Kosten. Das ist auch die Voraussetzung dafür, den externen Rat
   „nimm einen Reranker" jemals faktenbasiert zu beantworten.

### Was bei zusätzlichen Quellen bricht

| Aspekt | Bruch |
|---|---|
| Identität | E-Mails/Termine haben keinen `vault_path`; UNIQUE-Constraint blockiert |
| Sync | `rglob` über den Vault findet nichts Externes; mtime existiert nicht |
| Granularität | Ein Mail-Thread, ein Kalendereintrag und eine Notiz sind verschieden große Einheiten |
| Zeitbezug | „Welche Termine nächste Woche?" braucht Zeitfilter im Retrieval — heute gibt es nur `days` im Digest |
| Löschung | Externes Objekt verschwindet → kein Tombstone, Ghost-Einträge im Index |
| Kosten | Massen-Embedding eines Postfachs bei sequenziellen Einzel-Calls |
| Skalierung | Kein ANN-Index; bei Postfach-Größenordnung wird der exakte Scan spürbar |
| Berechtigung | Alle Quellen gleich sichtbar für jeden authentifizierten Client |
| Vertrauen | Externe Inhalte gehen unmarkiert in dieselben Prompts wie Instruktionen |

Punkt 1, 5 und 9 sind Fundamentthemen; die übrigen entstehen mit dem Connector
und dürfen dort gelöst werden.

---

## 14. Provenance / Trust

**Provenance existiert heute nur als Nebenprodukt.** `entries` weiß, dass etwas
aus Telegram kam (`telegram_chat_id`, `telegram_update_id`); der Vault-Index
weiß nichts über Herkunft; die Markdown-Datei enthält kein Herkunftsfeld.

### Was das Produkt braucht

| Frage des Nutzers | Heute beantwortbar? | Wofür nötig |
|---|---|---|
| „Woher kam diese Notiz?" | teilweise (nur Telegram, nur in der DB) | Vertrauen |
| „Ist dieser Satz von mir oder von der KI?" | **nein** | Vertrauen, Korrektheit über Jahre |
| „Welche Passagen wurden an das Modell gesendet?" | **nein** (E40-3 geplant) | Privacy-Versprechen |
| „Welches Modell hat das erzeugt?" | teilweise (`prompt_version` in DB) | Reproduzierbarkeit |
| „Auf welchen Quellen beruht diese Antwort?" | **ja** | RAG-Vertrauen |
| „Wer hat das erfasst?" (Team) | nein | Phase O |

### Trust und Korrekturen

Wenn Seiton automatisch sortiert, macht es Fehler — das ist keine Möglichkeit,
sondern eine Gewissheit. Das Produkt braucht deshalb einen **Korrekturpfad, der
so billig ist wie das Erfassen**. Heute existiert er praktisch nicht.

Empfohlenes Minimum für V1 (bewusst ohne Lernmechanik):

1. **Ergebnis zeigen**, wie es die UI bereits tut — inklusive vollem Pfad, auch
   in Telegram.
2. **Verschieben und umbenennen in der UI**, mit Index-Aktualisierung.
   Nicht neu erfinden: die Notes-Seite kann bereits laden, speichern, löschen.
3. **Undo kanalunabhängig** und bei `append` auch im Dateiinhalt vollständig.
4. **Korrekturen protokollieren, nicht auswerten.** Wer später aus Korrekturen
   lernen will, braucht die Daten; wer heute eine Lernschleife baut, optimiert
   gegen ein Modell ohne Nutzer. Ein Feld genügt.

Der Weg zu „Seiton lernt aus Korrekturen" führt nicht über Fine-Tuning, sondern
über gespeicherte Nutzerregeln, die dem Klassifikationsprompt beigelegt werden
(„Fitness-App-Themen gehören nach Projects/Fitness App"). Das ist ein späteres,
kleines Feature — und keine Learning Engine.

---

## 15. Read / Assist / Action Model

### Heutiger Stand

Der Antwortpfad ist **read-only, und das ist eine dokumentierte
Architektur-Invariante**: keine Tools im `/ask`-Pfad, Antworten werden nie als
Aktion interpretiert. Das ist die wichtigste Sicherheitseigenschaft des
Systems und sollte explizit als Invariante mit Testabdeckung festgeschrieben
werden (E40-4).

**Es gibt aber bereits einen schreibenden Pfad mit zu weiten Rechten:** Der
MCP-Server exponiert `capture_note` mit demselben globalen `SEITON_API_KEY` wie
die Lesewerkzeuge (`examples/mcp/seiton-brain-mcp/server.py:114-127`). Ein
LLM-Agent in Cursor oder Claude Desktop kann damit ungefragt in den Vault
schreiben. Das ist **kein theoretisches, sondern ein heutiges**
Least-Privilege-Problem, wenn auch mit begrenztem Schaden. E36-1 (scoped Keys)
ist die richtige Antwort und sollte vorgezogen werden.

### Empfohlenes Ebenenmodell

| Ebene | Beispiel | Berechtigung | Bestätigung | Protokoll |
|---|---|---|---|---|
| **READ** | Notizen durchsuchen, E-Mails lesen | Read-Scope, `ai_access`-gefiltert | keine | optional (E36-2) |
| **WRITE-OWN** | Notiz im eigenen Vault anlegen | Write-Scope, nur eigener Vault | keine im Capture-Kanal; **ja** bei Agent-Kanälen | ja |
| **ASSIST** | E-Mail-Entwurf, Terminvorschlag | Read + Entwurfsablage | Ergebnis ist ein Vorschlag, kein Vollzug | ja |
| **ACT** | E-Mail senden, Termin anlegen | eigener Write-Scope pro Connector, separat erteilt | **immer, pro Aktion** | ja, unveränderlich |

**Prinzipien:**

1. **Ein Token bedeutet keine Erlaubnis.** Ein vorhandener Connector-Token
   berechtigt nur zu dem, was der Nutzer für diesen Anwendungsfall freigegeben hat.
2. **Tool-Allowlist pro Kanal.** Der Antwortpfad hat null Tools. Der Assist-Pfad
   hat lesende Tools. Der Aktionspfad hat genau die freigegebene Aktion.
3. **Bestätigung ist Teil der Aktion, nicht der Benutzeroberfläche.** Die
   Freigabe wird serverseitig geprüft, nicht im Frontend ausgeblendet.
4. **Assist vor Act.** Ein Entwurf, den der Nutzer selbst absendet, hat 90 % des
   Nutzens bei 5 % des Risikos. Diese Stufe ist möglicherweise das Endziel, nicht
   nur eine Zwischenstufe.
5. **Widerruf muss sofort wirken** — Token löschen beendet laufende Berechtigungen.

**Zeitpunkt:** Nichts davon vor der Beta außer den scoped Keys. Das Modell gehört
in einen ADR, sobald der erste schreibende Connector konkret wird — nicht vorher.

---

## 16. Security & Privacy Model

### Bestand

| Prinzip | Stand | Beleg |
|---|---|---|
| Local-first | **erfüllt** — alles läuft auf der Box, API bindet auf 127.0.0.1 | `docker-compose.yml` |
| Self-Hosting | **erfüllt** — drei Profile, Installer, Doctor | `scripts/` |
| Secrets zentral | **erfüllt** — ausschließlich `app/config.py`/`.env`, nichts hartkodiert | Konvention + Code |
| Secrets at-rest | **teilweise** — optionaler OS-Keyring; `UI_PASSWORD` fehlt darin | `app/cli/keyring_store.py:18-24` |
| Verschlüsselung at-rest (DB/Vault) | **fehlt** — `raw_input` im Klartext | `app/models/entry.py` |
| API-Auth | **erfüllt** — Pflicht-Key, timing-safe, 503 ohne Key | `app/api/auth.py` |
| Least Privilege | **fehlt** — ein Key, alle Rechte | E36-1 |
| UI-Auth | **erfüllt** — localhost-Guard proxy-sicher fail-closed, Session-HMAC, Lockout | `app/setup/security.py`, `app/ui/auth.py` |
| Tenant Isolation | **per Instanz** — kein Multi-Tenant-Konzept | bewusst (Phase O) |
| Audit Logging | **teilweise** — strukturierte Logs mit Korrelation, kein Sicherheitsprotokoll | `app/logging_config.py` |
| Log-Hygiene | **verletzt** — Voice-Transkript (80 Zeichen) landet im Log | `app/worker/tasks.py:141` |
| Sichere Updates | **teilweise** — `update.sh` mit Backup; kein Signaturkonzept | E46 |
| Backup/Restore | **teilweise** — Backup-UI und Skript; Restore-Verifikation offen | E29-4 |
| Export | **fehlt** strukturiert — Vault ist inhärent exportierbar | E31-2 |
| Vollständige Löschung | **fehlt** | E31-1 |
| Data Retention | **fehlt** | E31-3 |
| Sichere Connector-Sync | entfällt (keine Connectoren) | — |
| Outbound-Signatur | **fehlt** — Webhooks ohne HMAC, `summary` im Klartext | `app/webhooks/outbound.py:30-51` |

### Bewertung

Für ein Single-User-Self-Hosting-Produkt ist das Sicherheitsniveau **überdurchschnittlich**.
Die Phase-L-Arbeit (E27) hat die relevanten Web-Risiken adressiert. Was fehlt,
ist nicht Härtung, sondern **Privacy-Substanz**: Ein Produkt, das Privacy als
Hauptargument verkauft, muss Löschung, Export und Log-Hygiene liefern, bevor es
das erste Mal Geld kostet. E31 ist damit kein „nice to have" vor E21-2, sondern
Bestandteil des Verkaufsversprechens.

**Konkrete Sofortmaßnahmen mit hohem Verhältnis von Wirkung zu Aufwand:**
Transkript-Snippet aus dem Log entfernen · `UI_PASSWORD` in den Keyring
aufnehmen · Webhook-HMAC (E35-2) · Timing-safe Vergleich beim
Telegram-Webhook-Secret (E27-5).

---

## 17. Prompt Injection / Untrusted Data

### Heutiges Risiko: real, aber begrenzt

Alle LLM-Aufrufe verwenden **eine einzige `user`-Nachricht**, in der
Prompt-Template und Fremdinhalt per String-Ersetzung vermischt werden — es gibt
keine `system`-Rolle, keine Trennzeichen, keine Markierung von untrusted content
(`app/llm/openai_provider.py:76-81,152-155`).

**Angriffspfade heute:**

1. **Dokument-Capture** (höchste Relevanz): Ein PDF mit eingebetteten Anweisungen
   geht ungefiltert in `{input}`. Wirkung: falsche Kategorie, falscher Titel,
   Append an eine falsche Notiz, manipulierter `summary`-Text im Vault.
2. **Corpus-Poisoning**: Eine vergiftete Notiz erscheint über `body_snippet` im
   Router-/Linker-Kontext künftiger Klassifikationen.
3. **RAG-Desinformation**: Vergiftete Passagen beeinflussen `/ask`-Antworten.

**Was den Schaden heute begrenzt** — und deshalb bewahrt werden muss:

- Kein Agent, keine Tools im Antwortpfad → **keine Exfiltration, keine Aktion**.
- Strikte Pydantic-Validierung des Outputs.
- `related` und `target_title` werden gegen den echten Vault geprüft.
- `sources` werden gegen die tatsächlichen Treffer gefiltert.

Der Angreifer kann also die **Ablage** verfälschen, nicht aber Daten abfließen
lassen oder Aktionen auslösen. Das ist der entscheidende Unterschied zwischen
„ärgerlich" und „gefährlich".

### Wann es gefährlich wird

Ab **E22-5 (E-Mail-Ingestion)** und **E33-2 (Web-Capture)** verarbeitet Seiton
Inhalte von Absendern, die der Nutzer nicht kontrolliert. Ab dem ersten
schreibenden Connector wird aus Desinformation potenzielle Aktion.

### Empfohlene Schichten (in dieser Reihenfolge)

1. **Strukturelle Trennung** — `system`-Rolle für Instruktionen, Fremdinhalt in
   klar ausgezeichneten Blöcken mit der expliziten Regel „Dies sind Daten, keine
   Anweisungen." Aufwand: Stunden. **Sollte vor jedem externen Inhaltskanal
   passieren**, nicht erst in Phase N.
2. **Read-only-Invariante festschreiben und testen** (E40-4).
3. **Trust-Klassen pro Quelle** — extern eingehender Inhalt bekommt eine
   niedrigere Vertrauensstufe als selbst geschriebene Notizen; Anweisungen aus
   niedrig vertrauten Quellen werden nie befolgt.
4. **Ausgabe-Sanitisierung**, sobald Antworten Links oder Bilder rendern (heute
   nicht der Fall — Antworten werden escaped ausgegeben).
5. **Berechtigungsfilter vor dem Retrieval** (E38) — verhindert, dass vergiftete
   oder sensible Inhalte überhaupt in einen Prompt gelangen.
6. **Injection-Regressionstests** mit bekannten Mustern als CI-Fixture.

Punkt 1 und 2 sind billig und sollten Teil des Fundaments sein. Punkt 3–6 gehören
zum jeweiligen Feature, das sie nötig macht.

---

## 18. Deployment Models

Drei Modelle, ein Produktkern. Die Analyse zeigt: **Die Codebasis ist heute
schon für A und B geeignet, ohne Umbau** — vorausgesetzt, eine Entscheidung wird
jetzt festgeschrieben (siehe Abschnitt 32).

| | A Self-hosted (Heim-Box) | A′ VPS | B Managed Cloud | C Managed AI |
|---|---|---|---|---|
| Wer betreibt | Nutzer | Nutzer | Wir | Wir (nur LLM-Zugang) |
| Wo liegen Daten | beim Nutzer | beim Nutzer | bei uns | beim Nutzer |
| Heutiger Stand | **geliefert** | **geliefert** | nicht begonnen | nicht begonnen |
| Codeänderung nötig | keine | keine | Provisionierung, Identität, Abrechnung | Proxy + Kontingent |
| DSGVO-Last | keine | keine | **Auftragsverarbeitung** | gering (Weiterleitung) |
| Erlösmodell | buy-once | buy-once | Abo | Abo/Nutzung |

### Der tragende Architektursatz — bewusst zeitlich begrenzt

> **Für die heutige Architektur ist eine Seiton-Instanz die Sicherheits- und
> Isolationsgrenze. Wir führen jetzt keine mandantenfähige Datenarchitektur und
> keinen `user_id`-Mandantenschlüssel ein.**

Wenn das jetzt festgeschrieben wird, gilt:

- Managed Cloud in einer ersten Variante = **Single-Tenant-Provisionierung**
  derselben Compose-Stacks. Es entsteht kein zweites Produkt, nur
  Betriebsautomatisierung.
- Teams (Phase O) = **Shared Instance** mit Nutzerkonten *innerhalb* der Grenze.
  Nutzerkonten dürfen und sollen für Authentifizierung, Attribution und
  Berechtigungen existieren — nur nicht als Mandantenschlüssel.
- Solange diese Annahme gilt, ist kein Multi-Tenant-Umbau nötig.

**Was das ausdrücklich nicht ist:** eine irreversible Festlegung für alle
künftigen Cloud-Szenarien. Ob eine spätere Cloud eine andere
Isolationsarchitektur braucht — etwa wegen Betriebskosten pro Instanz,
Skalierung oder einer anderen Zielgruppe —, ist eine **bewusste zukünftige
Entscheidung bei nachgewiesenem Bedarf**, kein heute auszuschließender Fall.

Der Wert der Entscheidung liegt darin, dass sie heute nichts kostet und
verhindert, dass beim Einstieg in Teams oder Cloud beiläufig ein
Mandantenmodell in die Datenmodelle wandert, das niemand entschieden hat. Sie
steht implizit bereits in Phase O und ADR 0007 Option 1 — sie sollte explizit
und mit dieser Befristung festgehalten werden.

---

## 19. Self-hosting / VPS

**Bewertung: gut gelöst, mit einer klar benennbaren Restreibung.**

Vorhanden: Docker Compose in drei Profilen · Installer für Linux/macOS/Windows ·
`init.sh`, `doctor.sh`, `update.sh`, `deploy-vps.sh` · Setup-Wizard im Browser ·
Reverse-Proxy-Beispiele (Caddy, nginx, Cloudflare Tunnel) · Telegram-Long-Polling,
das den öffentlichen Port überflüssig macht — eine wirklich gute Entscheidung.

Der Nutzer kontrolliert Daten, Datenbank, Secrets und LLM-Konfiguration
vollständig. BYOK ist der einzige heute unterstützte Modus. Ollama und
whisper.cpp sind angebunden; lokale **Embeddings** fehlen (E39-1) — das ist die
einzige echte Lücke im Versprechen „nichts verlässt das Gerät".

**Restreibungen für nicht-technische Nutzer:**

| Hürde | Bewertung |
|---|---|
| Docker installieren | unvermeidbar auf diesem Weg; akzeptabel für die Zielgruppe |
| Repository klonen | vermeidbar durch ein Release-Archiv |
| **Manueller Neustart nach dem Setup-Wizard** | vermeidbar und störend — der Wizard sollte den Neustart selbst auslösen |
| Absoluter Host-Pfad für den Vault | erklärungsbedürftig; ein Standardpfad mit „Ich habe schon einen Vault"-Alternative wäre einfacher |
| OpenAI-Konto + API-Key | die größte Hürde für Laien — genau das Argument für Managed AI |
| Von unterwegs erreichbar (Tailscale) | für Laien die zweitgrößte Hürde; heute durch Telegram umgangen |

**Wichtige Erkenntnis:** Telegram löst derzeit die schwerste Consumer-Hürde
(mobiler Zugriff ohne Netzwerkkonfiguration). Telegram zurückzustufen, ohne
diese Hürde anders zu lösen, würde das Produkt für die Zielgruppe schlechter
machen — siehe Abschnitt 25.

---

## 20. Managed Cloud

**Konzeptionelle Bewertung, keine Umsetzungsempfehlung für heute.**

| Vorteil | Realistisch? |
|---|---|
| Onboarding ohne Docker | ja — der größte Hebel |
| Kein eigener API-Key nötig | nur zusammen mit Managed AI |
| Automatische Updates/Backups/Monitoring | ja |
| Multi-Device sofort | ja (heute über Tailscale gelöst) |

| Herausforderung | Gewicht |
|---|---|
| DSGVO-Auftragsverarbeitung für hochsensible Daten | **sehr hoch** — AVV, TOMs, Löschkonzept, EU-Region, Auskunftspflichten |
| Betriebsverantwortung 24/7 für einen Solo-Entwickler | **sehr hoch** — bricht direkt mit dem Ziel „passives Einkommen" |
| Kostendeckung pro Instanz (~5–10 €/Monat Infrastruktur + LLM) | hoch — bestimmt den Mindestpreis |
| Identität und Abrechnung | mittel — neuer Code, aber Standardproblem |
| Incident Response | hoch |
| Tenant Isolation | **niedrig**, wenn Single-Tenant-Instanzen gewählt werden |

**Einschätzung:** ADR 0007 empfiehlt bereits Option 1 (Single-Tenant-Instanzen) —
das ist richtig, weil es die Codebasis nicht anfasst. Die eigentliche Frage ist
nicht technisch, sondern persönlich: **Ist der Entwickler bereit, Betriebs- und
Datenschutzverantwortung für fremde, hochsensible Daten zu tragen?** Solange die
Antwort nicht eindeutig ja ist, sollte ADR 0007 auf *Proposed* stehen bleiben und
E24 gesperrt bleiben. Ein schlecht betriebener Cloud-Dienst für Bewerbungs- und
Gesundheitsnotizen ist ein existenzielles Risiko, kein Umsatzkanal.

**Eine dritte Option verdient mehr Aufmerksamkeit, als sie in ADR 0007 bekommt:**
Verteilung über Umbrel, Start9, CasaOS oder PikaPods. Das liefert „gehostet
ohne eigenen Betrieb", kostet fast nichts und erreicht exakt die
privacy-affine Zielgruppe. Als Distributionskanal ist das vor der Cloud-Frage zu
prüfen.

---

## 21. Managed AI / BYOK

**Architektonisch koexistieren BYOK, lokale Modelle und Managed AI problemlos** —
sie sind derselbe Provider hinter derselben Abstraktion, mit unterschiedlicher
Basis-URL und unterschiedlichem Schlüssel.

```
Aufgabe (classify | answer | embed | transcribe | vision)
        ↓
   Provider-Auflösung: Konfiguration + Trust-Klasse
        ↓
 ┌─────────────┬──────────────────┬─────────────────────┐
 │ BYOK        │ Lokal            │ Managed             │
 │ openai      │ ollama           │ Seiton-Proxy        │
 │ base_url ✕  │ base_url lokal   │ base_url = wir      │
 │ trust extern│ trust local      │ trust extern        │
 └─────────────┴──────────────────┴─────────────────────┘
```

**Der Schlüssel ist E39-2** (generischer OpenAI-kompatibler Provider mit freier
`base_url`). Damit wird Managed AI serverseitig zu einem dünnen Proxy und
clientseitig zu **null neuem Code** — dieselbe Konfiguration wie LM Studio, vLLM,
Azure OpenAI oder ein EU-Gateway. Diese eine Story ist strategisch wertvoller,
als ihre Priorisierung (Phase N, unten) vermuten lässt.

**Ergänzend nötig, wenn Managed AI kommt:** Kontingent und Kostendeckel,
Modell-Whitelist, Verbrauchsanzeige für den Nutzer, und die explizite
Trust-Deklaration des Proxys als `external`.

**Wichtig:** Managed AI erfordert **kein** eigenes GPU- oder Modell-Hosting und
ist unabhängig von der Cloud-Frage — es ist auch für Self-Hosting-Kunden
verkaufbar („kein eigener OpenAI-Key nötig"). Damit ist es die risikoärmste
Monetarisierungsachse überhaupt: kein fremdes Datenhosting, wiederkehrender
Umsatz, löst nachweislich die größte Onboarding-Hürde.

---

## 22. Backend Technology Review

**Gesamturteil: KEEP. Es gibt keinen Rewrite-Grund — weder heute noch absehbar.**

| Technologie | Bewertung | Begründung |
|---|---|---|
| **Python** | **KEEP** | Das Produkt ist zu ~70 % Dokumentverarbeitung und LLM-Orchestrierung. pypdf, python-docx, python-pptx, Tesseract-Bindings, whisper.cpp, Embedding-Bibliotheken und jedes neue KI-Werkzeug erscheinen hier zuerst. In Go oder Rust wäre exakt der Teil, der das Produkt ausmacht, ein Nachbauprojekt. |
| **FastAPI** | **KEEP** | Async, Pydantic-integriert, automatisches OpenAPI. Kein Engpass in Sicht — die Latenz stammt zu >95 % vom LLM. |
| **Pydantic** | **KEEP** — strategisch | Die strikte Validierung von LLM-Ausgaben ist eine tragende Sicherheitseigenschaft, kein Komfort. |
| **Celery** | **KEEP**, mittelfristig **EVOLVE** | Angemessen. Alternative (Postgres-basierte Queue) würde einen Dienst sparen; das lohnt sich nur, falls Redis je zum Betriebsproblem wird. Kein Anlass. |
| **Redis** | **KEEP** | Broker; künftig auch für verteilte Rate-Limits (E27-5). |
| **PostgreSQL** | **KEEP** — strategisch | Volltext, Vektoren, JSON, Transaktionen in einem Dienst. Genau der richtige Zuschnitt. |
| **pgvector** | **KEEP** | Eine dedizierte Vektordatenbank wäre ein zusätzlicher Dienst mit eigener Konsistenz- und Backup-Frage — für ein Self-Hosting-Produkt ein Rückschritt. Bei sehr großen Beständen: HNSW-Index ergänzen, nicht Technologie wechseln. |
| **SQLAlchemy async** | **KEEP** | Solide, mit Alembic gekoppelt. |
| **Alembic** | **KEEP** | Migrationen sind für ein Self-Hosting-Produkt mit Auto-Update unverzichtbar. |
| **LLM-Abstraktion** | **EVOLVE** — jetzt beginnen | Siehe Abschnitt 26. Die Abstraktion leckt an mehreren Stellen. Kein Rewrite, sondern Aufräumen. |

### Sachlicher Vergleich

| | Python (heute) | TypeScript/Node | Go | Rust |
|---|---|---|---|---|
| KI-/Dokument-Ökosystem | ●●●●● | ●●●○○ | ●●○○○ | ●●○○○ |
| Nebenläufigkeit | ●●●○○ | ●●●●○ | ●●●●● | ●●●●● |
| Rohleistung | ●●○○○ | ●●●○○ | ●●●●● | ●●●●● |
| Typsicherheit | ●●●○○ (mit mypy ●●●●○) | ●●●●○ | ●●●●○ | ●●●●● |
| Ein Sprachstack mit Frontend | ●○○○○ | ●●●●● | ●○○○○ | ●○○○○ |
| Wartbarkeit für einen Solo-Dev | ●●●●○ | ●●●●○ | ●●●○○ | ●●○○○ |
| Bestehende Codebasis + ~561 Tests | **erhalten** | **verloren** | **verloren** | **verloren** |

Rohleistung ist irrelevant, wenn jede Anfrage auf ein Sprachmodell wartet.
Der einzige nennenswerte Vorteil von TypeScript wäre ein gemeinsamer Sprachstack
mit einem künftigen React-Frontend — das rechtfertigt keinen Backend-Rewrite,
sondern höchstens die Wahl der Frontend-Sprache.

**Ein Rewrite wäre erst zu erwägen, wenn:** die Latenz nachweislich am Backend
liegt (heute nicht), oder eine harte Verteilungsanforderung entsteht (nicht in
Sicht), oder das Team wächst und Python nicht beherrscht (nicht der Fall).
Keine dieser Bedingungen ist erfüllt oder absehbar.

**Empfohlene Weiterentwicklung statt Rewrite:** schrittweises Type-Checking
(E45-6) — genau dort beginnen, wo LLM-Ausgaben und Vault-Pfade verarbeitet
werden.

---

## 23. Frontend Technology Review

**Empfehlung: B — Jinja2 + Vanilla JS behalten, mit definiertem Migrationsauslöser.**

### Ist-Zustand

~1.093 Zeilen JavaScript über sechs Screens, kein Build, kein `package.json`, kein
Framework. Die Komplexität verteilt sich sehr ungleich: Login 37 Zeilen,
Dashboard 158, Settings 289. Kein Screen hat komplexen geteilten Zustand, kein
Screen streamt, keiner pollt.

**Das ist für den heutigen Funktionsumfang die richtige Wahl** — kein
npm-Sicherheitsflächenzuwachs, kein Build im Auslieferungspfad eines
Self-Hosting-Produkts, sofort lesbar.

### Warum nicht Option D (jetzt migrieren)

Ein Rewrite würde ~1.100 Zeilen funktionierenden Code durch ein Toolchain-Projekt
ersetzen, das Docker-Image vergrößern, den Installer verkomplizieren und in einer
Phase Zeit kosten, in der noch kein Nutzer die UI benutzt hat. Es gibt keinen
Nutzerbefund, der das rechtfertigt.

### Migrationsauslöser — konkret

Migration wird wirtschaftlich, **sobald zwei der folgenden drei Bedingungen
gleichzeitig zutreffen**:

1. **Streaming-Chat mit Verlauf** wird gebaut (E40-1) — inkrementelles Rendern,
   Abbrechen, Nachrichtenzustände, Kontext-Inspektor. Das ist die erste Funktion,
   für die Vanilla-JS-Zustandshaltung wirklich teuer wird.
2. **Ein zusammenhängender Zustand wird von drei oder mehr Screens geteilt** —
   z. B. Nutzerrolle, Sichtbarkeitsfilter, aktive Quellenauswahl (Phase N/O).
3. **Die JS-Menge übersteigt ~2.500 Zeilen** oder dieselbe Zustandslogik
   existiert ein drittes Mal dupliziert.

**Vorgesehene Zielform, wenn ausgelöst:** Python-Backend bleibt unverändert.
React + TypeScript **nur für die dynamischen Flächen** (Chat, Notizen, Suche) als
gebündelte Assets ohne Server-Side-Rendering. Setup-Wizard, Login und Settings
bleiben Jinja — sie sind formularbasiert, müssen ohne Build funktionieren und
sind der einzige Teil, der auch bei kaputtem Frontend erreichbar sein muss.

**Vorbereitende Maßnahmen, die heute schon sinnvoll sind** (und keine Migration
darstellen): API-Antworten von der Darstellung sauber trennen (bereits so),
Designtokens in CSS statt verstreuter Werte (E47-4), keine Server-Templates mit
eingebetteter Geschäftslogik.

**Nicht empfohlen:** HTMX/Alpine als Zwischenschritt. Das wäre eine dritte
Frontend-Philosophie im selben Projekt und würde die spätere React-Entscheidung
nur verteuern.

---

## 24. Monolith / Service Boundaries

**Empfehlung: modularer Monolith beibehalten. Keine Dienstaufteilung — heute
nicht und absehbar nicht.**

Die heutige Aufteilung (`api`, `worker`, `beat`, `poller` als Prozesse einer
Codebasis) ist genau richtig: Prozesstrennung nach Betriebsanforderung, nicht
nach Domäne. Ein Self-Hosting-Produkt, das auf einem Mini-PC laufen soll, darf
nicht in Dienste zerfallen — jeder zusätzliche Dienst ist eine zusätzliche
Fehlerquelle im Wohnzimmer des Kunden.

**Wo Modulgrenzen dagegen schärfer werden sollten** (Code-Hygiene, nicht Verteilung):

| Grenze | Heute | Empfehlung |
|---|---|---|
| LLM-Provider | `OpenAIProvider` erbt nicht von `LLMProvider`; Ollama erbt von OpenAI | ABC durchsetzen, gemeinsame Chat-Schicht extrahieren |
| Retrieval | `app/vault/index.py` mischt Indexierung, Keyword-Suche, Vektorsuche und Digest-Sammlung | in `indexing` und `retrieval` trennen — Voraussetzung dafür, dass der Berechtigungsfilter genau **einen** Durchsetzungspunkt hat |
| Wissensidentität | `vault_path` überall | hinter `source`/`source_id` kapseln |
| Extraktoren | vault-dateigebunden | Bytes + MIME-Typ statt Pfad → wiederverwendbar für Upload und Connectoren |
| Kanäle | Telegram-Logik enthält Produktverhalten (`/undo`) | Produktverhalten in `services/`, Kanäle nur Transport |

Diese fünf Schnitte kosten wenig, sind rein interne Refactorings und machen
jeden späteren Connector, Kanal und Berechtigungsfilter billiger. Sie sind der
konkrete Inhalt von „für Erweiterung vorbereitet sein" — nicht Microservices.

---

## 25. Web / PWA / Mobile / Desktop

### Verifizierter Ist-Zustand — Bestätigung

| Behauptung | Ergebnis |
|---|---|
| Backend | **bestätigt** |
| Web-UI | **bestätigt** — sechs Screens, Jinja2 + Vanilla JS |
| PWA | **bestätigt, aber minimal** — installierbar; Service Worker cached ausschließlich statische Dateien; kein Offline-Capture, kein Share-Target, kein Push |
| Docker-/Shell-Installation | **bestätigt** |
| Setup-Wizard im Web | **bestätigt** — sechs Schritte, localhost-only |
| Keine native Desktop-App | **bestätigt** — kein Electron, kein Tauri, kein `package.json` |
| *(ergänzend)* keine native Mobile-App | **bestätigt** |

### Welche Clients braucht Seiton wirklich?

```
                    Seiton Core / API
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Web-UI (PWA)      Mobile Capture       Maschinen
   Browser            PWA + Shortcut      REST · MCP · Webhooks
   ── Pflicht ──      ── Pflicht ──       ── vorhanden ──
        │                   │
   alle Funktionen    Text · Sprache · Foto · Teilen
                            │
                    Telegram (Rückfallweg
                    für mobilen Zugriff)
```

### Braucht Seiton eine native Desktop-App?

**Nein.** Die Begründung aus ADR 0004 ist weiterhin schlüssig und wird durch die
Analyse gestützt:

1. Ein zweites Gehirn muss immer erreichbar sein; ein Laptop ist nicht immer an.
   Die Anwendung gehört auf die Always-on-Box, nicht auf den Client.
2. Die Web-UI läuft auf jedem Gerät mit Browser — inklusive der Geräte, für die
   nie eine Desktop-App gebaut würde.
3. Der Aufwand (Electron/Tauri, Signierung pro Plattform, Notarisierung,
   Auto-Update-Kanäle) ist für einen Solo-Entwickler erheblich und liefert
   **keine Fähigkeit**, die die Web-UI nicht hätte.

Der einzige theoretische Vorteil wäre ein globaler Tastenkürzel-Schnellerfassen.
Das lässt sich mit einem Systemskript gegen `POST /v1/capture` in wenigen Zeilen
lösen — und gehört als Rezept in die Dokumentation, nicht als Produkt in die
Roadmap. **E20-3 und E20-5 sind Streichkandidaten**, nicht nur „kein Nahziel".

### Braucht Seiton eine native Mobile-App?

**Heute nicht — und die Frage ist noch nicht entschieden.** PWA und Web bleiben
der erste und aktuelle Mobile-Ansatz; eine native App wird jetzt weder geplant
noch gebaut. Das ist bewusst **keine** Aussage darüber, dass sie nie sinnvoll
sein wird.

Der Grund für das Zurückstellen ist Erkenntnisstand, nicht Ablehnung: Die PWA
ist heute minimal (nur Asset-Cache, kein Share-Target, kein Offline-Capture,
kein Push), und die mobile Erfassung läuft faktisch über Telegram. Solange das
so ist, gibt es schlicht keine Messung, an der sich beurteilen ließe, ob eine
PWA ausreicht.

**Vorgehen:** Zuerst die PWA auf das machbare Niveau bringen (Share-Target auf
Android, iOS-Shortcut, Mikrofon, Upload, Offline-Warteschlange) und real
benutzen. Danach anhand der Nutzung neu bewerten.

**Mögliche Auslöser für eine Neubewertung** — jeweils nur, wenn sie sich in
realer Nutzung als relevante Hürde zeigen:

| Auslöser | Warum die Plattform hier begrenzt |
|---|---|
| Share Sheet | Auf iOS gibt es kein PWA-Share-Target; ein Shortcut ist ein Umweg |
| Sprach-/Kamera-UX | Aufnahme im Browser ist möglich, aber weniger direkt als eine native Erfassung |
| Push-Benachrichtigungen | Auf iOS an die Installation als Web-App gebunden und eingeschränkt |
| Offline-Capture | Im Browser über Service Worker machbar, mit Einschränkungen bei Speicherlebensdauer |
| Hintergrund-Upload | Größere Dateien und Sprachaufnahmen ohne geöffnete App |
| Biometrische Entsperrung | Im Web nur eingeschränkt verfügbar |

Native Mobile ist damit **DEFER mit definiertem Auslöserkatalog**, nicht
„unwahrscheinlich". Native Desktop bleibt davon unberührt ein Streichkandidat —
dort fehlt anders als bei Mobile jede Plattformfähigkeit, die die Web-UI nicht
ohnehin hätte.

---

## 26. LLM Strategy

### Ist-Zustand der Abstraktion: funktional, aber undicht

| Leck | Wirkung |
|---|---|
| `OpenAIProvider` erbt nicht von der ABC `LLMProvider` | Vertrag ist unverbindlich; Abweichungen fallen nicht auf |
| Ollama ist eine Unterklasse von OpenAI | „Multi-Provider" ist faktisch „OpenAI-kompatibel" — für die Praxis in Ordnung, als Architektur irreführend |
| Embeddings nur OpenAI; Factory wirft bei `ollama` | „Nichts verlässt das Gerät" ist heute **nicht** vollständig einlösbar |
| Vision nur OpenAI, synchroner Client, kein Interface | eigenständige Insel |
| Whisper über eine Fassade, aber ohne ABC | funktioniert; stiller Fallback von lokal auf OpenAI ist ein Trust-Problem |
| `answer`/`digest`-Prompts nicht versioniert | inkonsistent zu Router/Writer/Linker |
| Ein Chat-Modell für alle Aufgaben | keine Kosten-/Qualitätsdifferenzierung |
| Embedding-Dimension fest 1536 im Schema | Modellwechsel ist ohne Migration unmöglich |

### Sollten verschiedene Aufgaben verschiedene Modelle nutzen?

**Ja, aber als Konfigurationsmöglichkeit, nicht als Vorgabe.**

| Aufgabe | Anforderung | Empfehlung |
|---|---|---|
| Routing (Kategorie, Ziel) | schnell, günstig, häufig | kleines Modell — Standard |
| Writing (Zusammenfassung, Tags) | Sprachqualität | mittleres Modell |
| Linking | Präzision auf Titelliste | klein |
| RAG-Antwort | Qualität am sichtbarsten | größtes vertretbares Modell |
| Embeddings | Konsistenz, mehrsprachig | eigenes Modell, versioniert |
| Speech-to-Text | eigenes Modell | vorhanden |
| Vision | eigenes Modell | vorhanden |
| Agentic Planning | existiert nicht | bewusst offen lassen |

### Empfohlene Zielabstraktion

```
Aufgabe → Rolle → (Provider, Modell, Trust-Klasse)
                        ↓
        LLMProvider · EmbeddingProvider · TranscriptionProvider · VisionProvider
                        ↓
        openai | openai_compatible (freie base_url) | ollama
```

**Konkrete Prioritäten, in dieser Reihenfolge:**

1. **Embedding-Metadaten am Index** (Modell, Dimension, Version) + Content-Hash
   pro Chunk — E37-2. Ohne das ist kein Modellwechsel möglich, weder zu lokalen
   noch zu besseren Embeddings. Das ist eine **Fundamentstory**, keine
   Retrieval-Verbesserung.
2. **Generischer OpenAI-kompatibler Provider** — E39-2. Öffnet LM Studio, vLLM,
   Azure, EU-Gateways und Managed AI mit einer Story.
3. **Lokale Embeddings** — E39-1. Vervollständigt das Local-Only-Versprechen.
4. **Trust-Klasse pro Provider, kein stiller Fallback über Trust-Grenzen** —
   E38-3. Ein Ausfall des lokalen Modells darf niemals unbemerkt zu OpenAI führen.
5. **Optionale Modellwahl pro Rolle** — klein, jederzeit nachrüstbar.

**Ausdrücklich nicht empfohlen:** native SDKs für Anthropic oder Google. Die
OpenAI-kompatible Ebene deckt den Bedarf; jedes weitere SDK ist Wartungslast ohne
Produktnutzen.

---

## 27. UX Principles

### Bewertung des heutigen Ansatzes

Der Ideal-Flow lautet: *Gedanke → öffnen → sprechen/schreiben/teilen → fertig.*

| Schritt | Web-UI | Telegram |
|---|---|---|
| Öffnen | Browser/PWA-Symbol | Chat, immer offen |
| Schreiben | ein Feld, ein Klick (oder Cmd+Enter) | Nachricht |
| Sprechen | **nicht möglich** | Sprachnachricht |
| Teilen (Share Sheet) | **nicht möglich** | „Teilen an Telegram" |
| Datei | **nicht möglich** | Anhang |
| Fertig | Ergebnis mit Pfad und Tags | Bestätigung mit Ordner |

Das Anti-Muster (Kategorie wählen, Ordner wählen, Tags wählen, Titel schreiben)
ist **vollständig vermieden** — die Textarea verlangt nichts außer Text. Das ist
die zentrale UX-Stärke des Produkts und sollte niemals aufgeweicht werden, auch
nicht durch gut gemeinte „optionale" Felder.

### Die vier UX-Prinzipien, die daraus folgen

1. **Erfassen fragt nie nach Metadaten.** Ein Eingabefeld. Alles andere leitet
   die KI ab.
2. **Das Ergebnis ist sichtbar und korrigierbar.** Automatisierung ohne
   Sichtbarkeit erzeugt Misstrauen; Sichtbarkeit ohne Korrektur erzeugt Frust.
3. **Latenz wird angezeigt, nicht versteckt.** Die Klassifikation dauert
   sekundenlang. Heute blockiert der Aufruf synchron. Für Text ist das
   akzeptabel; für Dateien und Sprache nicht — dort braucht es einen sofortigen
   Empfangsnachweis und eine nachgereichte Bestätigung, wie Telegram es bereits
   macht.
4. **Nichts scheitert stumm.** Fehlermeldungen auf Deutsch, mit Handlung
   (E30-4). Heute: teils `alert()`, teils Inline-Text.

### Die eigentliche UX-Hürde liegt vor dem Produkt

Der Capture-Flow ist gut. Die Reibung steckt in Docker, Vault-Pfad, API-Key und
Neustart nach dem Setup. **Wer die Benutzererfahrung verbessern will, sollte
zuerst das Onboarding vereinfachen, nicht das Dashboard umgestalten** — der
Neustart-Schritt und ein Standard-Vault-Pfad sind die naheliegendsten Kandidaten.

---

## 28. Monetization Hypotheses

Ausdrücklich **Hypothesen**, keine Festlegung. Bewertet nach dem Grundsatz: Die
Architektur darf nicht verschlechtert werden, um Premium-Funktionen zu erzeugen.

| Achse | Attraktivität | Risiko | Verschlechtert das Produkt? |
|---|---|---|---|
| **Buy-once-Lizenz** (ADR 0004) | mittel | kein wiederkehrender Umsatz; nur passiv bei reibungsloser Installation | nein — Mechanik existiert (E21-1) |
| **Managed AI** (kein eigener Key nötig) | **hoch** | Kontingent und Kostendeckel zwingend | **nein** — löst eine echte Hürde |
| **Managed Hosting** | hoch | DSGVO, Betrieb, Bereitschaft | nein, aber hohe persönliche Last |
| **Managed Backup/Betrieb** als Zusatz | mittel | gering | nein |
| **Support/Einrichtungshilfe** | mittel | Zeit statt Software | nein |
| Zusätzliche Connectoren als Premium | mittel | teilt den Kern; Selfhoster erwarten Offenheit | **ja, wenn read-only Basiskanäle betroffen sind** |
| Erweiterte RAG-/AI-Funktionen als Premium | niedrig | trifft den Kern des Versprechens | **ja** — nicht empfohlen |
| Teams/Sitzplätze | mittel | erst mit Phase O | nein |
| Automatisierungen als Premium | niedrig | REST ist bereits offen | teilweise |

**Beobachtung:** Die attraktivsten Achsen (Managed AI, Managed Hosting, Support)
sind **Betriebsleistungen**, nicht künstlich beschnittene Funktionen. Das passt
zur Open-Source-Strategie (ADR 0005) und vermeidet den klassischen Fehler,
Produktqualität für Preisstufen zu opfern.

**Die einzige Monetarisierungsentscheidung mit Architekturwirkung** ist Managed
AI — und die wird durch E39-2 (freie `base_url`) ohnehin vorbereitet. Alles
andere kann später entschieden werden, ohne Code zurückzunehmen.

---

## 29. Roadmap Conflicts

Klassifikation ausgewählter Roadmap-Punkte gegen die Produktvision. **Es wird
nichts gestrichen** — dies ist ein Vorschlag zur Diskussion.

### KEEP — unverändert richtig

E27-5 Rate-Limits · E28-4 Idempotency-Key · E29-4 Backup-Retention ·
E29-6 Betriebsrobustheit · E30-2/4/5/6 UX-Pass · E31-1/2/3/4 Privacy ·
E45-5/6/14/15 Engineering · E46 komplett · E47 Designsystem ·
E37-1/2/3 Retrieval · E38 komplett · E39 komplett · E32-1/2/3 Vault-Interop ·
E34 Git-Backup · E35-1/2 REST + Webhooks.

### MODIFY — inhaltlich richtig, Zuschnitt oder Zeitpunkt anpassen

| ID | Änderungsvorschlag |
|---|---|
| **E29-5** Doku-Sync | **Deutlich vorziehen.** `ARCHITECTURE.md` beschreibt ein älteres System, und E45-2 weist Agents an, es zu lesen. Konkrete Fehlerquelle. |
| **E33-1** Provenance | **Erweitern und vorziehen.** Nicht nur `source` im Capture-Pfad, sondern `source`/`source_id` auch am Index — die quellenneutrale Identität ist die eigentliche Fundamentarbeit. |
| **E37-2** Embedding-Metadaten | **Als Fundamentstory führen**, nicht als Retrieval-Verbesserung. Blockiert lokale Embeddings und jeden Modellwechsel. |
| **E40-1** Chat-Seite | **Aufteilen.** Der Teil „Kontext = voller Treffer-Chunk + Nachbarn" ist eine reine Retrieval-Korrektur und sollte sofort passieren; die Chat-Oberfläche kann warten. |
| **E37-4** Ähnliche Notizen | **Vorziehen und erweitern** auf den Capture-Pfad: kNN statt Token-Overlap bei der Kandidatensuche. Größter Qualitätshebel im Bestand. |
| **E36-1** Scoped API-Keys | **Vorziehen.** Heute kann jeder MCP-Client mit dem Lese-Key schreiben. |
| **E22-5** E-Mail-Ingestion | Beibehalten, aber als **erster echter Connector** mit vollem Sync-State/Provenance/Injection-Modell führen — nicht als weiterer Capture-Kanal. **Anbieter und Protokoll offen lassen** (Gmail / Microsoft / generisches IMAP), Entscheidung erst anhand realer Beta-Nutzer. |
| **E23-4** Share-Target | Nach Plattform trennen: Android über Web Share Target; iOS **nur** über Shortcut — dort gibt es kein PWA-Share-Sheet. |
| **E40-4** Injection-Härtung | Die Prompt-Trennung (system/data, Delimiter) **vorziehen**, bevor externe Inhalte verarbeitet werden. |

### DEFER — richtig, aber zu früh

Phase O komplett (E41–E44, Teams) — bis mindestens fünf Einzelnutzer das Produkt
regelmäßig verwenden · E24 Cloud (bereits durch ADR 0007 gesperrt — Sperre
beibehalten) · E30-7 Ask-Verlauf (geht in E40-1 auf) · E26-5/E26-6
Template-Builder · E25-4 Systemgesundheit-Dashboard · **E23-5 nativer
Mobile-Wrapper** — Teil der offenen Native-Mobile-Frage, erst nach realer
PWA-Nutzung bewerten (Abschnitt 25); heute weder planen noch streichen.

### REMOVE CANDIDATE — Streichung zur Diskussion

| ID | Begründung |
|---|---|
| **E20-3 / E20-5** Native Desktop-App + Code-Signing | Kein Anwendungsfall, den die Web-UI nicht abdeckt (Abschnitt 25). Konsequent streichen statt „kein Nahziel". |
| **E15-5** Notion-Anbindung evaluieren | Der reale Bedarf ist Migration, nicht Synchronisation — und den deckt E32-3 (ZIP-Import) ab. Als eigenständige Evaluierung entbehrlich. |
| **E43-4** Aufgaben-Ansicht | Beginn eines Projektmanagement-Nachbaus; das Audit schließt PM bereits aus. |
| **E45-11** Linear | Bereits zurückgestellt; bei einem Solo-Entwickler mit GitHub Issues dauerhaft entbehrlich. |

### NEEDS DECISION — Produktentscheidung, nicht Umsetzung

Kanalparität (Voice und Upload außerhalb Telegrams) — **neu, nicht in der
Roadmap** · Ablagestruktur flach vs. hierarchisch — **neu, nicht in der
Roadmap** · Originaldateien behalten — **neu** · Embeddings-Standardwert ·
Isolationsgrenze = Instanz für den aktuellen Horizont (schriftlich festhalten,
ohne Festlegung für spätere Cloud-Szenarien) · ADR 0007 Cloud · E21-2
Verkaufskanal · Rolle von Telegram langfristig.

### Struktureller Befund

Die Roadmap ist **inhaltlich bemerkenswert gut** — die späteren Phasen enthalten
bereits Provenance, Hybrid Search, Berechtigungsschicht, lokale Modelle und
Injection-Härtung, also genau das Richtige. Das Problem ist nicht der Inhalt,
sondern dass **die Fundamentteile hinter Politur- und Prozessarbeit einsortiert
sind**. Vier Stories aus den Phasen M und N (E33-1, E37-2, E37-4, ein Teil von
E40-1) gehören vor die Beta; drei ganze Phasen dahinter.

---

## 30. Overengineering Risks

### Wo das Projekt bereits überplant ist

| Beobachtung | Bewertung |
|---|---|
| Phasen M/N/O umfassen ~50 Stories mit Aufwandsschätzung, ohne einen einzigen externen Nutzer | **höchstes Prozessrisiko** — jede dieser Stories basiert auf vermuteten Bedürfnissen |
| Sieben ADRs, mehrere Audit-Dokumente, drei Roadmap-Dateien, `current-state.md`, `engineering.md`, `production-ops.md` | Für einen Solo-Entwickler beachtlich diszipliniert, aber die Dokumentation wächst schneller als die Nutzerbasis — und `ARCHITECTURE.md` ist bereits veraltet, weil Pflege Aufwand ist |
| Teams-Phase (Rollen, Identität, Sichtbarkeit, Team-RAG) vollständig geplant | Das Produkt hat noch keinen einzelnen zufriedenen Nutzer |
| Prozessarbeit (E45, E46, E47) mit 30+ Stories | Wertvoll, aber sie erzeugt keinen Nutzerwert und läuft Gefahr, Produktarbeit dauerhaft zu verdrängen |
| Cloud-Edition mit ADR und fünf Stories geplant, Status *Proposed* | Korrekt gesperrt — gute Entscheidung |

### Was wirklich vor einer privaten Beta passieren muss

1. Kanalparität — Sprache und Dateien außerhalb Telegrams.
2. Ablagestruktur-Entscheidung (flach vs. hierarchisch) und Umsetzung.
3. Retrieval-Qualität: Chunk-Kontext, Hybrid, Embeddings standardmäßig aktiv.
4. Provenance und quellenneutrale Identität (drei Spalten).
5. Korrekturpfad in der UI.
6. Privacy-Substanz: Löschung, Export, Log-Hygiene (E31).
7. Onboarding ohne manuellen Neustart.
8. `ARCHITECTURE.md` aktualisieren.

### Was ausdrücklich warten kann

Teams · Cloud · Abrechnung · Connectoren · Aktionen · Designsystem-Vollausbau ·
Reranking · ANN-Index · Multi-Modell-Konfiguration · native Clients ·
Berechtigungs-UI · Version History · Automatisierungsrezepte.

### Architekturentscheidungen: jetzt vs. später

**Jetzt (weil später teuer):** Wissensidentität (`source`/`source_id`) ·
Embedding-Metadaten · Ablagestruktur · Isolationsgrenze · Prompt-Trennung
system/data · Provenance im Frontmatter.

**Später (weil später gleich teuer):** Frontend-Framework · Connector-Framework ·
Aktionsmodell · Cloud-Isolationsarchitektur jenseits der Einzelinstanz ·
Abrechnung · Reranker · ANN-Index · Modellwahl pro Rolle.

Die erste Liste ist kurz und billig. Genau darin liegt die Empfehlung dieses
Reviews: **wenige, günstige Fundamententscheidungen jetzt — alles andere nach
den ersten echten Nutzern.**

---

## 31. Proposed V1 / V1.5 / V2

### V1 — „Besser als der Inbox-Ordner" (private Beta, 3–5 Nutzer)

Maßstab: Ein Nutzer sagt nach zwei Wochen, dass es besser ist, als Gedanken in
Apple Notes oder Telegram-Saved-Messages zu werfen.

**Enthalten:**

- Erfassen von Text, Sprache und Dateien **über Web-UI, PWA und Telegram**
- Automatische Ablage ohne jede Nutzerentscheidung, in einer Struktur, die auch
  bei 500 Notizen noch sinnvoll ist
- Bestehendes Wissen wird zuverlässig erkannt und ergänzt (semantisch, nicht
  lexikalisch)
- Suche, die funktioniert: Hybrid, Embeddings standardmäßig aktiv
- `/ask` mit belegten Antworten und ausreichend Kontext
- Sichtbares Ergebnis und Korrektur in der UI
- Herkunft pro Notiz
- Installation in unter 20 Minuten ohne manuellen Neustart
- Löschung und Export
- Backup mit verifiziertem Restore

**Nicht enthalten:** Teams, Cloud, Abrechnung, Connectoren, Aktionen, Chat mit
Verlauf, lokale Embeddings, Berechtigungsschicht.

### V1.5 — „Mein Wissen, meine Regeln" (öffentliche Beta / erster Verkauf)

- Knowledge Chat mit Verlauf, Quellenanzeige und Kontext-Inspektor (E40-1/2/3)
- Berechtigungsschicht `ai_access` pro Ordner (E38) — das eigentliche
  Differenzierungsmerkmal am Markt
- Lokale Embeddings; vollständiger Local-Only-Modus (E39)
- URL-/Web-Capture (E33-2)
- Git-Backup und Versionshistorie (E34, E43-2)
- Scoped API-Keys und Zugriffsprotokoll (E36)
- Designsystem umgesetzt (E47)

### V2 — „Nicht nur meine Notizen" (Erweiterung)

- **Ein** Connector produktreif: E-Mail read-only (E22-5) als Kandidat, inklusive
  Sync-State, Provenance, Injection-Härtung — Anbieter und Protokoll werden erst
  anhand der Beta-Nutzer festgelegt
- Kalender read-only, wenn E-Mail sich bewährt hat
- Assist: Zusammenstellen, Zusammenfassen, Entwürfe — **ohne** Senden
- Anschließend **entweder** Teams (Phase O) **oder** Cloud (E24), nicht beides

Zwischen V1 und V1.5 gehört ein echter Nutzungszeitraum. Zwischen V1.5 und V2
gehört eine Entscheidung darüber, ob das Produkt in die Breite (Connectoren) oder
in die Tiefe (mehr Nutzer pro Instanz) wächst.

---

## 32. Decisions Required Now

Fünf Entscheidungen. Jeweils: Was ist zu entscheiden, warum jetzt, was es kostet,
wenn man wartet.

### D1 — Kanalparität: Erhalten Web-UI und PWA Sprache und Datei-Upload?

*Warum jetzt:* ADR 0004 erklärt die UI zur Hauptoberfläche, aber die
Hauptoberfläche kann heute weniger als der „optionale" Kanal. Das ist ein offener
Widerspruch zwischen Strategie und Produkt, der jede Aussage über die Rolle
Telegrams blockiert.
*Kosten des Wartens:* Telegram bleibt de facto Pflicht; das Datenschutzargument
wird angreifbar (alle Sprachnachrichten und Dokumente laufen über Telegram-Server).
*Empfehlung:* **Ja** — Upload und Mikrofonaufnahme in die Web-UI und REST. Die
Serverlogik existiert vollständig; es fehlt nur der Transport.

### D2 — Ablagestruktur: flach oder hierarchisch?

*Warum jetzt:* Die Struktur bestimmt Frontmatter, Kategorien, Prompts, Index und
UI. Vor allem aber: Sobald Nutzer echte Vaults befüllt haben, ist jede Änderung
eine Datenmigration in fremden Dateien.
*Kosten des Wartens:* Wächst mit jeder Notiz jedes Nutzers.
*Empfehlung:* **Hierarchisch, aus dem bestehenden Vault gelernt.** Kategorie
bleibt als Frontmatter-Label; der Zielpfad wird mehrstufig und die KI erhält die
tatsächlich vorhandene Ordnerstruktur als Auswahl, mit einer Regel für das
Anlegen neuer Zweige. Das ist die Voraussetzung für den beworbenen Magic Moment.

### D3 — Identität von Wissenselementen: `vault_path` oder `(source, source_id)`?

*Warum jetzt:* Drei Spalten und ein Constraint, plus etwa sechs Aufrufstellen.
Das ist ein halber Tag.
*Kosten des Wartens:* Nach dem ersten Connector ein Umbau mit Datenmigration
quer durch Index, Retrieval, API und UI.
*Empfehlung:* **Jetzt einführen** (Abschnitt 10). Ohne Connector zu bauen.

### D4 — Sind Embeddings im Auslieferungszustand aktiv?

*Warum jetzt:* Es entscheidet, welches Produkt ein neuer Nutzer tatsächlich
erlebt, und ob der Einrichtungsdialog Kosten transparent machen muss.
*Kosten des Wartens:* Jeder Beta-Nutzer bewertet ein Produkt, das nicht das
beworbene ist.
*Empfehlung:* **Ja, aktiv** — mit einer ehrlichen Kostenangabe im Setup und
einem Ausschalter. Ein Second Brain ohne semantische Suche ist eine Dateiablage.

### D5 — Ist die Instanz für den aktuellen Horizont die Isolationsgrenze?

*Warum jetzt:* Weil Phase O und ADR 0007 diese Annahme bereits stillschweigend
treffen, ohne sie festzuschreiben — und weil ein beiläufig eingeführter
Mandantenschlüssel die teuerste Art wäre, diese Entscheidung nicht zu treffen.
*Kosten des Wartens:* Gering, solange niemand anfängt, `user_id` in Datenmodelle
zu ziehen. Genau das ist aber der wahrscheinliche Fehler beim Einstieg in Teams
oder Cloud.
*Empfehlung:* **Ja, für den aktuellen Horizont, als ADR festhalten.** Für die
heutige Self-hosted-Architektur und eine mögliche erste Managed-Cloud-Variante
(Single-Tenant-Provisionierung) ist die Instanz die Isolationsgrenze; eine
mandantenfähige Datenarchitektur wird jetzt nicht eingeführt. Nutzerkonten
innerhalb einer Instanz sind für Authentifizierung, Attribution und
Berechtigungen ausdrücklich vorgesehen, dienen aber nicht der Mandantentrennung.
**Keine irreversible Festlegung:** Ob eine spätere Cloud eine andere
Isolationsarchitektur benötigt, wird bei nachgewiesenem Bedarf bewusst neu
bewertet.

---

## 33. Decisions That Can Wait

| Entscheidung | Frühester sinnvoller Zeitpunkt | Warum Warten billig ist |
|---|---|---|
| **Frontend-Framework** | Wenn zwei der drei Auslöser aus Abschnitt 23 eintreten | Die UI ist klein und wird ohnehin neu geschrieben, wenn sie migriert wird — Warten kostet nichts |
| **Cloud-Edition (ADR 0007)** | Nach V1.5 und nach einer persönlichen Bereitschaftsentscheidung | Single-Tenant-Provisionierung erfordert keinen Codeumbau; die Entscheidung ist betrieblich, nicht technisch |
| **Managed AI und Preisgrenzen** | Nach E39-2 (freie `base_url`) | Die technische Vorarbeit ist ohnehin für lokale Modelle nötig |
| **Native Mobile-App** | Nach realer PWA-Nutzung, anhand der Auslöser aus Abschnitt 25 | Die PWA ist heute minimal ausgebaut — es fehlt schlicht die Messung, an der sich die Frage entscheiden ließe |
| **Konkrete Connector-Auswahl (Anbieter/Protokoll) und Aktionsmodell** | Anhand der Anbieter realer Beta-Nutzer | Ohne zu wissen, welche Postfächer und Kalender die Nutzer tatsächlich haben, wäre die Wahl geraten — und Framework-Anforderungen kennt man erst nach der ersten Implementierung |
| **Reranker, ANN-Index, Modellwahl pro Rolle** | Nach dem Eval-Harness (E37-3) | Ohne Messung wäre es Meinung |
| **Teams (Phase O)** | Nach nachgewiesener Einzelnutzung | Baut auf E38 auf, das ohnehin zuerst kommt |
| **WhatsApp und weitere Messenger** | Vermutlich nie | Erfordert die WhatsApp Business API von Meta: kostenpflichtig, nicht self-hostbar, Genehmigungsprozess — widerspricht dem Produktversprechen |

---

## 34. Recommended Next Steps

**Ohne Umsetzung — Vorschlag für die Diskussion nach der externen Zweitmeinung.**

1. **Diesen Review lesen und die fünf Entscheidungen aus Abschnitt 32 treffen.**
   Alles Weitere hängt davon ab.
2. **Externe Zweitmeinung einholen**, mit den fehlenden Angaben aus der
   Chat-Zusammenfassung (Punkt L) als Kontext.
3. **`ARCHITECTURE.md` korrigieren** (E29-5 vorziehen). Kleiner Aufwand,
   verhindert falsche Agenten- und Entwicklerannahmen.
4. **Roadmap anpassen** — erst nach 1 und 2, und mit vorheriger Darstellung der
   vorgeschlagenen Änderungen. Der Vorschlag steht in Abschnitt 29.
5. **Ein Fundament-Arbeitspaket definieren** aus D2, D3, D4 plus
   Prompt-Trennung — vermutlich fünf bis sieben Stories.
6. **Kanalparität als eigenes Paket** (D1).
7. **Retrieval-Qualitätspaket:** Chunk-Kontext, Hybrid, Eval-Harness,
   kNN im Capture-Pfad.
8. **Privacy-Paket (E31) abschließen** — Voraussetzung dafür, für das Produkt
   Geld zu verlangen.
9. **Private Beta mit drei bis fünf Nutzern** — und erst danach über Phase M,
   N oder O entscheiden.

---

## Anhang A — Technologie-Entscheidungstabelle

| Thema | Status heute | Empfehlung | Zeitpunkt | Rewrite nötig? |
|---|---|---|---|---|
| **Python** | Backend-Sprache | **KEEP** | dauerhaft | nein |
| **FastAPI** | REST + UI-Routen | **KEEP** | dauerhaft | nein |
| **Pydantic** | LLM-Output-Validierung | **KEEP** (strategisch) | dauerhaft | nein |
| **PostgreSQL** | Entries, Index, Chunks | **KEEP** (strategisch) | dauerhaft | nein |
| **pgvector** | 1536-dim, exakter Scan | **KEEP**, ANN-Index bei Bedarf | ANN erst bei Messbarkeit | nein |
| **Redis** | Celery-Broker | **KEEP** | dauerhaft | nein |
| **Celery** | Worker + Beat | **KEEP** | dauerhaft | nein |
| **SQLAlchemy** | async ORM | **KEEP** | dauerhaft | nein |
| **Alembic** | Migrationen | **KEEP** | dauerhaft | nein |
| **Jinja2** | Server-Templates | **KEEP** | bis Migrationsauslöser | nein |
| **Vanilla JS** | ~1.093 Zeilen, kein Build | **KEEP** | bis 2 von 3 Auslösern | nein |
| **React/TypeScript** | nicht vorhanden | **LATER** — nur dynamische Flächen | bei Auslöser (frühestens E40) | nein — additiv |
| **Web-UI** | sechs Screens | **KEEP + ausbauen** (Upload, Mikrofon) | V1 | nein |
| **PWA** | installierbar, nur Asset-Cache | **EVOLVE** — Share-Target (Android), Offline-Queue | V1/V1.5 | nein |
| **Native Mobile** | nicht vorhanden | **DEFER** — PWA/Web zuerst; Neubewertung anhand definierter Auslöser | nach realer PWA-Nutzung | — |
| **Native Desktop** | nicht vorhanden | **REMOVE** (E20-3/E20-5 streichen) | — | — |
| **Telegram** | einziger Kanal für Voice/Datei | **KEEP als erstklassiger optionaler Kanal**; Parität herstellen | V1 | nein |
| **Obsidian-Vault** | Source of Truth für Notizen | **KEEP** — Modell C, vertraglich präzisieren | dauerhaft | nein |
| **Seiton Knowledge Model** | implizit, dateigebunden | **EVOLVE** — `source`/`source_id` + UNIQUE | **jetzt** | nein — 3 Spalten |
| **Notion** | nicht angebunden | **LATER** — Migration über ZIP-Import (E32-3); Sync nein | nach V2 | nein |
| **File-Connectoren** | Vault-Ordner + Telegram-Upload | **EVOLVE** — Upload in UI/REST; externe Ordner später | V1 / V2 | nein |
| **Email-Connectoren** | nicht vorhanden | **LATER** — read-only als Kandidat für den ersten Connector; Anbieter/Protokoll offen (Gmail · Microsoft · IMAP) | V2, Auswahl nach Beta-Nutzern | nein |
| **Calendar-Connectoren** | nicht vorhanden | **LATER** — nach E-Mail | nach V2 | nein |
| **RAG** | Top-5 Notizen × 400 Zeichen | **EVOLVE** — Chunk-Kontext, Hybrid, Eval | V1 | nein |
| **LLM-Provider-Layer** | ABC ungenutzt, Ollama erbt von OpenAI | **EVOLVE** — ABC durchsetzen, `openai_compatible` | V1/V1.5 | nein |
| **Local LLM** | Ollama (Chat) + whisper.cpp | **KEEP**, Embeddings ergänzen (E39-1) | V1.5 | nein |
| **BYOK** | einziger Modus | **KEEP** als Standard | dauerhaft | nein |
| **Self-Hosting** | drei Compose-Profile + Installer | **KEEP**, Onboarding glätten | V1 | nein |
| **VPS-Hosting** | `deploy-vps.sh` + Profil | **KEEP** | dauerhaft | nein |
| **Managed Cloud** | nicht vorhanden | **DEFER** — Single-Tenant, ADR 0007 gesperrt lassen | nach V1.5 | nein |
| **Managed AI** | nicht vorhanden | **LATER** — dünner Proxy über E39-2 | nach V1.5 | nein |
| **Actions** | nicht vorhanden (bewusst) | **LATER** — Assist vor Act, immer mit Freigabe | nach V2 | nein |
| **Security-Modell** | Single-Key, kein ACL, keine Prompt-Trennung | **EVOLVE** — scoped Keys, `ai_access`, system/data | V1 → V1.5 | nein |

---

## Anhang B — Produkt-Scope-Tabelle

| Capability | Core | Extension | Later | Out of Scope | Begründung |
|---|:--:|:--:|:--:|:--:|---|
| Text-Capture (alle Kanäle) | ✅ | | | | Einstiegspunkt des Produkts |
| Voice-Capture (alle Kanäle) | ✅ | | | | Der mobile Anwendungsfall; heute nur Telegram |
| Datei-/Dokument-Capture (alle Kanäle) | ✅ | | | | „Habe ich die Rechnung noch?" ist ein Kernversprechen |
| Originaldatei aufbewahren | ✅ | | | | Ohne sie ist die Rechnungsfrage nicht beantwortbar |
| Automatische Klassifikation | ✅ | | | | Der eigentliche Wert |
| Hierarchische Ablage | ✅ | | | | Ohne sie skaliert die Ablage nicht |
| Bestehendes Wissen ergänzen | ✅ | | | | Unterscheidet Second Brain von Notizapp |
| Markdown-Vault als Ablage | ✅ | | | | Portabilität = Vertrauen |
| Volltextsuche | ✅ | | | | |
| Semantische Suche | ✅ | | | | Standardmäßig aktiv, sonst nur Dateiablage |
| RAG mit Quellenangabe | ✅ | | | | Ohne Belege kein Vertrauen |
| Provenance / Herkunft | ✅ | | | | Nachträglich nicht rekonstruierbar |
| Korrektur und Undo | ✅ | | | | Automatisierung ohne Korrektur erzeugt Frust |
| Backup, Export, Löschung | ✅ | | | | Bedingung für Privacy als Verkaufsargument |
| Self-Hosting (Docker) | ✅ | | | | Produktdefinition |
| Web-UI + PWA | ✅ | | | | Hauptoberfläche |
| Telegram | | ✅ | | | Erstklassig optional — nach Kanalparität |
| REST-API | | ✅ | | | Vorhanden, offen |
| MCP-Server | | ✅ | | | Differenzierungsmerkmal, früh dran |
| Outbound-Webhooks | | ✅ | | | Automatisierung ohne Eigenbau |
| Git-Backup und Historie | | ✅ | | | Datenbesitz sichtbar machen |
| Knowledge Chat mit Verlauf | | ✅ | | | V1.5 |
| Berechtigungen `ai_access` | | ✅ | | | Marktlücke; V1.5 |
| Lokale Modelle (LLM, STT, Embeddings) | | ✅ | | | Vervollständigt Local-Only |
| Ähnliche Notizen / Duplikatwarnung | | ✅ | | | Kleiner Aufwand, täglicher Nutzen |
| URL-/Web-Capture | | ✅ | | | Erweitert Capture ohne neue Quelle |
| E-Mail lesen (read-only) | | | ✅ | | Kandidat für den ersten echten Connector, V2; Anbieter/Protokoll offen |
| Kalender lesen | | | ✅ | | Nach E-Mail |
| Notion lesen | | | ✅ | | Migration statt Sync bevorzugen |
| Externe Ordner indexieren | | | ✅ | | Nach quellenneutraler Identität |
| Assist (Entwürfe, Zusammenstellungen) | | | ✅ | | 90 % Nutzen, 5 % Risiko von Act |
| Aktionen (senden, anlegen) | | | ✅ | | Nur mit Freigabe pro Aktion |
| Teams / Shared Instance | | | ✅ | | Nach nachgewiesener Einzelnutzung |
| Managed Cloud | | | ✅ | | Betriebliche, nicht technische Entscheidung |
| Managed AI | | | ✅ | | Risikoärmste Monetarisierungsachse |
| Native Mobile-App | | | ✅ | | PWA/Web zuerst; Neubewertung anhand der Auslöser in Abschnitt 25 |
| Native Desktop-App | | | | ❌ | Kein Vorteil gegenüber der Web-UI |
| Obsidian-Ersatz (Editor, Graph, Plugins) | | | | ❌ | Direkter Wettbewerb mit dem eigenen Speicherformat |
| Notion-Ersatz (Datenbanken, Boards) | | | | ❌ | Anderes Produkt |
| E-Mail-Client | | | | ❌ | Lesen genügt |
| Kalender-Anwendung | | | | ❌ | Lesen genügt |
| Projektmanagement (Kanban, Sprints) | | | | ❌ | Über REST an bestehende Tools |
| Dateisynchronisation | | | | ❌ | Syncthing, iCloud, rclone existieren |
| Allgemeiner Chatbot ohne eigene Daten | | | | ❌ | Kein Alleinstellungsmerkmal |
| Mandantenfähige Datenarchitektur | | | | ❌ *(aktueller Horizont)* | Instanz ist die Isolationsgrenze; bei nachgewiesenem Cloud-Bedarf neu zu bewerten |
| Autonomer schreibender Agent | | | | ❌ | Unvereinbar mit dem Sicherheitsmodell |
| Eigenes Modell-/GPU-Hosting | | | | ❌ | Managed AI braucht das nicht |
| WhatsApp-Integration | | | | ❌ | Meta-Business-API: kostenpflichtig, nicht self-hostbar |
| Custom-n8n-Node | | | | ❌ | Bereits per ADR 0004 gestrichen |

---

## Anhang C — Empfohlene Zielarchitektur

```
                              CLIENTS
   ┌──────────────┬──────────────┬──────────────┬──────────────┐
   │  Web-UI/PWA  │   Telegram   │  REST-API    │  MCP-Server  │
   │ Text·Voice   │ Text·Voice   │  Automation  │  AI-Clients  │
   │ Datei·Share  │ Datei·Foto   │              │  (scoped)    │
   └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘
          └──────────────┴──────┬───────┴──────────────┘
                                ▼
   ╔══════════════════════ CAPTURE ═══════════════════════════╗
   ║  Transport → Extraktion (Bytes+MIME) → Transkription     ║
   ║  → Kandidatensuche (kNN)  → Klassifikation → Schreiben    ║
   ║  Provenance: source · source_id · actor · generated_by    ║
   ╚═══════════════════════════╤══════════════════════════════╝
                               ▼
   ╔═══════════════════ KNOWLEDGE CORE ═══════════════════════╗
   ║  Knowledge Item   UNIQUE(source, source_id)              ║
   ║  Chunks + Embeddings (Modell/Dimension/Hash am Index)    ║
   ║  Trust-Stufe · ai_access · Beziehungen                   ║
   ╚═════╤══════════════════════════════════════════╤═════════╝
         │ Notizinhalte = Dateien                   │ Metadaten,
         ▼ (Source of Truth, portabel)              ▼ Index, Ableitungen
   ┌───────────────────────┐          ┌──────────────────────────┐
   │  OBSIDIAN VAULT       │          │  PostgreSQL + pgvector   │
   │  Markdown · Anhänge   │          │  reproduzierbar          │
   │  Git-Historie         │          │  wegwerfbar              │
   │  ◄── Seiton schreibt  │          └──────────────────────────┘
   └───────────────────────┘
         ▲ read-only
   ┌─────┴─────────────────────────────────────────────────────┐
   │  EXTERNE CONNECTOREN  (später, unabhängig, read-only)     │
   │  Email · Kalender · Notion · externe Ordner · Web         │
   │  Auth → Scopes → Sync-State → Normalisierung              │
   └───────────────────────────────────────────────────────────┘
                               │
                               ▼
   ╔═══ PERMISSION / TRUST BOUNDARY ══════════════════════════╗
   ║  ai_access ∩ Kanal-Trust ∩ Scope   —   fail-closed       ║
   ║  Durchsetzung VOR dem Retrieval, genau ein Punkt         ║
   ╚═══════════════════════════╤══════════════════════════════╝
                               ▼
   ╔════════════════ RETRIEVAL / RAG ═════════════════════════╗
   ║  Hybrid (tsvector + kNN, RRF) → Chunk-Kontext            ║
   ║  → Antwort mit Belegen · READ-ONLY, keine Tools          ║
   ╚═══════════════════════════╤══════════════════════════════╝
                               ▼
   ╔═════════════════ LLM LAYER ══════════════════════════════╗
   ║  Rolle → (Provider, Modell, Trust)                       ║
   ║  openai · openai_compatible(base_url) · ollama           ║
   ║  Instruktion (system)  ‖  Daten (delimitiert, untrusted) ║
   ╚═══════════════════════════╤══════════════════════════════╝
                               ▼
   ╔══════ ASSIST  ──(explizite Freigabe pro Aktion)──► ACT ══╗
   ║  Entwurf · Zusammenstellung   │   Senden · Anlegen       ║
   ║  read + Ablage im Vault       │   eigener Write-Scope    ║
   ║                               │   Audit-Log, widerrufbar ║
   ╚═══════════════════════════════╧══════════════════════════╝

 ══════════════════════════════════════════════════════════════
   DEPLOYMENT — identischer Produktkern, eine Codebasis
 ══════════════════════════════════════════════════════════════
   Heim-Box / NAS  │  VPS            │  Managed Cloud (später)
   Daten b. Nutzer │  Daten b.Nutzer │  Daten bei uns
   BYOK / lokal    │  BYOK / lokal   │  + Managed AI
 ──────────────────┴─────────────────┴────────────────────────
   Unterschiede NUR in: Deployment · Identität · Abrechnung ·
   Betrieb · Provisionierung
   ANNAHME (aktueller Horizont, nicht endgueltig):
     Die Instanz ist die Isolationsgrenze; erste Cloud = Single-Tenant.
     Heute kein user_id als Mandantenschluessel. Nutzerkonten INNERHALB
     einer Instanz sind fuer Auth/Attribution/Berechtigungen vorgesehen.
     Andere Cloud-Isolationsarchitektur: bei Bedarf bewusst neu bewerten.
```

---

*Dieses Dokument ist eine Analyse. Es wurde nichts implementiert, keine Story
begonnen und weder Roadmap noch ADRs verändert.*
