# Integrationen & Ökosystem

Langfristige Integrations-Ideen für Seiton Brain — **Backlog / Vision**, nicht
alles sofort umsetzen. Architektur-Grundlage: [ADR 0003 — Engine + Adapter](../adr/0003-engine-and-adapters.md).

| Dokument | Inhalt |
|----------|--------|
| [n8n.md](./n8n.md) | n8n-Anbindung: HTTP zuerst, Custom Node später, Beispiel-Szenarien |
| [setup-onboarding.md](./setup-onboarding.md) | Easy Setup, TUI/CLI, API-Key-Handling, `seiton doctor` |
| [vault-backends.md](./vault-backends.md) | Obsidian-Alternative, `VaultBackend`-Interface, Backends |

**Phasen-Reihenfolge:** Erst Phase B (Append, Tags) → Phase C (REST-API,
Self-Hosting) → Phase D (Public v1.0, Setup-CLI) → Phase E (n8n-Ökosystem,
zweites Vault-Backend).

Details und User Stories: [`ROADMAP.md`](../../ROADMAP.md) — Phase E, Epics E13–E17.
