# Public GitHub Presence Audit — September 2026

> **Status:** Analyse + umgesetzte Bereinigung der öffentlichen Repo-Präsenz.
> Keine Lizenzänderung, keine Rechtsberatung, keine Git-Historie umgeschrieben.
> Normative Produkt-/Deployment-Wahrheit: [ADR 0008](adr/0008-deployment-models-self-hosted-first.md).

---

## A. Current Public Repo Impression (vor Bereinigung)

| Zielgruppe | Eindruck |
|------------|----------|
| **Potenzielle Nutzer** | Stark persönlich („Ich verliere Ideen…“), Showcase-/Portfolio-Status im ersten Satz; Produktreife unklar (README nannte v0.2.x, 360 Tests — veraltet). |
| **Entwickler** | Technisch solide (CI, ADRs, Tests), aber CONTRIBUTING/Issues auf Deutsch; Portfolio-Framing statt Produkt-Repo. |
| **Security-orientiert** | SECURITY.md inhaltlich gut, aber Deutsch; klare Advisory-Meldung vorhanden. |
| **Contributor** | Unklar ob Contributions erwünscht; „Portfolio-Repo“ suggeriert Showcase statt wartbares Produkt. |

**Gesamt:** Kompetentes Projekt, aber die **erste Leseebene** (README, Repo-Beschreibung, CONTRIBUTING) kommunizierte noch **Lern-/Portfolio-Phase**, nicht „echtes Produkt in Entwicklung“.

---

## B. Veraltete / problematische Stellen

| Datei | Problem | Aktion |
|-------|---------|--------|
| `README.md` | Portfolio/Showcase, Lernabschnitt, Duplikat DE/EN, v0.2.x / 360 Tests | **NOW** — Produkt-README EN, aktualisiert |
| GitHub Repo Description | „MIT portfolio“ | **NOW** — via `gh` (Maintainer) |
| `CONTRIBUTING.md` | Portfolio-Repo, DE only | **NOW** — EN, ehrliches Solo-Modell |
| `SECURITY.md` | DE only (öffentlich) | **NOW** — EN |
| `.github/ISSUE_TEMPLATE/*` | DE, veraltete ROADMAP-Phasen | **NOW** — EN, Phasen aktualisiert |
| `.github/pull_request_template.md` | DE | **NOW** — EN |
| `app/ui/settings.py` | „Portfolio-Edition“ (nutzersichtbar) | **NOW** — Produktwording |
| `docs/licensing.md` | „Portfolio-Edition“ in Tabelle | **NOW** — „Open Source (MIT)“ |
| `docs/adr/0005-*.md` | Bewerbungs-/Portfolio-Strategie historisch | **KEEP** + Hinweis auf Messaging-Update |
| `docs/integrations/README.md` | „fürs Portfolio“ | **NOW** — Produktwording |
| `CHANGELOG.md` v0.1.0 | „Lern-/Portfolio-Projekt“ | **KEEP** (Historie) |
| Keine GitHub Releases/Tags | Kein `v0.3.0` Release artefakt | **LATER** (E29-3 / Launch) |

---

## C. Lizenzstatus (sachlich, keine Rechtsberatung)

| Frage | Stand |
|-------|--------|
| **Hauptlizenz** | [MIT](LICENSE) — Standardtext, Copyright „Yannik Leekes“, 2026 |
| **Eigenes Repo MIT?** | Ja — `LICENSE` im Root; GitHub API bestätigt `license: mit` |
| **Andere Lizenzen** | Dependencies überwiegend permissiv (FastAPI, SQLAlchemy, …); `pip-audit` in CI. Keine AGPL/GPL in `requirements.txt` geprüft. Asset-Screenshots: projekteigen (`docs/assets/`). |
| **Öffentlich seit** | Repo erstellt **2026-05-22** (erster Commit); MIT seit früher Phase (LICENSE zuletzt 2026-05-28) |
| **Veröffentlichte Releases** | **Keine** GitHub Releases/Tags zum Audit-Zeitpunkt — nur `main` |
| **Rechte an veröffentlichten Commits** | Unter MIT: Nutzung/Kopie/Modifikation/Weitergabe erlaubt (mit Copyright-Hinweis). Bereits geklonte Commits bleiben MIT, auch wenn spätere Releases anders lizenziert werden |
| **Zukünftige Versionen anders?** | **Prinzipiell ja** — ADR 0005 sieht kommerzielle Edition / Lizenzwechsel für *neue* Releases vor; bestehende MIT-Commits bleiben MIT |
| **Repo privat stellen?** | Technisch jederzeit möglich; **bereits geklonte/forkte MIT-Kopien** bleiben legal nutzbar. Kein „Rückruf“ der MIT-Version |

