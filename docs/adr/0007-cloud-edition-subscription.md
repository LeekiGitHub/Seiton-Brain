# ADR 0007: Cloud-Edition mit Abo (Hosted + Managed LLM) — Vorschlag

- **Status:** Proposed (Entscheidung offen)
- **Datum:** 2026-08-08
- **Entscheider:** Yannik
- **Bezug:** revidiert bei Annahme Teile von [ADR 0004](./0004-commercial-consumer-product.md)
  („SaaS bewusst verworfen", „kein Abo")

## Kontext

ADR 0004 legt das Produkt als **self-hosted, buy-once, BYO-Key** fest. Das
schließt zwei Kundengruppen aus:

1. Kunden, die **nicht selbst hosten** wollen/können (keine Always-on-Box,
   kein Docker, kein Tailscale).
2. Kunden, die **keinen eigenen LLM-Key** anlegen wollen — für Laien ist
   „OpenAI-Konto + API-Key + Billing" eine echte Hürde.

Idee (2026-08-08): zusätzlich zur bestehenden Edition eine **Cloud-Edition im
Abo** anbieten — wir hosten die Instanz und liefern LLM-Zugang inklusive
(Managed LLM). Telegram bleibt optional; Haupteingang wäre Web-UI/App.

## Spannungsfelder (Grund, warum das ein ADR braucht)

| Punkt | ADR 0004 (heute) | Cloud-Edition (Vorschlag) |
|-------|------------------|---------------------------|
| Betrieb | „Wir betreiben nichts" | 24/7-Betrieb, Uptime-Verantwortung |
| Daten | verlassen nie die Kundenmaschine | liegen bei uns → **DSGVO-Auftragsverarbeitung** (AVV, TOMs, Löschkonzept, EU-Hosting) |
| Kosten | BYO-Key, keine Inferenzkosten | Inferenzkosten bei uns → **Quota/Metering zwingend** |
| Erlösmodell | buy-once | wiederkehrend (Abo) — betriebswirtschaftlich attraktiv |
| Codebasis | single-user, localhost-UI | braucht **UI-Auth** und Mandanten-Konzept |

## Optionen

1. **Single-Tenant-Instanzen (empfohlen als Startpunkt):** pro Kunde eine
   isolierte Instanz (bestehender Docker-Stack, automatisch provisioniert,
   EU-Hoster z. B. Hetzner/IONOS). Kein Multi-Tenancy-Umbau der Codebasis;
   Datenisolation per Design; Preis muss Instanzkosten (~5–10 €/Monat Infra
   + LLM-Quota) decken.
2. **Multi-Tenant-SaaS:** eine Plattform, Mandanten-Modell in DB/Vault.
   Deutlich größerer Umbau (User-Modell überall, Vault-Namespacing,
   Noisy-Neighbor, Security-Fläche). Erst sinnvoll ab vielen Kunden.
3. **Partner-/Marketplace-Hosting:** z. B. Umbrel/Start9/PikaPods-Listing —
   „hosted" ohne eigenen Betrieb. Geringster Aufwand, aber ohne Abo-Erlös
   und ohne Managed LLM.

**Managed LLM** (unabhängig von 1/2): ein dünner Proxy mit unserem Key,
per-Kunde-Quota (Tokens/Monat), Kostendeckel, Modell-Whitelist. Auch für
Self-Hosted-Kunden als Zusatz-Abo denkbar („kein eigener Key nötig").

## Vorläufige Empfehlung

- **Option 1 + Managed LLM**, aber erst nach Vorarbeiten, die auch
  self-hosted Nutzen stiften: **UI-Auth (E23-1)** und **UI-Capture (E22-1)**
  sind harte Voraussetzungen und in jedem Szenario nötig.
- Option 3 parallel prüfen (geringer Aufwand, Distribution).
- Buy-once-Edition bleibt bestehen (ADR 0004 wird ergänzt, nicht ersetzt).

## Entscheidung

**Offen.** Stories unter Epic **E24** sind bis zur Annahme dieses ADR
gesperrt (außer E24-1 = diese Entscheidung herbeiführen).

## Konsequenzen bei Annahme

- DSGVO-Paket nötig: AVV-Vorlage, Datenexport, Löschkonzept, EU-Region.
- Abo-Billing (z. B. Stripe) + Entitlements neben Offline-Lizenz (E21-1).
- Betriebsverantwortung: Monitoring, Backups, Incident-Prozess — bricht mit
  „passives Einkommen, wir betreiben nichts"; realistisch als bewusster
  Trade-off gegen wiederkehrenden Umsatz.

## Referenzen

- [ADR 0004 — Kommerzielles Produkt](./0004-commercial-consumer-product.md)
- [ADR 0005 — Repo- & Lizenzstrategie](./0005-repo-and-license-strategy.md)
- [ADR 0006 — Ein Stack](./0006-consumer-stack-no-sqlite-fork.md)
- Roadmap: Epics **E22–E25** in [`ROADMAP.md`](../../ROADMAP.md)
