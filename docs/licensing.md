# Lizenzierung (E21)

Seiton Brain ist aktuell ein **öffentliches MIT-Projekt** (Portfolio-Edition).
Für die geplante **kommerzielle Consumer-Edition** (buy-once, self-hosted, ADR
0004) gibt es ein **offline-validierbares** Lizenzformat — **ohne Lizenz-Server**.

## Editionen

| Edition | Repo / Default | Lizenz erforderlich |
|---------|----------------|---------------------|
| **Open Source / Portfolio** | Öffentliches GitHub-Repo, `SEITON_LICENSE_REQUIRED=false` | Nein (MIT) |
| **Consumer (kommerziell)** | Distribution mit Enforcement | Ja (`SEITON_LICENSE_REQUIRED=true`) |

Was im Kauf enthalten ist (Consumer-Edition, Stand Planung):

- Web-UI (Dashboard, Notizen, Suche, Ask, Settings)
- Telegram-Eingang (optional)
- Self-Hosting via Docker (Consumer- oder VPS-Modus)
- Updates per `scripts/update.sh` (kein Abo-Zwang; Update-Politik beim Verkauf festlegen)
- BYO-Key für OpenAI/Ollama — keine Kosten durch uns

**Nicht** im Scope der Consumer-Edition (ADR 0004/0005):

- Gehosteter Betrieb durch uns
- Custom-n8n-Node (REST-API + Beispiele reichen)
- Verkaufs-/Payment-Shop (Story **E21-2**, später)

## Lizenzschlüssel-Format

```
SEITON1.<payload_base64url>.<signature_base64url>
```

- **Signatur:** Ed25519 über den Payload-Teil (ASCII, vor dem zweiten Punkt)
- **Payload (JSON):** `edition`, `licensee`, `issued`, optional `expires`, `features[]`
- **Prüfung:** komplett offline mit eingebettetem Public Key (`app/licensing/public_key.pem`)

Beispiel-Features: `ui`, `updates`, `telegram`.

## Konfiguration

In `.env` (oder über **Einstellungen → Lizenz**):

```env
SEITON_LICENSE_KEY=SEITON1.…
SEITON_LICENSE_REQUIRED=false   # true nur in kommerzieller Distribution
```

- `SEITON_LICENSE_REQUIRED=false` (Default im öffentlichen Repo): Start auch ohne Key
- `SEITON_LICENSE_REQUIRED=true`: API und Worker beenden sich ohne gültige Lizenz

Nach Änderung an der `.env` Container/Prozess neu starten.

## Lizenz ausstellen (Betreiber)

Nur für den Lizenzgeber — **Private Key nie ins Repository**:

```bash
# Einmalig Schlüsselpaar (Private Key landet in keys/, gitignored)
python scripts/issue-license.py --generate-keys

# Lizenz für Käufer
python scripts/issue-license.py --licensee user@example.com --edition consumer
# Optional: --expires 2027-12-31
```

Der Private Key liegt standardmäßig unter `keys/license-signing.pem`.
Der Public Key wird ins Repo committed (`app/licensing/public_key.pem`).

## Verkauf (E21-2 — später)

Story **E21-2** (Eigenshop/Store + automatische Lizenz-Ausgabe) ist bewusst
**nicht** Teil von E21-1. Bis dahin: manuelle Ausstellung mit `issue-license.py`
nach Zahlung.

## Referenzen

- [ADR 0004 — Kommerzielles Produkt](./adr/0004-commercial-consumer-product.md)
- [ADR 0005 — Repo- & Lizenzstrategie](./adr/0005-repo-and-license-strategy.md)
- Modul: `app/licensing/`
