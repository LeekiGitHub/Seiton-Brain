# Team Collaboration, Shared Knowledge & Professional Use — Audit 2026-08

> **Klassifikation: HISTORISCH** (Snapshot August 2026). Nicht als geltende
> Entscheidung lesen. Aktuelle Wahrheit: [`docs/current-state.md`](current-state.md)
> und [`docs/adr/`](adr/) — für Produktidentität und Deployment insbesondere
> [ADR 0008](adr/0008-deployment-models-self-hosted-first.md). Die hier
> formulierte Aussage „Self-Hosting ist bereits das Produkt" ist durch ADR 0008
> ersetzt: Self-hosting ist die **zuerst ausgelieferte Betriebsform**, nicht die
> Produktidentität.

**Datum:** 2026-08-18 · **Scope:** Strategie-/Architektur-Analyse + Roadmap-Update
**Leitfrage:** Kann und sollte Seiton Brain neben persönlicher Nutzung auch für
kleine Teams, Gruppen und professionelle Nutzung geeignet sein?

> **Status: Entscheidung getroffen.** Ergebnis dieses Audits ist die Einstufung
> **PERSONAL + SMALL TEAM** (Begründung unten) und eine neue **Phase O** in der
> ROADMAP (E41–E44). Bewusst **nicht** empfohlen: Realtime-Editing, Kommentare,
> Kanban, Multi-Tenant, Enterprise-IAM (vollständige Liste in Abschnitt „NOT
> Build").

Verwandte Dokumente: ADR 0004 (Single-User-Produkt), ADR 0007 (Cloud =
Instanz pro Kunde), [`audit-2026-08-private-knowledge-ai.md`](./audit-2026-08-private-knowledge-ai.md)
(Phase N — `ai_access`-Permission-Layer, dessen Muster hier wiederverwendet wird).

---

## Executive Summary

**Empfehlung: PERSONAL + SMALL TEAM — über das Modell „Shared Instance", nicht
über Multi-Tenant-Umbau.**

Die entscheidende Architektur-Einsicht: Seiton Brain muss für kleine Teams
**kein Multi-User-System im klassischen Sinn** werden. Das Produkt ist
Instanz-basiert (ADR 0007: auch die Cloud-Edition = eigene Instanz pro Kunde).
Ein Team ist dann einfach: **eine Instanz = ein Team = ein gemeinsamer Vault.**
Damit entfallen die teuersten Probleme (Tenant-Isolation, Workspace-Tabellen,
Cross-Tenant-Leakage) strukturell — die Instanzgrenze *ist* die Isolationsgrenze.

Was tatsächlich fehlt, ist überschaubar und in vier Epics fassbar:

1. **Identität** (E41): Wer ist wer? Heute: ein geteiltes Passwort, keine
   `users`-Tabelle, keine Attribution. Kuriosum: Die Telegram-Allowlist erlaubt
   *heute schon* mehrere Personen pro Instanz — nur weiß niemand, wer was
   erfasst hat.
2. **Rollen & Sichtbarkeit** (E42): Owner/Editor/Viewer (drei Rollen, nicht
   sechs) + private Ordner (`visibility`) — exakt dasselbe Muster wie der
   `ai_access`-Layer aus Phase N, durchgesetzt an derselben Stelle **vor** dem
   Retrieval.
3. **Awareness & Wiki-Grundlagen** (E43): „Was hat sich geändert, wer hat's
   geschrieben, wie sah es vorher aus?" — Version History kommt fast gratis
   aus dem Git-Backup (E34), Templates (E26) sind durch den geteilten Vault
   automatisch Team-Templates.
4. **Team-AI-Kontrolle** (E44): Der Owner bestimmt instanzweit erlaubte
   AI-Provider/Trust-Level; Team-RAG filtert `ai_access ∩ visibility ∩ Rolle`
   — eine Erweiterung von E38, kein neues System.

Was wir **nicht** bauen: Realtime-Editing (CRDT), Kommentare/Threads,
Mentions/Notifications, Kanban/Projektmanagement, externe Share-Links,
Multi-Tenant in einer Instanz, SSO/Enterprise-IAM. Der Team-Wiki-Markt
(Docmost, Outline, BookStack — alle frei) ist gesättigt; unsere Nische ist das
**Shared Second Brain**: Capture von überall → AI ordnet ein → gemeinsames,
befragbares Wissen mit Privacy-Kontrolle. Nicht „Google Docs", sondern
„gemeinsames Gedächtnis".

---

## 1. Current Collaboration Readiness — Ist-Analyse

### Wo „Resource belongs to exactly one user" heute implizit gilt

| Stelle | Befund | Team-Problem? |
|---|---|---|
| **Datenmodell** | Nur 3 Tabellen (`entries`, `vault_note_index`, `vault_chunk`) — **keine `users`-Tabelle**, kein `created_by`/`updated_by`. Einzige Identitätsspur: `entries.telegram_chat_id`. | Ja — Attribution unmöglich; **aber**: keine falsche Ownership-Annahme zu migrieren, die Felder fehlen einfach. Nachrüsten ist additiv (nullable Spalten), keine teure Migration. |
| **UI-Auth** (`app/ui/auth.py`) | Ein gemeinsames `UI_PASSWORD`; Sessions **zustandslos** (HMAC über Expiry, Schlüssel aus dem Passwort abgeleitet), Kommentar: „Single-User-System". | Ja — kein Login pro Person, kein Logout einzelner Mitglieder, Passwortwechsel wirft alle raus. Kern von E41. |
| **REST-API** | Ein `SEITON_API_KEY`, all-or-nothing. | Ja — E36-1 (Scoped Keys) ist bereits geplant; Team braucht zusätzlich Key→Nutzer-Zuordnung. |
| **Telegram** | Allowlist mit **mehreren** User-IDs möglich — de facto heute schon „Familien-Capture". | Nein strukturell — nur fehlt das Mapping Telegram-ID → Person. |
| **Vault** | Ein Filesystem-Vault, Ordner als einzige Struktur; Writes atomar, File-Locks geplant (E28-2). | Nein — der gemeinsame Vault *ist* das Shared-Knowledge-Modell. Ordner = Spaces. |
| **Suche/RAG** | Alles läuft durch `retrieve_vault_notes()` — ein Durchsetzungspunkt. | Nein — im Gegenteil: der beste Hebel. Sichtbarkeits-Filter dockt an derselben Stelle an wie `ai_access` (E38-2). |
| **Worker/Jobs** | Celery-Tasks instanzweit, kein Nutzerbezug. | Kaum — Digest/Sync sind sinnvoll instanzweit; nur Attribution im Capture-Task nötig. |
| **Brute-Force-Schutz** | In-Memory pro Prozess. | Klein — bei mehr Nutzern weiterhin ok (eine Instanz, ein Prozess). |
| **Lizenzierung** (E21-1) | Offline-Lizenz Ed25519, Payload erweiterbar. | Nein — Seat-/Edition-Felder passen ins bestehende Format. Monetarisierungs-Grundlage existiert. |

**Readiness-Urteil:** Für *Multi-Account-in-einer-Instanz* heute nicht bereit
(fehlende Identität), aber **ungewöhnlich gut vorbereitet** für das
Shared-Instance-Modell: Instanz-Isolation, ein Retrieval-Seam, Ordner-Struktur,
Git-Versionierung (E34), Template-System (E26), Self-Hosting-Tooling — alles da
oder geplant. Die Lücke ist schmal und additiv.

---

## 2. Product Fit — natürliche Erweiterung oder Ablenkung?

### Drei Produktmodi unter einem Modell

| Modus | Was es bei uns bedeutet | Verdict |
|---|---|---|
| **Personal** | Status quo: eigene Instanz, eigener Vault. | Kernprodukt, bleibt Default. |
| **Team** | **Dieselbe Software**, eine gemeinsam betriebene Instanz: Mitglieder-Accounts, Rollen, gemeinsamer Vault mit privaten Ordnern. | Natürliche Erweiterung — kein zweiter Produkttyp. |
| **Professional / Self-Hosted** | **Ist bereits unsere DNA**: Docker Compose, install/deploy/update/doctor-Skripte, Backups (E25-1/E29-4), Offline-Lizenz, lokale LLMs (Phase N). Kleinunternehmen = Team-Modus + vorhandenes Self-Hosting + Admin-AI-Kontrolle (E44). | Kein separater Modus — Self-Hosting ist der Normalfall, nicht das Enterprise-Feature. |

Die drei Ebenen passen unter ein Produktmodell, **weil** wir Instanz-basiert
sind: „Team" und „Professional" sind Konfigurationen derselben Instanz, keine
getrennten Architekturen.

### Warum es zum Kern passt (und wo die Grenze liegt)

Der Produktkern ist *Capture → AI ordnet ein → befragbares Wissen*. Genau
dieser Kern wird im Team **wertvoller**, nicht verwässert: geteiltes Capture
(jeder wirft per Telegram/UI/Mail Wissen hinein), geteilte Retrieval-Qualität
(„Was haben wir zu Kunde X?"), geteilte AI-Kontrolle. Die Falle wäre, den
*Editor* zum Kollaborationsprodukt auszubauen (Realtime, Kommentare, Docs) —
das ist der gesättigte Markt und nicht unser Spiel. **Fit: ja — solange
Kollaboration „gemeinsames Gedächtnis" heißt und nicht „gemeinsames Schreiben
in Echtzeit".**

---

## 3. Recommended Collaboration Model — Shared Instance statt Shared Minds

Der Auftrag fragt nach „Shared Minds/Workspaces" (einzelne Bereiche gezielt
teilen, My Mind privat). Bewertung beider Abstraktionen:

| | Shared Minds (Bereiche einzeln teilen, ein Account überall) | **Shared Instance (Team = Instanz, private Ordner darin)** |
|---|---|---|
| Architektur | Braucht globale Accounts, Workspace-Tabellen, Cross-Workspace-ACL, Tenant-Isolation in DB/Index/Vektoren — der teuerste Umbau | Instanzgrenze = Isolationsgrenze; nur Ordner-Sichtbarkeit nötig (Muster existiert: `ai_access`) |
| Privacy-Risiko | Hoch (eine DB, ein Index, ACL-Fehler = Leak zwischen Workspaces) | Strukturell klein (privates bleibt `visibility:private`, Team-Inhalte sind eh geteilt) |
| UX | Ein Ort für alles — elegant, aber komplex | Persönliche Instanz + Team-Instanz = zwei URLs; **in** der Team-Instanz gibt es private Ordner |
| Passt zu ADR 0004/0007 | Nein (widerspricht Single-User/Instanz-Modell) | Ja (identisch mit Cloud-Modell) |

**Empfehlung: Shared Instance.** Konkret:

- Ein Team betreibt (oder mietet, E24) **eine** Instanz. Der Vault ist das
  „Company Wiki / Project Brain". Ordner sind die Bereiche („Project Alpha",
  „Research", „Kundenwissen").
