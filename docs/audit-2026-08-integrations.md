# Integrations, Interoperability & Ecosystem Audit — August 2026

> **Klassifikation: HISTORISCH** (Snapshot August 2026). Nicht als geltende
> Entscheidung lesen. Aktuelle Wahrheit: [`docs/current-state.md`](current-state.md)
> und [`docs/adr/`](adr/) — für Produktidentität und Deployment insbesondere
> [ADR 0008](adr/0008-deployment-models-self-hosted-first.md).

Ergänzung zum [Product Readiness Audit](./audit-2026-08-product-readiness.md).
Leitfrage: **Welche externen Systeme und Informationsflüsse sollte Seiton
Brain unterstützen, damit es sich wie die zentrale Wissensschicht im
digitalen Leben des Nutzers anfühlt — nicht wie eine isolierte Notiz-App?**

Kein Produktivcode geändert — Entscheidungsgrundlage.

> **Entscheidung (2026-08-18):** Alle 5 Initiativen vom Product Owner
> bestätigt → **Phase M — Ecosystem & Interoperability** mit Epics
> **E32–E36** in der [ROADMAP](../ROADMAP.md), geplant nach dem
> Phase-L-Kern (Launch-Härtung).

---

## 1. Ist-Stand: Integrationsflächen im Code (verifiziert)

| Fläche | Stand heute |
|--------|-------------|
| **Vault = Markdown/Obsidian** | Notizen sind native `.md` mit Frontmatter (`title`, `category`, `created`, `updated`, `tags`), `[[Wikilinks]]` für Related, konfigurierbarem Ordner-Mapping (`SEITON_VAULT_CONFIG`), Templates in `_seiton/templates/`. **Das Produktformat ist selbst schon das offene Austauschformat.** |
| **REST `/v1`** | `POST /capture`, `POST /classify`, `GET /entries` (+ `/{id}`), `GET /notes/content`, `GET /notes/search` (Keyword/semantisch), `POST /ask`, `POST /digest`. **Kein** Update/Delete, ein einziger API-Key ohne Scopes. |
| **Outbound-Webhooks** | Events `note.created`, `note.appended`, `note.indexed`, `entry.failed` an eine URL. **Keine Signierung, kein Retry, keine `note.updated`/`note.deleted`-Events.** |
| **MCP-Server** (`examples/mcp/`) | 5 Tools: `search_notes`, `ask_brain`, `get_note`, `capture_note`, `digest` — via REST + API-Key. |
| **n8n** | Beispiel-Workflows REST-only (ADR 0004: kein Custom-Node). |
| **Git-Backend** (`app/vault/git_backend.py`) | **Existiert bereits:** Auto-Commit pro Seiton-Änderung + optionaler Push auf Remote (`VAULT_GIT_PUSH`, `VAULT_GIT_REMOTE`, Branch). Fehlt: geführtes Setup, UI-Status, Commit externer (Obsidian-)Edits, Doku-Sichtbarkeit. |
| **Dateien lesen** | E18-Extractors: PDF/Word/PowerPoint/Text/Markdown, Bilder via OCR/Vision — read-only in den Index (`doc_type`). |
| **Import** | Bestehender Obsidian-Vault wird beim Erststart voll indexiert. Kein Notion/Evernote/ZIP-Import. Laufende Koexistenz leidet am Index-Drift (E28-1). |
| **Backup** | `pg_dump` + `vault.tar.gz` lokal; kein Offsite-Ziel, keine Rotation (E29-4). |
| **Background-Jobs** | Celery ohne Beat — **kein periodischer Task-Mechanismus** (blockiert Polling-Integrationen wie IMAP/ICS und Index-Sync gleichermaßen). |
| **Auth für Integrationen** | Ein API-Key, timing-safe, off-by-default. Kein OAuth, keine Scopes, kein Zugriffs-Log. |
| **URL-Capture** | **Nicht vorhanden:** ein geteilter Link wird nur als Rohtext klassifiziert, kein Artikel-Fetch/-Extrakt. |
| **Geplant (ROADMAP)** | E22-5 E-Mail via IMAP, E22-6 Q&A→Note, E23-3 Offline-Queue, E23-4 Share-Target/iOS-Shortcut, E15-5 Notion-Evaluation, E24-x Cloud. |