**Offene Product/Legal Decision:** Ob kommerzielles Release als **Open Core**, **Dual License**, **reine proprietäre Distribution** oder **MIT + paid services** — siehe Abschnitt G.

---

## D. Public vs. Private — Empfehlung

| | |
|---|---|
| **Jetzt** | **Public beibehalten** — Vertrauen, Issues, Security Advisories, Contributor-Sichtbarkeit, kein Secret im Repo (nur `.env.example`) |
| **Vorteile public** | Transparenz (Privacy-Positionierung), CI-Badge-Effekt, Fork-/Clone-fähig, Portfolio-Ersatz nicht nötig wenn README produktorientiert |
| **Risiken** | MIT-Forks jederzeit möglich; Ideen/Architektur sichtbar; muss weiterhin keine Secrets committen |
| **Trigger für private** | Nur bei konkretem Geschäftsgrund (z. B. proprietärer Core vor Launch) — **nicht** als Security-Ersatz |
| **Sensibles im Repo?** | Keine Secrets gefunden; Lizenz-Signing-**Secrets** gehören nicht ins Repo (ADR 0005) — korrekt |

---

## E. Sprachstrategie (Empfehlung)

| Bereich | Jetzt | Später |
|---------|-------|--------|
| README, CONTRIBUTING, SECURITY | **EN** (umgesetzt) | — |
| Issue/PR Templates | **EN** (umgesetzt) | — |
| Neue Commits, Branches, PR-Titel | **EN ab sofort** | — |
| ROADMAP, ADRs, `current-state`, Engineering | DE (intern) | schrittweise EN oder zweisprachig vor Launch |
| Web-UI / Setup | DE (Nutzer) | i18n bei Launch (E47+) |
| CHANGELOG | DE | Release Notes EN bei GitHub Releases |

**Git-Historie:** nicht umschreiben.

---

## F. Empfohlene README-Struktur (umgesetzt)

1. Name + one-line value proposition  
2. Status (version, maturity, deployment model)  
3. Key capabilities (kurz)  
4. Screenshots  
5. Deployment (self-hosted now; managed cloud vision, not available)  
6. Quick start (link to packaging/self-hosting)  
7. Privacy & security (link SECURITY.md)  
8. Documentation index  
9. Contributing  
10. License  

Kein Marketing-Blurb, kein Lern-/Showcase-Abschnitt.

---

## G. Konkrete Änderungen — Klassifikation

| Item | Klasse |
|------|--------|
| README / CONTRIBUTING / SECURITY / Templates / Settings / licensing.md / integrations README | **NOW** (dieser PR) |
| GitHub Releases für v0.3.0 | **LATER** (Launch-Härtung) |
| Vollständige UI-i18n | **LATER** (E47+) |
| ADR 0005 Strategie (MIT → Commercial) | **NEEDS PRODUCT/LEGAL DECISION** vor Verkauf |
| Open Core vs. Dual License vs. MIT+Services | **NEEDS PRODUCT/LEGAL DECISION** |
| Trademark / Domain / Branding | **LATER** (bewusst nicht heute) |
| `docs/integrations/README.md` Portfolio-Zeile | **NOW** |
| Historische ADRs/Audits/Changelog v0.1.0 | **KEEP** |

### Geschäftsmodell vs. MIT (Diskussion, keine Entscheidung)

| Modell | Passt zu… | Risiko / Trade-off |
|--------|-----------|-------------------|
| **MIT beibehalten** | Vertrauen, OSS-Narrativ, Self-hosters | Kommerzielle Forks legal |
| **Open Core** | Paid Features (Cloud, Managed AI, Backup) | Grenze Core/Pro pflegen |
| **Dual License** | Enterprise / kommerzielle Nutzung | Komplexität |
| **Proprietär ab Release N** | Maximale Kontrolle | Vertrauensverlust, Fork-Druck |
| **MIT + Services** (Support, Cloud, Hosting) | ADR 0008-Richtung | Wettbewerb kann Code kopieren |

**Empfehlung für Timing:** Entscheidung **vor E21-2 / kommerziellem Release** — nicht blockierend für tägliche Entwicklung (E47 als Nächstes).

---

## Referenzen

- [ADR 0004 — Commercial consumer product](adr/0004-commercial-consumer-product.md)
- [ADR 0005 — Repo & license strategy](adr/0005-repo-and-license-strategy.md)
- [ADR 0008 — Deployment models](adr/0008-deployment-models-self-hosted-first.md)
- [current-state.md](current-state.md)