- **Private Bereiche im Team:** Ordner mit `visibility: private` (nur
  Ersteller + Owner-Notfallzugriff, klar dokumentiert) — für Entwürfe und
  persönliche Arbeitsnotizen im Team-Kontext.
- **Wirklich Privates** gehört in die persönliche Instanz — bewusste,
  physische Trennung statt ACL-Vertrauen. Cross-Instance-Links: nicht bauen
  (Kopieren/Capturen von der einen in die andere reicht).
- Lifecycle: Einladung per Link/Code (E41-3), Entfernen = Session+Keys
  widerrufen, Inhalte bleiben beim Team (Attribution bleibt), Ownership-
  Transfer = Rolle übertragen, Export/Löschen = vorhandene E31-Mechanik.

---

## 4. Permission Model — drei Rollen, capabilities intern

**Empfehlung: Owner / Editor / Viewer.** Bewusst ohne Admin (= Owner kann
mehrere Personen sein), ohne Contributor (Editor deckt es ab), ohne Guest
(externe Read-only-Links sind P4, s. u.). Der Markt bestätigt: Docmost/Outline
fahren mit 3 Rollen; BookStacks Granularität ist Enterprise-Bedarf.

| Capability | Owner | Editor | Viewer |
|---|---|---|---|
| Lesen (team-sichtbar) | ✅ | ✅ | ✅ |
| Suchen/AI fragen | ✅ | ✅ | ✅ (im Rahmen der Sichtbarkeit) |
| Erstellen/Bearbeiten/Capture | ✅ | ✅ | ❌ |
| Löschen | ✅ | ✅ (eigene + team) | ❌ |
| Mitglieder einladen/entfernen, Rollen | ✅ | ❌ | ❌ |
| AI-Policy, Integrationen, Settings, Export, Backup | ✅ | ❌ | ❌ |

