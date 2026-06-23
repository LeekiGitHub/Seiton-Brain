# ADR 0004: Kommerzielles Produkt — self-hosted Consumer-App (buy-once, BYO-key)

- **Status:** Accepted (Geschäftsmodell) · Detail-Architektur teils offen
- **Datum:** 2026-06-21
- **Entscheider:** Yannik
- **Bezug:** ergänzt und überschreibt Teile von [ADR 0003](./0003-engine-and-adapters.md)

## Kontext

Seiton Brain war ursprünglich als **persönliches Open-Source-Projekt** geplant
(siehe ADR 0003: Engine + Adapter, Telegram/Obsidian als Default-Adapter, n8n als
Integrationsschicht, Mac Mini als 24/7-Host). Die Architektur und Roadmap sind
entsprechend auf einen **technischen Selfhoster** zugeschnitten.

Neue Ausrichtung (Entscheidung 2026-06-21): Seiton Brain soll als **kommerzielles
Produkt** verkauft werden. Geschäftsmodell-Eckpunkte des Entscheiders:

- **Einmal kaufen** (kein Abo), Kunde besitzt eine Lizenz.
- **Self-hosted beim Kunden**, der Kunde verantwortet seine eigenen Daten.
- **Bring-your-own-Key**: Kunde nutzt eigene LLM-/Whisper-Konten und API-Keys.
- **Wir betreiben nichts**: keine fremden Daten, keine Inferenzkosten, keine
  Server-/Uptime-Verantwortung. Wir liefern Software + Bugfixes + Updates.
- **Zielgruppe: Privatpersonen** (Consumer), nicht Enterprise.
- **Ziel: weitgehend passives Einkommen** über Produktverkauf.

