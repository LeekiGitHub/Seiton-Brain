# Integrationen & Ökosystem

Langfristige Integrations-Ideen für Seiton Brain — **Backlog / Vision**, nicht
alles sofort umsetzen. Architektur-Grundlage: [ADR 0003 — Engine + Adapter](../adr/0003-engine-and-adapters.md).

| Dokument | Inhalt |
|----------|--------|
| [n8n.md](./n8n.md) | n8n-Anbindung: HTTP zuerst, Custom Node später, Beispiel-Szenarien |
| [`examples/n8n/`](../../examples/n8n/README.md) | Importierbare Workflow-JSONs (Capture, Webhooks, Todoist) |
| [setup-onboarding.md](./setup-onboarding.md) | Easy Setup, TUI/CLI, API-Key-Handling, `seiton doctor` |
| [vault-backends.md](./vault-backends.md) | Obsidian-Alternative, `VaultBackend`-Interface, Backends |
| [knowledge-retrieval.md](./knowledge-retrieval.md) | Brain als Wissensquelle: Suche, RAG-Q&A, Retrieval-API, MCP-Server |

**Phasen-Reihenfolge:** Erst Phase B (Append, Tags) → Phase C (REST-API,
Self-Hosting) → Phase D (Public v1.0, Setup-CLI) → Phase E (n8n-Ökosystem,
zweites Vault-Backend) → Phase F (Brain als Wissensquelle: Retrieval, RAG,
MCP-Server).

Details und User Stories: [`ROADMAP.md`](../../ROADMAP.md) — Phase E/F, Epics E13–E17.