Intern werden Rollen auf **Capabilities** gemappt (read, write, manage_members,
manage_ai, manage_settings, export) — eine Funktion `can(user, capability)`,
damit spätere Verfeinerung keine Checks umschreiben muss. Nach außen bleiben
es drei verständliche Rollen.

**Permissions-Ebenen:** Rolle wirkt instanzweit; Sichtbarkeit wirkt pro
**Ordner** (mit Notiz-Override wie bei `ai_access`). Keine Berechtigungen auf
Collection-/Abschnittsebene — Verständlichkeit schlägt Granularität.

---

## 5. Authorization Architecture

```
Request → Session (user_id) → Rolle → Capability-Check (Aktion)
        → Sichtbarkeits-Filter (Ordner: team | private:<user>)
        → ein Durchsetzungspunkt: retrieve_vault_notes / Notes-API
        → Aktion (UI, REST, MCP, Telegram, RAG)
```

Grundsätze (identisch mit E38, nur um die Nutzer-Dimension erweitert):

- **Backend-only Enforcement:** Frontend blendet aus, Server entscheidet.
- **Filter vor Retrieval:** Suche, Vektor-Suche und RAG-Kontext filtern
  `visibility` (und `ai_access`) in der WHERE-Klausel — ein Nutzer kann über
  Suche/AI/Embeddings/API **strukturell** nichts sehen, was er nicht lesen darf.