Dieses Modell passt gut zur Sensibilität der Daten (Bewerbungen, Zeugnisse,
Rechnungen, „zweites Gehirn"): „Deine Daten verlassen nie deine Maschine" wird
zum **Verkaufsargument** statt zur Haftungslast. SaaS wurde bewusst verworfen
(DSGVO-Auftragsverarbeitung für hochsensible Daten, Inferenzkosten-Risiko,
24/7-Betrieb — siehe „Alternativen").

## Zentrale Spannung

**Privatpersonen + self-hosted beißt sich.** Der heutige Stack (Docker, Postgres,
Redis, Celery, öffentlich erreichbarer Telegram-Webhook via ngrok/Cloudflare) ist
für nicht-technische Consumer **nicht einrichtbar**. Für „passives Einkommen"
ist das fatal: Jede Setup-Reibung erzeugt Support-Last. **Make-or-break des
Produkts ist Distribution & Einrichtung, nicht der Funktionsumfang.**

## Entscheidung

1. **Produkt = self-hosted Consumer-App.** Verkauf als einmal kaufbare Lizenz,
   BYO-Key, Daten bleiben beim Kunden.

2. **UI wird die Hauptoberfläche — als lokal ausgelieferte Web-UI.** Setup-Wizard,
   Dashboard, Verwalten, Suche und `/ask`-Retrieval laufen im Browser, **serviert
   vom Always-on-Host des Kunden** (nicht von uns). Begründung: Web-UI ist
   plattformunabhängig (jedes Gerät hat einen Browser → Mac/Win/Linux/Handy) und
   passt zur Always-on-Realität, während eine native Desktop-App auf einem
   nicht-24/7-Laptop dem Anspruch widerspricht. **Datenschutz:** an localhost/LAN
   gebunden, Fernzugriff über privates Netz (Tailscale o. Ä.) — Daten verlassen
   die Box nie, kein Cloud-Dienst. Eine native Desktop-App ist damit **kein
   Nahziel** (evtl. ganz unnötig). **Telegram wird vom Default-Eingang zum
   optionalen Power-Feature** (mobiles Erfassen) — die ADR-0003-Annahme „Telegram
   = Default-Adapter" wird bewusst revidiert.

3. **Telegram per Long-Polling statt Webhook** für lokales/Consumer-Hosting —
   entfernt die Anforderung einer öffentlichen HTTPS-URL (kein ngrok/Tunnel
   nötig). Webhook bleibt für Server-/VPS-Betrieb optional.

4. **Always-on-Box beim Kunden ist das Leitbild.** Ein „zweites Gehirn", das von
   unterwegs (per Telegram) erreichbar sein soll, braucht eine 24/7-Komponente.
   Primärziel: **Heimserver / Mini-PC / Mac Mini** beim datenschutz-affinen
   Privatkunden (passt zum Privacy-Verkaufsargument). **VPS** (z. B. IONOS) ist
   eine **spätere** Alternative, kein Nahziel. Vorbilder dieses Genres: Home
   Assistant (+ Nabu Casa/Green-Hardware), Plex/Jellyfin (Relay), Umbrel/Start9
   (Personal-Server-OS), Synology (QuickConnect).

   **Fernzugriff ohne Router-Konfiguration** (der sonst schwerste Teil): Telegram
   per **Long-Polling** (Box ruft ausgehend an Telegram → kein offener Port, keine
   öffentliche IP); UI von unterwegs über **Tailscale** o. Ä. (laien-tauglich).

5. **Auslieferung gestaffelt.** Zuerst eine **reduzierte Version** (stark
   vereinfachtes Setup / gebündelter Installer für die Heim-Box). Eine native
   Desktop-App ist **bewusst kein Nahziel** (Web-UI deckt den Bedarf ab; siehe
   Festlegung 2). Updates (inkl. Auto-Update) sind Teil des Produktversprechens.

6. **Lizenzierung offline-fähig.** Buy-once-Lizenzschlüssel muss **ohne unseren
   Server** validierbar sein (wir wollen ja gerade nichts betreiben).

7. **n8n als Produkt-Feature entfällt.** Die REST-API (E13) bleibt — Power-User
   können n8n selbst per HTTP anbinden. Wir **bauen und pflegen aber keine
   Custom-n8n-Node** mehr (E14-2 gestrichen).

## Konsequenzen

### Roadmap (siehe `ROADMAP.md`)

- **Gestrichen/zurückgestellt:** E14 (n8n-Ökosystem), insb. E14-2 Custom Node.
- **Reframed:** E9 (Hosting) von „Mac Mini" → „Multi-Plattform-Self-Hosting +
  VPS"; E1 bekommt Long-Polling-Option; E16 (Setup) verschiebt sich von CLI/TUI
  in die UI; E15-4 (read-only Web-UI) geht in das UI-Epic auf.
- **Neu:** Epic UI/Dashboard, Epic Packaging & Distribution, Epic Commercial/
  Licensing.

### Architektur

- UI-first; Telegram optional; Long-Polling-Pfad.
- **Stack-Vereinfachung für die Consumer-Edition zu evaluieren** (z. B. SQLite
  statt Postgres, in-process Worker statt Redis/Celery), um die Anzahl
  beweglicher Teile beim Endnutzer zu minimieren. Server-/VPS-Edition kann den
  vollen Stack behalten.

### Positiv

- Keine fremden Daten → keine DSGVO-Auftragsverarbeitung, keine Inferenzkosten.
- Privacy als Verkaufsargument statt Last.
- Geringe laufende Betriebslast für einen Solo-Entwickler.

### Negativ / Trade-offs

- „Einmal kaufen" = kein wiederkehrender Umsatz → braucht stetig neue Käufer
  (Marketing). „Passiv" nur, wenn die Installation **wirklich** reibungslos ist.
- Consumer-Distribution (Installer/Desktop-App, Auto-Update, Code-Signing pro OS)
  ist erheblicher Neu-Aufwand gegenüber „docker compose up".
- „Editionen" sind voraussichtlich **ein Stack an verschiedenen Hosting-Orten**
  (Heim-Box vs. VPS), **keine** zwei Codebasen. Eine echte Zwei-Produkt-Trennung
  ist unwahrscheinlich und wird aufgeschoben, bis es einen konkreten Grund gibt.

## Entschieden (2026-06-22)

- **Deployment-Leitbild:** Always-on-Box beim Kunden (Heimserver/Mini-PC/Mac
  Mini). VPS = spätere Alternative, kein Nahziel.
- **UI-Form:** lokal ausgelieferte **Web-UI** (kein natives Desktop-App-Nahziel).
- **Fernzugriff:** Telegram Long-Polling + Tailscale o. Ä. statt Router-Konfig.
- **Fokus jetzt:** Produkt selbst (Web-UI E19 + Retrieval E17, Telegram
  Long-Polling E1-5). Verkaufsspezifisches (E21) ist geparkt.

## Offene Detailentscheidungen

- **Wie weit Stack-Vereinfachung?** SQLite/in-process für die Heim-Box ja/nein
  (E9-5, Eval). „Editionen" voraussichtlich ein Stack, verschiedene Hosting-Orte.
- **UI-Tech-Stack** (welches Framework für die lokale Web-UI).
- **Distributionsform der reduzierten Version:** gebündelter Installer um den
  bestehenden Stack vs. nur radikal vereinfachtes Setup.
- **Lizenz-Mechanik & Verkaufskanal** — geparkt, bis Produkt steht.

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|-------------|--------------|
| Hosted SaaS | DSGVO-Auftragsverarbeitung für hochsensible Daten, Inferenzkosten-Risiko, 24/7-Betrieb — widerspricht Ziel „passiv, keine fremden Daten" |
| Abo-Modell | Entscheider will Einmal-Kauf; wir betreiben nichts Laufendes |
| Reines Open-Source ohne Verkauf | Bisheriger Stand; kein Einkommen |
| n8n-Node bauen/pflegen | Kein Mehrwert für Privatkunden; Wartungslast (eigenes Repo, npm, n8n-Review) |
| Enterprise-Fokus | Andere Zielgruppe, Vertrieb/Support-intensiv |

## Referenzen

- ADR 0003 (Engine + Adapter): [`0003-engine-and-adapters.md`](./0003-engine-and-adapters.md)
- Roadmap: [`ROADMAP.md`](../../ROADMAP.md)
- Architektur: [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