**Kernbefund:** Seiton ist architektonisch bereits ungewöhnlich offen (Markdown-Vault, REST, MCP, Webhooks, Git). Die Lücke ist weniger „fehlende Integrationen" als **fehlende Produktisierung und Vervollständigung der vorhandenen Offenheit**.

---

## 2. Integration Landscape (Markt/Community-Recherche)

Quellen: Readwise-Doku + offizielles Obsidian-Plugin, Mem-Doku
(Email-to-Mem), Zapier-Integrationsverzeichnis (Reflect), Feature-Request-
Portale (Web Highlights), Reddit-Auswertungen (r/Obsidian, r/productivity,
r/PKMS), Khoj/Reor aus dem vorherigen Audit.

**Was Nutzer bei PKM-Tools immer wieder fordern und tatsächlich intensiv nutzen:**

1. **Highlight-/Lese-Ingestion** — Readwise ist der De-facto-Standard-Layer (Kindle/Pocket/Instapaper/PDF → automatischer Sync in den Vault, append-only, Template-basiert). Meistgenutzte „Integration" im Obsidian-Umfeld.
2. **Web-Clipping** — „Artikel/Highlight → Notiz" ist der meistgewünschte Capture-Flow (Obsidian Web Clipper offiziell; bei Tools ohne Clipper Top-Feature-Request).
3. **E-Mail-Forwarding-Adresse** — Standard bei Mem (`save@mem.ai`), via Zapier bei Reflect; Notion nur über Drittanbieter (Quicktion u. a. existieren als eigene bezahlte Produkte nur für diese Lücke!). „Everything can be sent into my Second Brain" ist ein belegtes Bedürfnis.
4. **Data Ownership / Export** — Reflect wird öffentlich für „locked ecosystem, no bulk export" kritisiert; Obsidians Dominanz in Power-User-Kreisen basiert auf local-first Markdown. **Vertrauen durch Portabilität ist kauf­entscheidend.**
5. **Zapier/Make/n8n-Anbindung** — Standard-Erwartung bei Cloud-Produkten; bei self-hosted Produkten übernimmt n8n + Webhooks dieselbe Rolle.
6. **Kalender/Meeting-Notes** — stark bei Team-Tools (Tana, Otter, Fireflies); bei Single-User-PKM deutlich schwächeres Signal.
7. **MCP/AI-Access** — 2026 zunehmend Standard-Erwartung („meine AI darf mein Wissen abfragen"); Tana bewirbt MCP prominent, Khoj positioniert sich als AI-Hub.

---

## 3. Jobs to be Done → was davon zu uns passt

| Job | Bedarf belegt? | Unser Stand | Lücke |
|-----|----------------|-------------|-------|
| **Capture** — „sofort speichern" | ★★★ (Kern-USP) | Telegram (Text/Voice/Foto/Doc), UI, REST, MCP | **URL→Artikel fehlt ganz**; Share-Sheet (E23-4) und E-Mail (E22-5) geplant, nicht gebaut |
| **Migration** — „mein Wissen liegt woanders" | ★★★ (Onboarding-Hürde) | Obsidian-Vault wird indexiert (= nativer Import) | Nicht als Onboarding inszeniert; kein Markdown-ZIP-Import (deckt Notion-Export ab); Index-Drift bricht Koexistenz |
| **Backup/Ownership** — „meine Daten gehören mir" | ★★★ (kaufentscheidend) | Markdown-Vault by design; Git-Push existiert; lokales Backup | Git-Backup unsichtbar/unproduktisiert; kein Offsite; keine Rotation |
| **Automation** — „wiederkehrende Flüsse" | ★★ (Power-User) | REST + Webhooks + n8n-Beispiele | API unvollständig (kein Update/Delete), Webhooks unsigniert, wenige Events |
| **AI Access** — „meine AI fragt mein Wissen" | ★★☆ steigend | MCP mit 5 Tools (Differenzierer!) | Ein Key = Vollzugriff; kein Read-only-Scope, kein Zugriffs-Log; Doku-Sichtbarkeit |
| **Action** — „aus Wissen wird Aufgabe" | ★★ | Kategorie „Aufgabe" + Webhooks | Bewusst NICHT selbst bauen: Task-Systeme via n8n/Webhook-Rezepte anbinden |
| **Context** — „fremde Daten neben Notizen sehen" (Sheets-Embed, Kalender) | ★☆ für unsere Zielgruppe | — | Bewusste Lücke: OAuth-Sync/Embed-Komplexität ohne Capture-first-Fit |

---

## 4. Gap-Analyse Schlüsselkategorien

### Obsidian/Markdown (strategisch wichtigste Kategorie)

Wir müssen hier nichts „integrieren" — **wir sind das Format**. Konsequenzen:

- Ordnerstruktur, Frontmatter, Wikilinks, Templates: erhalten ✅
- Vollständiger Markdown-Export: ist der Vault selbst ✅
- Bestehenden Vault importieren: funktioniert (Erstindexierung) ✅ — aber ohne Onboarding-Flow und ohne laufenden Re-Sync (E28-1 = **die** Interop-Story)
- **Multiplikator-Effekt:** Jedes Tool, das in einen Obsidian-Vault schreibt (Readwise-Plugin, Obsidian Web Clipper, iCloud/Syncthing-Ordnersync), wird durch den Index-Sync automatisch zu einer Seiton-Integration — ohne dass wir Code schreiben. Das gesamte Obsidian-Ökosystem wird unser Integrations-Katalog.

### Cloud Storage & Backup

- GDrive/Dropbox/OneDrive-**APIs (OAuth) nicht bauen**: Der Vault ist ein normaler Ordner — Sync-Clients und `rclone` erledigen App→Cloud heute schon. Ein `rclone`-Offsite-Rezept + Backup-Rotation (E29-4) genügt.
- **Open Format + Automated Backup + Easy Restore** als Trust-Paket: Markdown-Vault (haben wir) + Git/rclone-Offsite (fast) + One-Click-Restore (E25-1-Basis) → als Produktprinzip „**Deine Daten, überall, für immer**" vermarktbar.

### Git/GitHub

- `GitVaultBackend` kann heute Commit-pro-Änderung + Push. Für „GitHub-Backup" als Feature fehlt: geführtes Setup (Repo/Remote/Deploy-Key), Commit auch externer Obsidian-Edits (periodisch), Status in Settings, Doku.
- Bewertung: **Power-User-Feature, aber exakt unsere Zielgruppe** (self-hosted, technikaffin). Versionierung + Historie + Offsite in einem. Aufwand klein, da 80 % existieren.

### Google Workspace / Microsoft 365

- Sheets/Docs Import/Embed/Live/Two-Way (Modelle A–E): Nutzen für Capture-first-Single-User gering, Komplexität (OAuth, Sync-Engine, Konflikte) hoch → **Tier 4**, nicht bauen. Import einzelner Dokumente ist über Datei-Upload (E18/E22-2) bereits abgedeckt — Word/PDF rein funktioniert heute.
- Gmail/Outlook: nicht als API-Integration, sondern generisch via **IMAP-Postfach** (E22-5) — providerunabhängig, ohne OAuth-App-Reviews, self-hosted-tauglich.

### Kalender

- Meeting→Notiz ist Otter/Fireflies/Tana-Territorium (Team-Fokus). Für uns: ICS-read-only („heutige Termine als Kontext im Digest") wäre nett, aber kein belegter Kernbedarf unserer Zielgruppe → **Tier 3, später bei Nachfrage**.

### Tasks

- Trennung bestätigt: **Seiton = Wissen & Kontext, externes Tool = Ausführung.** `note.created` (category=Aufgabe) → Todoist/Linear via n8n-Rezept. Keine eigene Task-Integration bauen → **Tier 4 + Rezepte**.

### Browser/Web & Mobile Capture

- Größte echte Capture-Lücke: **URL → extrahierter Artikel → Notiz mit Quelle**. Heute wird ein Link nur als Text klassifiziert. Mit Artikel-Extraktion wird jeder geteilte Link (Telegram, Share-Sheet, UI) zu einer vollwertigen Wissensnotiz mit `source:`-Frontmatter.
- Eigene Browser-Extension: **nicht nötig als Erstschritt** — PWA-Share-Target (Android) + iOS-Shortcut (E23-4) + Bookmarklet gegen `POST /v1/capture` decken 80 % ab. Extension = Tier 3.

### Automation Platforms

- Zapier/IFTTT-Apps erfordern öffentlich erreichbare Endpoints → erst mit Cloud-Edition sinnvoll. **n8n ist die self-hosted-native Antwort** und ADR-konform. Fundament dafür härten: vollständige REST-CRUD, signierte Webhooks, mehr Events, Idempotenz.

### AI Ecosystem

- MCP-Server existiert und ist 2026 ein echtes Verkaufsargument. Fehlende Vertrauensschicht: **Scoped Keys** (read-only für AI-Clients vs. read-write für Automationen), optionales Zugriffs-Log („welches Tool hat wann was gelesen"), prominente Doku für Claude Desktop/ChatGPT/Cursor.

---

## 5. Integration Matrix

Richtung: Import / Export / Backup / Capture / Read / Write / Sync (1-way/2-way).
Aufwand: XS–XL · Nutzerwert & DSGVO-Risiko: niedrig/mittel/hoch.

| Integration | Use Case | Richtung | Nutzerwert | Zielgruppe | Aufwand | Komplexität | Datenschutzrisiko | Priorität |
|---|---|---|---|---|---|---|---|---|
| **Obsidian-Vault-Koexistenz** (Index-Sync + Onboarding) | Bestehendes Brain mitbringen, parallel weiternutzen | 2-Way (Dateiebene) | **Hoch** | Alle | M | Mittel | Keins (lokal) | **Tier 1** |
| **Git-Backup** (GitHub/GitLab/lokal) | Versionierung + Offsite + Historie | Backup/Export | **Hoch** | Power-User (= Kernzielgruppe) | S–M | Niedrig (80 % da) | Mittel (privates Repo!) | **Tier 1** |
| **URL/Web-Capture** (Artikel-Extraktion) | Link teilen → Wissensnotiz | Capture | **Hoch** | Alle | S–M | Niedrig–Mittel | Niedrig | **Tier 1** |
| **E-Mail-Capture** (IMAP, E22-5) | Newsletter/Mail-an-mich → Notiz | Capture | **Hoch** | Alle | M | Mittel | Mittel (Mail-Inhalte) | **Tier 1** |
| **Share-Sheet/Shortcut** (E23-4) | Mobil in 2 s teilen | Capture | **Hoch** | Alle | S | Niedrig | Keins | **Tier 1** |
| REST-CRUD + signierte Webhooks + Events | Automation-Fundament (n8n/Make) | Read/Write/Events | Mittel–hoch | Power-User | M | Mittel | Niedrig | **Tier 2** |
| Scoped API-Keys + MCP-Sichtbarkeit | AI liest kontrolliert | Read (AI) | Mittel–hoch, steigend | AI-Nutzer | S | Niedrig | **Senkt** Risiko | **Tier 2** |
| Markdown-ZIP-Import | Notion-/Generic-Migration | Import | Mittel | Wechsler | S | Niedrig | Keins | **Tier 2** |
| rclone/S3-Offsite-Backup (Rezept + Hook) | Cloud-Backup ohne OAuth | Backup | Mittel | Alle | XS–S | Niedrig | Mittel (Ziel wählbar) | **Tier 2** |
| Readwise/Clipper-Rezepte (Doku) | Highlights → Vault → Index | Import (via Vault) | Mittel | Leser | XS (Doku) | Keine | Keins | **Tier 2** |
| Browser-Extension | 1-Klick-Clip + Highlight | Capture | Mittel | Alle | L | Hoch (3 Stores) | Niedrig | Tier 3 |
| Evernote ENEX / OneNote-Import | Legacy-Migration | Import | Niedrig–mittel | Wechsler | M | Mittel | Keins | Tier 3 |
| Kalender ICS (read-only Kontext) | Termine im Digest | Read | Niedrig–mittel | Teilgruppe | S–M | Mittel | Mittel | Tier 3 |
| Notion-Export/Sync (E15-5) | Notion-Nutzer andocken | Export/1-Way | Unklar (Evaluation!) | Notion-Nutzer | L | Hoch (Block≠MD) | Mittel | Tier 3 |
| Todoist/Linear/Jira/Trello | Wissen → Aufgabe | Write | Mittel | Teilgruppen | — | — | — | **Tier 4** → n8n-Rezepte |
| Google Docs/Sheets Embed/Live/2-Way | Live-Daten in Notizen | Embed/Sync | Niedrig (Fit!) | Wenige | XL | Sehr hoch | Hoch (OAuth) | **Tier 4** |
| GDrive/Dropbox/OneDrive-API | Cloud-Backup | Backup | — (rclone/Ordnersync deckt ab) | — | L | Hoch (OAuth) | Hoch | **Tier 4** |
| Zapier/IFTTT eigene App | Mainstream-Automation | Events | — (braucht Cloud-Edition) | — | L | Hoch | Mittel | **Tier 4** (mit E24 neu bewerten) |

---

## 6. Architektur-Empfehlungen („heute schaffen, damit 20+ Integrationen später einfach sind")

1. **Periodischer Scheduler (Celery Beat)** — fehlt komplett und blockiert *jede* Polling-Integration (IMAP, Git-Auto-Commit externer Edits, ICS, Index-Sync E28-1). Eine Infrastruktur-Story, viele Abnehmer. **Jetzt.**
2. **Provenance im Capture-Pfad** — ein `source`-Konzept (telegram/ui/rest/email/web/mcp + optional `source_url`) durch `process_text_message` bis ins Frontmatter (`source:`). Nachträglich teuer (Bestandsnotizen), jetzt billig. Grundlage für Vertrauen, Filter, Dedup und jede künftige Quelle. **Jetzt.**
3. **Event-Layer einmal sauber** — Webhook-Payloads versionieren (`"version": 1`), HMAC-Signatur, Events `note.updated`/`note.deleted` ergänzen, Retry mit Backoff. Danach ist jede Plattform-Anbindung nur noch Empfänger-Konfiguration. **Vor Automation-Marketing.**
4. **API-Key-Modell: mehrere Keys mit Scope (read/read-write) + optionales Zugriffs-Log.** Kleine Tabelle statt ein Env-String; Revocation pro Integration. **Vor AI-Access-Marketing.**
5. **Kein Plugin-System, kein OAuth-Framework auf Vorrat.** Für self-hosted Single-User sind REST + Webhooks + MCP + n8n unser Plugin-System (ADR-0004-konform); alle Tier-1/2-Integrationen kommen ohne OAuth aus (IMAP-App-Passwort, Git-Deploy-Key, rclone-Config). OAuth-Token-Storage erst bauen, wenn eine bestätigte Integration es wirklich braucht.
6. **Adapter-Muster fortführen, nicht vorziehen:** `VaultBackend`-Protocol und Extractor-Registry sind die richtigen Vorbilder. Ein „IngestSource"-Protocol lohnt erst ab der zweiten Polling-Quelle (E-Mail als erste bauen, dann generalisieren).

---

## 7. Top-5-Empfehlungen (Initiativen, keine Stories)

1. **„Bring your Second Brain" — Obsidian-Koexistenz als Produkt-Feature.**
   Index-Sync (E28-1, ohnehin Launch-Bedingung) + Setup-Onboarding „bestehenden Vault verbinden" + Koexistenz-Rezepte (Readwise-Plugin, Obsidian Web Clipper, Ordner-Sync).
   *Begründung:* Größter Vertrauens- und Onboarding-Hebel; macht das gesamte Obsidian-Ökosystem kostenlos zu unserem Integrationskatalog; Aufwand größtenteils schon eingeplant.

2. **Git-Backup produktisieren (GitHub/GitLab/lokal).**
   Geführtes Setup, periodischer Commit externer Edits (braucht Scheduler), Status in Settings, Doku.
   *Begründung:* 80 % des Codes existieren; Versionierung + Offsite + Anti-Lock-in in einem; perfekter Fit zur self-hosted-Zielgruppe; starkes Marketing („dein Wissen, versioniert, für immer").

3. **Universal Capture vervollständigen: URL-Extraktion + Share-Sheet + E-Mail.**
   Neu: Link → Artikel-Extrakt → Notiz mit Quelle; dazu die geplanten E23-4 (Share-Target/Shortcut) und E22-5 (IMAP).
   *Begründung:* Capture ist unser USP; diese drei schließen die meistgenutzten Capture-Wege des Marktes (Clipper, Mobile-Share, E-Mail-Forwarding); „Everything can be sent into my Second Brain" wird wahr.

4. **Automation-Fundament härten statt Einzelintegrationen bauen.**
   REST-CRUD komplettieren, Webhooks signieren + `note.updated`/`deleted`, Idempotenz (Synergie E28-4), 3–4 n8n-Rezepte (Todoist, Linear, Slack-Digest).
   *Begründung:* Deckt die Long-Tail-Integrationswünsche (Tasks, Sheets-Logging, Benachrichtigungen) ohne eigenen Code pro Ziel; ADR-0004-konform.

5. **Kontrollierter AI-Access: Scoped Keys + MCP-Sichtbarkeit.**
   Read-only-API-Keys, optionales Zugriffs-Log, Integrations-Karte in Settings + prominente Doku für Claude/ChatGPT/Cursor.
   *Begründung:* MCP haben wir vor dem Markt-Mainstream; die Vertrauensschicht (Scope/Revocation/Audit) macht daraus ein bewerbbares Differenzierungsmerkmal mit kleinem Aufwand.

**Bewusst nicht empfohlen:** Google/Microsoft-Office-Embeds & Two-Way-Sync, eigene Cloud-Storage-OAuth-Integrationen, eigene Task-Tool-Anbindungen, Zapier-App (vor Cloud-Edition), Plugin-System, eigener Kalender-Sync — jeweils schwacher Fit zu Capture-first-Single-User oder durch offene Basis bereits abgedeckt (Details in Matrix/Tier 4).

---

## Antwort auf die Leitfrage

Seiton fühlt sich dann wie die zentrale Wissensschicht an, wenn drei Flüsse
reibungslos sind: **alles hinein** (Telegram, Share, E-Mail, URL, Datei —
in Sekunden), **alles hinaus bzw. nie eingesperrt** (Markdown-Vault, Git-
Historie, Backups, Export — Ownership by design) und **alles anfragbar**
(Suche/RAG für Menschen, MCP/API mit Scopes für AIs, Events für Maschinen).
Die gute Nachricht dieses Audits: Alle drei Flüsse sind architektonisch
angelegt — es fehlt keine fremde Plattform-Integration, sondern die
Vervollständigung und Produktisierung unserer eigenen offenen Kanten.
