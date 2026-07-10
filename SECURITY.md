# Sicherheit

Seiton Brain ist **self-hosted**: Deine Daten, Keys und der Vault bleiben auf
deiner Hardware. Es gibt keinen zentralen Seiton-Cloud-Dienst und keine
Telemetrie.

Diese Datei beschreibt, wie du Sicherheitslücken meldest und welche
Bedrohungen das Projekt berücksichtigt.

---

## Unterstützte Versionen

| Version | Unterstützt |
|---------|-------------|
| `main` (aktuell) | ✅ |
| Ältere Tags | nur bei aktiver Nutzung — bitte auf `main` oder neuesten Tag updaten |

Sicherheitsfixes landen auf `main` und werden im [`CHANGELOG.md`](CHANGELOG.md)
unter `[Unreleased]` bzw. in Release-Tags dokumentiert.

---

## Schwachstellen melden

**Bitte melde Sicherheitsprobleme nicht als öffentliches GitHub-Issue.**

1. **Bevorzugt:** [GitHub Security Advisory](https://github.com/LeekiGitHub/Seiton-Brain/security/advisories/new) (Private Meldung)
2. **Alternativ:** Maintainer per GitHub kontaktieren (Profil-Link im Repo)

Bitte gib an:

- betroffene Version / Commit
- Schritte zur Reproduktion
- Auswirkung (z. B. Datenabfluss, RCE, Auth-Bypass)
- ggf. Proof-of-Concept (vertraulich)

**Ziel:** Erste Rückmeldung innerhalb von **7 Tagen**. Fix-Zeitplan hängt von
Schweregrad und Komplexität ab — wir stimmen das mit dir ab.

Öffentliche Anerkennung (Credit) nur mit deiner Zustimmung.

---

## Threat Model (Kurz)

### Was wir schützen wollen

| Asset | Beschreibung |
|-------|--------------|
| **Vault-Inhalt** | Persönliche Markdown-Notizen auf Disk |
| **DB** | Metadaten, Rohtexte, Embeddings (Postgres) |
| **Secrets** | `.env`: API-Keys, Bot-Token, Webhook-Secret, Lizenzschlüssel |
| **Telegram-Kanal** | Nur autorisierte Nutzer sollen Nachrichten senden können |

### Vertrauensgrenzen

```
[Telegram] ──HTTPS──► [dein Host: API/Worker]
[Browser localhost] ──► [Setup / Settings / OpenAPI]
[REST-Client] ──API-Key──► [/v1/*]
[OpenAI] ◄──HTTPS── [Worker]  (Klassifikation, Whisper, Embeddings)
```

- **Du** betreibst Docker, Netzwerk, Backups und Reverse-Proxy (VPS).
- **OpenAI** (oder später Ollama) sieht Prompt-Inhalte — BYO-Key, Daten fließen
  dorthin nur bei aktivierter Nutzung.
- **Kein** Seiton-Server für Betrieb oder Lizenzprüfung (offline Ed25519, E21).

### Implementierte Schutzmaßnahmen

| Bereich | Maßnahme |
|---------|----------|
| Telegram-Webhook | Header `X-Telegram-Bot-Api-Secret-Token` muss passen |
| Telegram-Zugriff | Optionale Allowlist (`TELEGRAM_ALLOWED_USER_IDS`) |
| Webhook-Body | Größenlimit (`TELEGRAM_WEBHOOK_MAX_BODY_BYTES`) |
| REST-API `/v1/*` | Deaktiviert ohne `SEITON_API_KEY`; Header `X-Seiton-Api-Key` (timing-safe) |
| Web-UI `/setup`, `/settings`, … | Nur **localhost** |
| OpenAPI `/docs` | Nur bei gesetztem API-Key oder `SEITON_DEBUG`; nur **localhost** |
| Vault-Pfade | Path-Traversal-Schutz (`resolve_vault_file`) |
| Vault-Schreiben | Atomare Writes (Tempfile + `os.replace`) |
| Docker | Non-root User im Image (E9-1) |
| VPS | API bindet auf `127.0.0.1:8000` — TLS via Reverse-Proxy |
| Secrets in Logs | Keys werden nicht geloggt; UI maskiert gespeicherte Werte |
| Idempotenz | Telegram-`update_id` verhindert Doppelverarbeitung |

### Bekannte Grenzen / nicht im Scope

- **Self-hosted = deine Verantwortung:** Firewall, SSH-Härtung, Backups,
  `.env`-Dateirechte, Docker-Socket-Zugriff.
- **Öffentliches MIT-Repo:** Code ist einsehbar; kommerzielle Distribution
  kann zusätzliche Härtung mitbringen (ADR 0005).
- **LLM-Prompt-Injection:** Klassifikation/RAG können von bösartigem Input in
  Nachrichten beeinflusst werden — kein vollständiger Sandbox-Schutz.
- **Outbound-Webhooks:** URL in `.env` — nur vertrauenswürdige Ziele eintragen.
- **MCP/n8n-Beispiele:** Externe Integrationen nutzen deinen API-Key lokal.

Ausführlichere Architektur-Entscheidungen: [`docs/adr/`](docs/adr/).

---

## Empfehlungen für Betreiber

1. **`.env` schützen** — `chmod 600`, nicht committen, nicht in Backups unverschlüsselt teilen.
2. **Telegram-Allowlist setzen**, wenn der Webhook öffentlich erreichbar ist.
3. **`SEITON_API_KEY`** lang und zufällig; API nur aktivieren, wenn nötig.
4. **VPS:** API nicht direkt auf `0.0.0.0` exposen; Reverse-Proxy mit TLS;
   nur `/webhook` (und ggf. nichts anderes) nach außen.
5. **Updates:** `./scripts/update.sh` für Patches.
6. **Backups:** `./scripts/backup.sh` — Vault + DB enthalten persönliche Daten.

Consumer-Setup: [`docs/self-hosting.md`](docs/self-hosting.md) ·
VPS: [`docs/vps-deployment.md`](docs/vps-deployment.md)

---

## Security-related Dependencies

Wir nutzen `pip`/`requirements.txt` mit gepinnten Versionen wo sinnvoll.
Bei bekannten CVEs in Dependencies: Issue oder Advisory wie oben melden.