- **Fail-closed:** unbekannte Sichtbarkeit = privat; Invarianten-Tests in CI
  („Viewer-RAG enthält nie private Chunks anderer") nach dem Muster der
  E27-1-/E38-2-Tests.
- **Nebenkanäle:** Webhook-Payloads bleiben Metadaten-only (heute schon);
  Digest respektiert Sichtbarkeit des anfragenden Nutzers; Logs ohne Inhalte
  (E31-3); Kanal-Dimension aus E38-3 gilt weiter (Telegram = external-Kanal).

---

## 6. Team Wiki — ja, aber als „Wiki-Qualitäten", nicht als Wiki-Produkt

Kann aus dem Second Brain ein sehr gutes kleines Team-Wiki werden, ohne einen
separaten Produkttyp? **Ja — zu ~80 % ist es das strukturell schon:**

| Wiki-Erwartung | Status |
|---|---|
| Pages/Hierarchie | 🟢 Notizen + Ordner (+ Obsidian parallel für Power-User) |
| Interne Links/Backlinks | 🟡 `[[Links]]` werden geschrieben (Linker-Rolle); Backlink-Anzeige fehlt (Phase-N-Synergie E37-4 „Similar Notes" deckt Verwandtes ab) |
| Suche | 🟢/🟡 wird mit E37 (Hybrid) sehr gut |
| Templates | 🟢 E26 — im geteilten Vault automatisch Team-Templates; es fehlen nur Beispiel-Vorlagen (Meeting, Decision Record, SOP) |
| Recent Changes / Contributors / Last Updated | ⚪ → E43-1 (aus `entries` + Git-Log) |
| Page History | ⚪ → E43-2: **Git-Backup (E34) liefert das fast gratis** — `git log --follow`/`git diff`/`git checkout` pro Notiz, produktisiert als UI |
| Pinning/Favorites/TOC | ⚪ bewusst später/nie — Ordner + Suche + Dashboard reichen für ≤10 Personen |

Die Leitplanke: Wir bauen die **Auffindbarkeits- und Vertrauens-Qualitäten**
eines Wikis (Suche, Autor, Historie, Templates), nicht die **Redaktions-
Features** (WYSIWYG-Kollaboration, Seitenbäume, Publishing).

---

## 7. Collaborative Editing — Level 1–2, bewusst kein Realtime

| Level | Bewertung |
|---|---|
| **L1 — Nacheinander bearbeiten** | 🟢 Basis; atomare Writes existieren, File-Locks kommen (E28-2) |
| **L2 — Konflikt-Erkennung** | ✅ empfohlen: `mtime`-/Hash-Check beim Speichern in der UI („Notiz wurde zwischenzeitlich geändert — neu laden/überschreiben") + Git als Sicherheitsnetz (nichts geht verloren) |
| **L3 — Realtime (CRDT/OT, Presence)** | ❌ **nicht bauen.** Google-Docs-Realtime ist für ≤10-Personen-Wissensteams kein Kernbedarf (BookStack lebt bewusst ohne); CRDT-Infrastruktur (Sync-Server, Offline-Merge, Editor-Umbau) wäre der teuerste Einzelposten des gesamten Audits und zöge uns exakt in den Notion/Docmost-Wettbewerb, den wir meiden |

Unser Modell ist ohnehin capture-zentriert: Die meisten Inhalte entstehen als
*neue* Notizen/Appends durch die Pipeline, nicht als lange gemeinsam editierte
Dokumente. Konfliktdruck ist strukturell niedrig.

---

## 8. Version History

**Empfehlung: Git-basiert produktisieren (E43-2), keine eigene Revisions-DB.**
`GitVaultBackend` (E15-3) + Auto-Commit externer Edits (E34-2) erzeugen bereits
eine vollständige, manipulationsarme Historie pro Datei. Fehlt nur die UI:
Verlauf pro Notiz (Zeitpunkt, Autor aus Commit/Attribution), Diff-Ansicht,
Restore (checkout einzelner Datei-Version als neuer Commit), Papierkorb-
Wiederherstellung gelöschter Notizen.

**Auch für Einzelnutzer wertvoll** („Was stand da letzte Woche?", Undo über
`/undo` hinaus) — deshalb kein reines Team-Feature, sondern Priorität hoch.
Voraussetzung: E34 (Phase M) zuerst.

---

## 9–10. Activity, Comments & Discussions

**Activity (E43-1):** „Zuletzt geändert"-Liste (Dashboard hat Ansätze), Autor
auf der Notiz-Seite, einfacher Aktivitäts-Feed aus `entries` + Git-Log.
**Keine** Mentions, keine Notifications, kein Follow/Watch — Awareness ja,
Benachrichtigungs-System nein. Wer Pushes will: Webhooks → n8n → Slack
(E35-3) existiert als Rezept.

**Comments:** **Nicht bauen (jetzt).** Diskussionen bleiben in Slack/Teams —
dorthin verlinken (Notiz-URLs sind stabil). Falls sich später echter Bedarf
zeigt: leichtes notizweites Kommentarfeld (append-only Abschnitt), niemals
Threads/Mentions/Resolve-Workflows. In die Entscheidungsmatrix als P4
aufgenommen.

---

## 11–12. Team AI / Team RAG & AI-Permissions

Direkte Fortsetzung von Phase N — keine neue Architektur:

- **Team-RAG (E44-2):** Retrieval-Filter wird dreidimensional:
  `ai_access(note) ∩ visibility(note, user) ∩ Kanal-Trust`. Ein Nutzer ohne
  Zugriff auf `Management/` bekommt daraus nie Kontext — nicht nachträglich
  gefiltert, sondern nie retrievt (E38-2-Mechanik). CI-Invariante.
- **Admin-AI-Policy (E44-1):** Der Owner legt instanzweit fest: erlaubte
  Provider/Trust-Klassen (nur `local`? auch `external`?), ob BYOK-ähnliche
  eigene Endpoints erlaubt sind, welcher Company-Endpoint gilt (eigener
  Ollama/vLLM/OpenAI-kompatibler Server — E39-2 liefert den generischen
  Provider). Members können die Policy nicht lockern, nur enger stellen.
- Transparenz aus E40-3 (Provider-Badge, Kontext-Inspektor) gilt im Team
  unverändert — „welches Modell hat unsere Daten gesehen" ist im Team noch
  wichtiger als solo.

---

## 13–14. Self-Hosting & Offline/LAN

**Self-Hosting ist bereits das Produkt** — Docker Compose (Standard/Consumer/
VPS), `install.sh`/`init.sh`/`deploy-vps.sh`/`update.sh`/`doctor.sh`, Health-
Checks, Backups (E25-1, E29-4), Alembic-Migrationen, Proxy-Beispiele (Caddy/
nginx), Setup-Wizard. Für Teams fehlt nichts Deployment-Spezifisches; „Simple
Self-Hosting First" ist erfüllt. NAS/Home-Server: läuft überall, wo Compose
läuft.

**Offline/LAN-only:** Nach Phase N (E39-1 lokale Embeddings) ist die Kette
LAN → App → Postgres → Vault → lokale Embeddings → Ollama **vollständig ohne
Cloud** machbar — Telegram entfällt dann (externer Dienst), Capture via
UI/REST/Mail im LAN. Zielgruppe: klein aber hochwertig (Kanzleien, Praxen,
Forschung). Kein Extra-Bau nötig, nur Doku (in E39-3 aufgenommen: LAN-Szenario
beschreiben). Produktwert: glaubwürdigstes Privacy-Argument im Markt.

---

## 15–16. Professional Privacy, Offboarding & Audit Log

- **Datenisolation:** Instanz pro Team (physisch), private Ordner
  (`visibility`), AI-Grenzen (`ai_access`) — drei klare Schichten.
- **Offboarding („Mitarbeiter verlässt das Team"):** Konto deaktivieren →
  Sessions/API-Keys sofort ungültig (E41-3); **Inhalte bleiben der Instanz**
  (Wissen gehört dem Team, Attribution bleibt für Nachvollziehbarkeit);
  private Ordner des Ausgeschiedenen: Owner-Entscheidung mit dokumentiertem
  Verfahren (exportieren & löschen oder ins Team überführen) — von Anfang an
  so modelliert, kein nachträglicher Streitfall.
- **Audit Log (E44-3):** zweistufig — *Activity History* für alle (E43-1) und
  *Security-Log* für Owner: Login-Ereignisse, Einladung/Entfernung,
  Rollenänderung, AI-Provider-Änderung, Export, Löschungen. Nur Metadaten,
  nie Inhalte (E31-3-konform). Kein SIEM, keine Retention-Engine.
- Backups/Export/Löschung: vorhandene Mechanik (E25-1, E31-1/2) gilt
  instanzweit und deckt Team-Bedarf.

---

## 17–18. Team Search & Koexistenz Personal/Team

**Team Search = bestehende Suche + Sichtbarkeits-Filter** (E42-2) + die
Phase-N-Qualität (Hybrid/RRF). Filter nach Autor/Datum/Ordner: Autor wird
durch E41-2 (Attribution) erst möglich — danach triviale Query-Parameter.
Keine getrennte „Global Search" nötig: eine Instanz, ein Index.

**Koexistenz:** Team-Inhalte leben in der Team-Instanz, Privates in der
persönlichen Instanz (physisch getrennt = keine versehentlichen Leaks),
Arbeits-Privates in `visibility:private`-Ordnern der Team-Instanz.
Cross-Instance-Links/Backlinks: **nicht bauen** — Kopier-/Capture-Fluss reicht,
und jede Brücke wäre ein neuer Leak-Kanal.

---

## 19. Externes Sharing

Read-only-/zeitbegrenzte/passwortgeschützte Links: **P4, nicht jetzt.**
Öffentliche Links sind eine neue Angriffsfläche (Tokens, Revocation,
Search-Engine-Indexing, anonyme Zugriffe) und stehen quer zum Privacy-
Versprechen. Bedarf zuerst beobachten; bis dahin: Export (E31-2) und
MCP/REST für kontrollierten programmatischen Zugriff.

---

## 20–22. Tasks, Kanban & Knowledge-to-Action

Strategievergleich (kritisch, wie beauftragt):

| | Nutzerwert | Produktfit | Komplexität | Konkurrenz | Urteil |
|---|---|---|---|---|---|
| **A — Knowledge only** (Checklisten) | mittel | hoch | — | — | zu wenig: Aufgaben *entstehen* nachweislich beim Capture (Kategorie „Aufgabe" existiert seit jeher) |
| **B — Lightweight Tasks** | hoch | hoch | niedrig | ok (wir konkurrieren nicht mit PM-Tools) | ✅ **empfohlen, minimal** |
| **C — Full PM (Kanban, Sprints, Dependencies)** | für uns gering | **niedrig** | hoch | Linear/Jira/Todoist uneinholbar | ❌ Jira-Klon-Falle |

**Knowledge-to-Action-Analyse:** Der reale Fluss ist „Meeting-Notiz → daraus
muss eine Aufgabe werden". Das braucht: (a) die Erkenntnis, *dass* etwas eine
Aufgabe ist — leistet die Classify-Pipeline heute schon (`category: aufgabe`);
(b) einen Ort, an dem offene Aufgaben sichtbar sind — fehlt (E43-4:
Aufgaben-Ansicht über Kategorie + `status: offen/erledigt` im Frontmatter,
ab E41 optional `assignee`); (c) den Weg in echte PM-Tools — **ist geplant**
(E35-3: `note.created` + category → Todoist/Linear via n8n).

**Empfehlung: B-minimal intern + Integrationen extern.** Kein Kanban, keine
Boards, keine Sprints, keine Dependencies, keine Due-Date-Engine. Wenn ein
Team echtes PM braucht, ist die Antwort E35, nicht ein eigenes Jira.

---

## 23–24. Team Templates & Team-Onboarding

**Templates:** E26 existiert; im geteilten Vault sind Templates automatisch
team-weit. Fehlt nur: mitgelieferte Profi-Vorlagen (Meeting Notes, Decision
Record, Project Brief, SOP, Retro, Kundennotiz) → Teil von E43-3. Hoher
Professional-Nutzen, minimale Komplexität — bestätigt.

**Onboarding-Journey (Soll):** Owner installiert (bestehender Setup-Wizard) →
legt im Wizard den Owner-Account an (E41-1) → lädt per Invite-Link ein
(E41-3) → verbindet bestehenden Vault / importiert ZIP (E32-1/3) → setzt
Ordner-Sichtbarkeit + AI-Policy (E42-2, E44-1) → Team captured, sucht, fragt.
Reibungspunkte, die die Stories adressieren: Invite ohne E-Mail-Server
(Link/Code statt Mail-Versand), Rollen-Defaults (eingeladen = Editor),
AI-Policy-Default = restriktiv (Owner muss extern explizit erlauben).

---

## 25. Konkurrenzanalyse — Baseline vs. Scope-Falle

| Produkt | Modell | Für uns relevant |
|---|---|---|
| **Docmost** (AGPL, self-hosted) | Spaces, 3 Rollen, Realtime, lokale LLM-AI | Der direkteste „freie" Wettbewerber fürs Team-Wiki — bestätigt: 3-Rollen-Modell reicht; Realtime ist *deren* Kern, nicht unserer |
| **Outline** (BSL) | Collections, Admin/Member/Viewer, braucht OIDC+S3 | Zeigt die Setup-Hürde: **built-in Login ohne Identity-Provider ist ein Feature** (E41-1 bewusst mit E-Mail/Passwort, kein SSO-Zwang) |
| **BookStack** (MIT) | Hierarchie, granulare Permissions, **kein Realtime** | Beweis: kleine Teams leben gut ohne Echtzeit-Editing |
| **Notion/Slite/Nuclino** (SaaS) | Flexibel, „wiki sprawl"-Kritik, Cloud-only | Unsere Differenz: Self-Hosted + Capture-Pipeline + AI-Kontrolle; „Sprawl" adressieren wir durch AI-Klassifikation statt Governance-Disziplin |
| **Obsidian im Team** | Git-Workflows, kein natives Multiplayer | Unsere Koexistenz-Stärke: Team-Instanz + Obsidian auf demselben Vault (E32) ist ein Alleinstellungsmerkmal |

**Grundlegende Erwartungen** (müssen wir erfüllen): Accounts + einfache
Rollen, geteilte Suche, „wer hat wann was geändert", Templates, einfacher
Import. **Scope-Fallen** (bewusst nicht): Realtime-Editing, Kommentare/
Mentions, Datenbank-Views, Publishing, SSO/SCIM, Boards.

---

## 26. Positionierung

**Empfehlung: „Privacy-First Team Knowledge"** mit dem bestehenden
Self-Hosted-KI-Unterbau — konkret:

> **„Das gemeinsame Gedächtnis für kleine Teams — selbst gehostet, mit AI,
> ohne Kontrollverlust über eure Daten."**

Sie verbindet die bestätigte Phase-N-Positionierung (Privacy-First Knowledge
AI) mit der Team-Dimension, statt eine neue Erzählung aufzumachen. „Shared
Second Brain" ist das emotionale Framing, „Team Knowledge Hub" das
funktionale — beide zahlen auf dieselbe Architektur ein.

---

## 27. Monetarisierung (Produktlogik, keine Preise)

| Stufe | Inhalt | Mechanik |
|---|---|---|
| **Personal** | heutiges Produkt, 1 Nutzer | MIT/Portfolio bzw. Consumer-Lizenz (E21-1) |
| **Team (Self-Hosted)** | E41–E44: Accounts, Rollen, Sichtbarkeit, Team-AI-Policy, Audit-Log | Lizenz-Payload um `edition`/`seats` erweitern — Ed25519-Format (E21-1) trägt das ohne Umbau |
| **Team (Cloud)** | dieselbe Instanz, gehostet | E24/ADR 0007 — Instanz-pro-Kunde passt 1:1 aufs Shared-Instance-Modell |

Natürliche Upgrade-Pfade: Personal → Team (Instanz teilen), Self-Hosted →
Cloud (Betrieb abgeben). Kein separates „Pro"-Tier nötig — AI-Features sind
Kernprodukt, keine Paywall-Ebene (Konsistenz mit Privacy-Versprechen).

---

## 28. Architecture Changes Now — was heute billig ist und später teuer

| Entscheidung | Warum jetzt | Kosten jetzt |
|---|---|---|
| **`created_by`/`actor` in E33-1 (Provenance) mitdenken** | E33-1 (Phase M) fasst ohnehin `process_text_message` bis ins Frontmatter an — `actor` (Telegram-ID/Key-ID/Session) ist dieselbe Codespur; nachträglich = zweiter Durchstich | ~0 (Story-Erweiterung) |
| **Nullable `user_id`-Spalten von Anfang an bei neuen Tabellen** (z. B. E36-1 API-Keys) | API-Keys pro Nutzer statt global vermeidet spätere Key-Migration | ~0 |
| **Session-Design E41-fähig halten** | zustandslose Passwort-Sessions können `user_id` nicht tragen; bei nächster Auth-Arbeit serverseitige Sessions/Token mit Subject vorsehen | Doku-Notiz |
| **`visibility` als Konvention neben `ai_access` reservieren** | gleiche Stelle (`vault_config.yaml`/Frontmatter/Index-Spalte); Fremd-Tools sollen das Feld nicht anders belegen | XS (Doku, mit E38-1) |
| **Lizenz-Payload: `edition`/`seats`-Felder dokumentieren** | Ed25519-Payload ist erweiterbar — Feldnamen jetzt festlegen verhindert Format-Bruch | XS |
| **Instanz-Modell beibehalten (kein Multi-Tenant)** | die wichtigste *Unterlassung*: keine `workspace_id` in Kerntabellen einführen | 0 |

---

## Entscheidungsmatrix

| Feature | Nutzerwert | Product Fit | Aufwand | Komplexität | Zielgruppe | Empfehlung |
|---|---|---|---|---|---|---|
| Shared Instance (Team = Instanz) | hoch | **sehr hoch** | niedrig | niedrig | Teams 2–10 | ✅ P0-Modell |
| Accounts + Login pro Person | hoch | hoch | mittel | mittel | Teams | ✅ P0 (E41-1) |
| Attribution (created_by/Autor) | hoch | hoch | niedrig | niedrig | alle | ✅ P0 (E41-2, Vorstufe in E33-1) |
| Rollen Owner/Editor/Viewer | hoch | hoch | mittel | niedrig | Teams | ✅ P1 (E42-1) |
| Ordner-Sichtbarkeit (private/team) | hoch | hoch | mittel | mittel | Teams | ✅ P1 (E42-2) |
| Team Search (permission-aware) | hoch | hoch | niedrig* | niedrig | Teams | ✅ P1 (*fällt mit E42-2 ab) |
| Team RAG (permission-aware) | hoch | hoch | niedrig* | mittel | Teams | ✅ P1 (E44-2, *auf E38-2) |
| Admin-AI-Policy | hoch (Prof.) | hoch | niedrig | niedrig | Teams/Prof. | ✅ P1 (E44-1) |
| Version History (git-basiert) | hoch (auch solo) | hoch | mittel | niedrig | alle | ✅ P2 (E43-2) |
| Activity/Recently Changed | mittel | hoch | niedrig | niedrig | Teams | ✅ P2 (E43-1) |
| Team-Templates (Vorlagenpaket) | mittel | hoch | niedrig | niedrig | Prof. | ✅ P2 (E43-3) |
| Lightweight Tasks (Ansicht) | mittel | mittel | niedrig | niedrig | Teams | ✅ P2 (E43-4, minimal) |
| Security-Audit-Log | mittel (Prof.) | hoch | niedrig | niedrig | Prof. | ✅ P3 (E44-3) |
| Self-Hosting | — | — | — | — | — | 🟢 existiert (Kern-DNA) |
| Eigener LLM-Endpoint | hoch (Prof.) | hoch | — | — | Prof. | 🟢 via E39-2 (Phase N) |
| Guests / externes Sharing (Links) | niedrig–mittel | mittel | mittel | **hoch** (Security) | einzelne | ⏳ P4 beobachten |
| Kommentare/Mentions | niedrig | niedrig | mittel | mittel | — | ❌ nicht bauen (Slack verlinken) |
| Realtime-Editing (CRDT) | niedrig (für uns) | **niedrig** | **sehr hoch** | sehr hoch | — | ❌ nicht bauen |
| Kanban / Full PM | niedrig | niedrig | hoch | hoch | — | ❌ nicht bauen (E35-Integrationen) |
| Multi-Tenant / Workspaces-Tabellen | — | widerspricht ADR 0007 | sehr hoch | sehr hoch | — | ❌ nicht bauen |
| SSO/SAML/SCIM, Org-Charts | niedrig (Zielgruppe) | niedrig | hoch | hoch | Enterprise | ❌ nicht bauen |

---

## Produktstufen (Evolution)

1. **Stage 1 — Personal** (heute): Kernprodukt, Phasen L/M/N härten und erweitern es.
2. **Stage 2 — Attribution-ready** (in M/N enthalten): Provenance + `actor`
   (E33-1), Konventionen reserviert — noch kein Team-Feature sichtbar.
3. **Stage 3 — Shared Instance** (Phase O Kern): Accounts (E41), Rollen +
   Sichtbarkeit (E42) — ein Team kann die Instanz sicher teilen.
4. **Stage 4 — Team Intelligence**: permission-aware Team-Suche/RAG (E44-2) +
   Admin-AI-Policy (E44-1) — „Was haben wir zu Kunde X?" mit Garantien.
5. **Stage 5 — Team-Gedächtnis-Qualitäten**: Historie (E43-2), Aktivität
   (E43-1), Templates-Paket (E43-3), Aufgaben-Ansicht (E43-4), Audit-Log (E44-3).

Phase O startet **nach** dem Phase-N-Kern (E38 ist technische Vorstufe von
E42-2/E44-2; E34 ist Vorstufe von E43-2).

---

## Abschlussentscheidung

### **PERSONAL + SMALL TEAM**

Begründung entlang der geforderten Dimensionen:

- **Architektur:** Das Instanz-Modell (ADR 0004/0007) macht Small-Team-Support
  ungewöhnlich billig (keine Tenant-Isolation) — und Enterprise-Multi-Tenant
  unattraktiv teuer. Die Architektur *zeigt* die richtige Grenze.
- **Nutzerwert:** Capture + AI-Ordnung + befragbares Wissen wird im Team
  wertvoller (gemeinsames Gedächtnis, Offboarding-Sicherheit, „ask the brain"
  statt „ask Sarah").
- **Wettbewerb:** Team-Wikis sind gesättigt (Docmost/Outline/BookStack, frei) —
  dort nicht angreifen. Die Lücke: **selbst gehostetes, capture-first Team-
  Wissen mit granularer AI-Kontrolle** — niemand besetzt sie.
- **Aufwand:** 4 schlanke Epics (E41–E44), die massiv auf Vorhandenem aufbauen
  (E34 Git, E26 Templates, E36 Keys, E38 Permission-Muster, E39-2 Endpoints).
- **Produktfokus:** Die „NOT build"-Liste schützt den Kern; Kollaboration
  heißt bei uns geteiltes Gedächtnis, nicht Echtzeit-Redaktion.
- **Privacy/AI/Self-Hosting:** Team-Modus *verstärkt* die Positionierung
  (Admin-AI-Policy, LAN-only-Fähigkeit ab Phase N, Instanz-Souveränität) statt
  sie zu verwässern. „Professional" ist kein vierter Modus, sondern unser
  Normalzustand (Self-Hosting-DNA).

**Antwort auf die Kernfrage:** Aus dem sehr guten persönlichen Second Brain
wird ein gemeinsames Wissenssystem, indem wir **genau drei Dinge** hinzufügen —
Identität, Sichtbarkeit, Team-AI-Kontrolle — und **alles andere** der
bestehenden Maschine überlassen: Capture-Pipeline, Klassifikation, Vault,
Suche, RAG, Git-Historie, Templates, Self-Hosting. Notion, Slack, Jira und
Google Docs bauen wir ausdrücklich nicht nach; wo Teams solche Werkzeuge
brauchen, verbinden wir sie (E35) statt sie zu ersetzen.

**Roadmap-Änderung:** Neue Phase **O — Shared Knowledge & Small Teams**
(E41–E44) nach dem Phase-N-Kern; E33-1 um `actor` erweitert (Begründung:
Abschnitt 28); keine bestehenden Punkte entfernt.
