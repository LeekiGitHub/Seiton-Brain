# Security

Seiton Brain is **self-hosted today**: your data, API keys, and vault stay on
your infrastructure. There is **no** Seiton-operated cloud service and no
telemetry. A **managed Seiton Cloud** is planned for the future
([ADR 0008](docs/adr/0008-deployment-models-self-hosted-first.md)); it would be
a separate deployment model with its own security and privacy posture and does
not change commitments for the self-hosted edition.

This document explains how to report vulnerabilities and what threats the project
considers.

---

## Supported versions

| Version | Supported |
|---------|-----------|
| `main` (current) | Yes |
| Older tags | Best-effort — prefer `main` or the latest tag |

Security fixes land on `main` and are noted in [CHANGELOG.md](CHANGELOG.md)
under `[Unreleased]` or in release tags.

---

## Reporting a vulnerability

**Please do not report security issues as public GitHub issues.**

1. **Preferred:** [GitHub Security Advisory](https://github.com/LeekiGitHub/Seiton-Brain/security/advisories/new) (private report)
2. **Alternative:** contact the maintainer via GitHub (profile linked from the repo)

Include:

- affected version / commit
- steps to reproduce
- impact (e.g. data exposure, RCE, auth bypass)
- proof-of-concept if available (keep it confidential)

**Goal:** first response within **7 days**. Fix timeline depends on severity;
we will coordinate with you.

Public credit only with your consent.

---

## Threat model (summary)

### Assets

| Asset | Description |
|-------|-------------|
| **Vault** | Personal Markdown notes on disk |
| **Database** | Metadata, raw text, embeddings (PostgreSQL) |
| **Secrets** | `.env`: API keys, bot token, webhook secret, license key |
| **Telegram channel** | Only authorized users should send messages |

### Trust boundaries

```
[Telegram] ──HTTPS──► [your host: API/worker]
[Browser localhost] ──► [setup / settings / OpenAPI]
[REST client] ──API key──► [/v1/*]
[OpenAI / Ollama] ◄──HTTPS── [worker]  (classification, Whisper, embeddings)
```

- **You** operate Docker, network, backups, and reverse proxy (VPS).
- **LLM providers** see prompt content when enabled — BYO key; data flows only
  when you use those features.
- **No** Seiton server for operation or license checks (offline Ed25519, E21).

### Implemented controls

| Area | Measure |
|------|---------|
| Telegram webhook | `X-Telegram-Bot-Api-Secret-Token` required |
| Telegram access | Optional allowlist (`TELEGRAM_ALLOWED_USER_IDS`) |
| Webhook body | Size limit (`TELEGRAM_WEBHOOK_MAX_BODY_BYTES`) |
| REST `/v1/*` | Disabled without `SEITON_API_KEY`; timing-safe header check |
| Web UI | Localhost by default; optional `UI_PASSWORD` (session cookie, HMAC, lockout); `/setup` stays localhost-only |
| Localhost guard | Proxy-aware, fail-closed (E27-1) |
| OpenAPI `/docs` | API key or `SEITON_DEBUG`; localhost only |
| Vault paths | Path traversal protection (`resolve_vault_file`) |
| Vault writes | Atomic writes (temp file + `os.replace`) |
| Docker image | Non-root user (E9-1) |
| VPS | API binds `127.0.0.1:8000` — TLS via reverse proxy or tunnel |
| Logging | Secrets not logged; UI masks stored values |
| Idempotency | Telegram `update_id` deduplication |

### Known limits

- **Self-hosted = your responsibility:** firewall, SSH hardening, backups,
  `.env` permissions, Docker socket access.
- **Public MIT repository:** source is visible; commercial distribution may add
  hardening ([ADR 0005](docs/adr/0005-repo-and-license-strategy.md)).
- **LLM prompt injection:** classification/RAG can be influenced by malicious
  user content — not a full sandbox.
- **Outbound webhooks:** only configure trusted URLs in `.env`.
- **MCP / n8n examples:** use your API key locally.

More architecture decisions: [docs/adr/](docs/adr/).

---

## Recommendations for operators

1. **Protect `.env`** — `chmod 600`, never commit; avoid sharing unencrypted backups.
   Optional OS keyring: [docs/keyring.md](docs/keyring.md).
2. **Set Telegram allowlist** if the webhook is reachable from the internet.
3. **Use a strong `SEITON_API_KEY`**; enable the REST API only when needed.
4. **VPS:** do not expose the API on `0.0.0.0` without TLS; protect setup/OpenAPI
   ([docs/remote-access.md](docs/remote-access.md)).
5. **Updates:** `./scripts/update.sh` for patches.
6. **Backups:** `./scripts/backup.sh` — vault and DB contain personal data.

Guides: [Self-hosting](docs/self-hosting.md) · [VPS](docs/vps-deployment.md) ·
[Remote access](docs/remote-access.md)

---

## Dependencies

Pinned versions in `requirements.txt`; CI runs `pip-audit`. Report vulnerable
dependencies via the advisory process above.

---

## Repository security features (maintainer)

As of 2026-08-30: Dependabot alerts/updates, secret scanning + push protection,
CodeQL, branch protection on `main` — see [docs/engineering.md](docs/engineering.md).
