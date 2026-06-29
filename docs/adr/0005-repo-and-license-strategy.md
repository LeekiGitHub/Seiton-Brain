# ADR 0005: Repo- & Lizenzstrategie (Portfolio jetzt, Produkt später)

- **Status:** Accepted
- **Datum:** 2026-06-26
- **Entscheider:** Yannik
- **Bezug:** [ADR 0004 — Kommerzielles Produkt](./0004-commercial-consumer-product.md)

## Kontext

Seiton Brain startete als **öffentliches GitHub-Repo (MIT)** — sinnvoll für
Portfolio, Bewerbungen und sichtbare Entwicklung. Parallel gilt [ADR 0004]:
langfristig **kommerzielles, self-hosted Consumer-Produkt** (buy-once, BYO-Key).

Die Frage: Wann und wie vom öffentlichen Entwicklungsrepo zur verkaufsfertigen
Edition wechseln, ohne Portfolio-Wert zu verlieren?

## Entscheidung

### Phase 1 — Jetzt (bis Stelle oder verkaufsfertiges Produkt)

1. **Repo bleibt public**, Lizenz vorerst **MIT**.
2. **README und Doku** kommunizieren ehrlich: öffentliche Entwicklung /
   Portfolio-Projekt; geplante kommerzielle Consumer-Edition (ADR 0004).
3. **Kein Custom-n8n-Node** als Produktfeature (ADR 0004) — REST-API +
   `examples/n8n/` für Power-User reichen.
4. **Sensibles für später privat halten:** Lizenzschlüssel-Algorithmus,
   Payment/Store-Integration, Signier-Secrets für Installer.

### Phase 2 — Trigger (einer von beiden reicht)

- **Bewerbungsziel erreicht** (festanstellung) *oder*
- **Produkt verkaufsbereit** (E19 UI + E20 Packaging + E21 Lizenzierung)

### Phase 3 — Dann

1. **Neue Major / neues Repo** für die kommerzielle Edition **oder**
   Lizenzwechsel auf neue Releases (bestehende MIT-Commits bleiben MIT).
2. Public Repo **archivieren** oder als eingefrorenes „Technical Foundation /
   Portfolio-Snapshot" belassen (Tag `portfolio-vX.Y`).
3. **Verkauf = Distribution + UI + Lizenz + Updates**, nicht „bitte kaufen
   trotz identischem MIT-Repo".

## Konsequenzen

### Positiv

- Portfolio profitiert sofort von sichtbarem Code, ADRs, Tests, CI.
- Kein vorzeitiger Druck, alles zu schließen, bevor E19–E21 existieren.
- Klare Erwartung für spätere Käufer und Forker.

### Negativ / Trade-offs

- Forks der MIT-Version sind bis Phase 3 legal möglich — akzeptiert als
  bewusster Trade-off für Karriere-Sichtbarkeit.
- README/Doku müssen Portfolio- und Produkt-Narrativ parallel führen.

## Referenzen

- ADR 0004: [`0004-commercial-consumer-product.md`](./0004-commercial-consumer-product.md)
- ROADMAP Epics E19–E21
