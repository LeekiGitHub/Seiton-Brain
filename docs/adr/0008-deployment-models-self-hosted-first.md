# ADR 0008: Deployment-Modelle — self-hosted zuerst, Managed Cloud Teil der Produktvision

- **Status:** Accepted
- **Datum:** 2026-08-30
- **Entscheider:** Yannik
- **Bezug:** **präzisiert [ADR 0004](./0004-commercial-consumer-product.md)** (hebt
  dessen absolute Aussagen zu „wir betreiben nichts" / „SaaS bewusst verworfen" auf)
  · rahmt [ADR 0007](./0007-cloud-edition-subscription.md) (bleibt *Proposed*)
- **Gilt als aktuelle Wahrheit für:** Produktidentität, Verhältnis Self-hosted ↔
  Managed Cloud, Deployment-Neutralität des Product Core, Isolationsgrenze

## Kontext

Die normative Dokumentation widersprach sich an einer produktstrategisch
zentralen Stelle:

- **ADR 0004 (Accepted)** formuliert absolut: *„Wir betreiben nichts"*,
  *„SaaS wurde bewusst verworfen"*, *„kein Cloud-Dienst"*, *„Abo-Modell: wir
  betreiben nichts Laufendes"*. Abgeleitete Dokumente übernahmen das
  (`SECURITY.md`: „Es gibt keinen zentralen Seiton-Cloud-Dienst";
  `docs/self-hosting.md`: „ohne dass wir Server betreiben";
  `docs/licensing.md`: „Nicht im Scope: gehosteter Betrieb durch uns";
  Setup-UI: „100 % self-hosted").
- **ADR 0007 (Proposed)** und **ROADMAP Phase I (E24)** planen gleichzeitig eine
  Managed Cloud mit Abo.

Für Menschen war das als zeitliche Abfolge lesbar. Für Agents und für neue
Mitlesende war es ein echter Widerspruch — und ADR 0004 ist der bindendere
Text. Ohne Auflösung besteht das Risiko, dass eine spätere Cloud entweder
architektonisch verbaut oder als „verworfen" behandelt wird.

Zusätzlich ist der Anspruch entstanden, den Product Core **deployment-neutral**
zu halten, ohne heute Cloud-Abstraktionen auf Vorrat zu bauen.

## Entscheidung

### 1. Produktidentität

**Seiton Brain ist ein persönliches AI-gestütztes Second Brain.**
Self-hosting ist ein **Deployment-Modell** und ein starkes Privacy-/
Control-Angebot — es ist **nicht** die Identität des Produkts.

Nutzer sollen langfristig wählen können, ob sie Seiton selbst betreiben oder
eine vollständig verwaltete Seiton-Cloud nutzen.

### 2. Reihenfolge: self-hosted zuerst

Die zuerst entwickelte und ausgelieferte Betriebsform bleibt **self-hosted**
(Heimserver, Mini-PC, geeignetes NAS, Mac-/Linux-System, eigener VPS).
Begründung unverändert: Die Architektur trägt das bereits, der Betrieb ist
weitgehend vorhanden, das Privacy-/Security-Modell passt, und es vermeidet
jetzt zusätzliche Cloud-Komplexität.

**Die Managed Cloud ist ausdrücklich kein V1-Blocker.**

### 3. Deployment-neutraler Product Core

Der Product Core bleibt in beiden Betriebsformen **derselbe Code**:

FastAPI · Knowledge Core · Capture · Retrieval · RAG · Connectoren ·
PostgreSQL · pgvector · Worker · LLM-Provider-Layer · REST-API · Web-UI/PWA

Unterschiede zwischen Self-hosted und Managed Cloud sollen langfristig
**ausschließlich** in diesen Bereichen liegen:

Provisionierung · Deployment · Identity · Billing · Tenant-/Instance-Verwaltung ·
Secrets Management · Backup Operations · Monitoring · Updates · Support

Self-hosted und Managed Cloud werden **nicht zwei getrennte Produkte**.
Konkret heißt das für den Alltag: Eine Änderung am Core darf nicht davon
abhängen, in welcher Betriebsform sie läuft; wo doch, gehört die Fallunter-
scheidung in die Konfiguration oder das Deploy-Profil (`SEITON_DEPLOY_MODE`),
nicht in die Fachlogik.

### 4. Keine Cloud-Abstraktionen auf Vorrat

Ausdrücklich **nicht** vorsorglich entwickeln:

Kubernetes · mandantenfähiges Datenmodell · Billing-System ·
Cloud-Provisionierungsplattform · Account-System allein für eine hypothetische
Cloud · Cloud-spezifische Microservices.

Deployment-Neutralität wird durch **saubere Modulgrenzen** erreicht, nicht durch
zusätzliche Abstraktionsschichten.

### 5. Isolationsgrenze (aktueller Horizont)

Für die heutige self-hosted Architektur ist **eine Seiton-Instanz die
Sicherheits- und Isolationsgrenze**. Eine mögliche erste Managed Cloud kann
ebenfalls auf **Single-Tenant-/Instance-Provisionierung** aufbauen.

Heute wird **keine mandantenfähige Datenarchitektur** und **kein
`user_id`-Mandantenschlüssel** eingeführt. Nutzerkonten innerhalb einer Instanz
sind für Authentifizierung, Attribution und Berechtigungen ausdrücklich
vorgesehen (Phase O) — nur nicht als Mandantenschlüssel.

Ob eine spätere Cloud eine andere Isolationsarchitektur benötigt, wird **bei
nachgewiesenem Bedarf bewusst neu bewertet**. Dies ist **keine** irreversible
„niemals Multi-Tenant"-Festlegung.

### 6. Was an ADR 0004 damit aufgehoben ist

| Aussage in ADR 0004 | Status ab ADR 0008 |
|---|---|
| „Wir betreiben nichts" | **aufgehoben** — gilt für die self-hosted Edition, nicht als Dauerprinzip |
| „SaaS wurde bewusst verworfen" | **aufgehoben** — Managed Cloud ist Teil der Produktvision, zeitlich nachgelagert |
| „Abo-Modell: Entscheider will Einmal-Kauf" | **aufgehoben als Ausschluss** — Erlösmodell der Cloud ist offen (ADR 0007) |
| „Daten verlassen die Box nie, kein Cloud-Dienst" | **präzisiert** — gilt für die self-hosted Edition |
| Buy-once, BYO-Key, self-hosted zuerst | **unverändert gültig** |
| UI-first, lokale Web-UI, kein Native-Desktop-Nahziel | **unverändert gültig** |
| Long-Polling, Always-on-Box, Offline-Lizenz | **unverändert gültig** |
| n8n-Custom-Node entfällt | **unverändert gültig** |

### 7. ADR 0007 bleibt *Proposed*

ADR 0008 entscheidet die **Positionierung** (Cloud gehört zur Vision, Core bleibt
gemeinsam). ADR 0007 entscheidet die **Geschäfts- und Betriebsfrage** (Abo,
Preis, DSGVO-Auftragsverarbeitung, Betriebsbereitschaft) — die bleibt offen, und
**E24 bleibt gesperrt**.

## Zielbild

```
                    SEITON PRODUCT CORE
                             │
              ┌──────────────┴──────────────┐
              │                             │
       MANAGED SEITON CLOUD            SELF-HOSTED
       spaeterer einfacher Weg         Control/Privacy-Weg
              │                             │
       wir betreiben                     Nutzer betreibt
       Infrastruktur                     Infrastruktur
              │                             │
       Browser / PWA                  Browser / PWA
       spaeter ggf. Mobile            spaeter ggf. Mobile
              │                             │
       Managed AI / BYOK              BYOK / lokale AI /
       je nach Tarif                  optional Managed AI
```

Zielbild, **keine** Implementierungsreihenfolge.

## Zeitliche Einordnung

| Stufe | Betriebsform | Inhalt |
|---|---|---|
| **V1 / private Beta** | self-hosted | Capture · Organisation · Retrieval · RAG · Privacy · Backup-/Restore-Grundlage · gute UX · PWA |
| **V1.5 / erste Produktreife** | self-hosted verkaufsfähig | erste echte Nutzererfahrung; optional Managed AI und weitere Privacy-/Convenience-Funktionen |
| **später** | Managed Seiton Cloud | kein eigener Server nötig · Registrierung · Provisionierung · automatische Updates · Backup · Monitoring · Consumer-Onboarding · ggf. Managed AI |

Die Stufen entsprechen der bestehenden Roadmap-Struktur (Phase L → Phase M/N →
Phase I/E24); es werden keine Versionsnummern neu vergeben.

## Konsequenzen

### Positiv

- Eine eindeutige aktuelle Wahrheit für Produktidentität und Deployment.
- Die Cloud verschwindet nicht aus der Vision und dominiert die Roadmap nicht.
- Deployment-Neutralität wird zur überprüfbaren Anforderung an neue Stories,
  statt implizit zu bleiben.
- Kein Umbau heute: Die Entscheidung erzeugt **keine** Codeänderung.

### Negativ / Trade-offs

- Das Marketing-Argument „wir betreiben nichts, deine Daten verlassen nie deine
  Maschine" gilt nur noch **für die self-hosted Edition** und muss dort
  entsprechend formuliert werden.
- Sollte die Cloud kommen, entstehen DSGVO-Auftragsverarbeitung und
  Betriebsverantwortung — das bleibt der schwerste offene Punkt (ADR 0007).
- „Deployment-neutral" ist eine Disziplin-Anforderung ohne automatische
  Durchsetzung; sie muss in Reviews mitgedacht werden.

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|---|---|
| ADR 0004 unverändert lassen | Der Widerspruch zu ADR 0007 bliebe bestehen und würde von Agents als „Cloud verworfen" gelesen |
| ADR 0004 inhaltlich überschreiben | ADRs sind Entscheidungshistorie; sie werden präzisiert oder abgelöst, nicht rückwirkend umgeschrieben |
| ADR 0007 jetzt auf *Accepted* setzen | Die Geschäfts- und Betriebsentscheidung (Abo, DSGVO, Bereitschaft) ist nicht getroffen |
| Cloud jetzt architektonisch vorbereiten | Abstraktionen auf Vorrat ohne bekannte Anforderungen; widerspricht Entscheidung 4 |
| Zwei Produktlinien (self-hosted / Cloud) | Doppelte Wartung für einen Solo-Entwickler; widerspricht Entscheidung 3 |

## Referenzen

- [ADR 0004 — Kommerzielles Produkt](./0004-commercial-consumer-product.md)
- [ADR 0006 — Ein Stack](./0006-consumer-stack-no-sqlite-fork.md)
- [ADR 0007 — Cloud-Edition mit Abo](./0007-cloud-edition-subscription.md) (Proposed)
- Analyse-Grundlage: [`docs/PRODUCT_ARCHITECTURE_REVIEW.md`](../PRODUCT_ARCHITECTURE_REVIEW.md)
- Roadmap: [`ROADMAP.md`](../../ROADMAP.md) · Kurzstand: [`docs/current-state.md`](../current-state.md)
