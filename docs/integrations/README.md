# Integrationen & Ökosystem

Langfristige Integrations-Ideen für Seiton Brain — **Backlog / Vision**, nicht
alles sofort umsetzen. Architektur-Grundlage: [ADR 0003 — Engine + Adapter](../adr/0003-engine-and-adapters.md)
und [ADR 0004 — Kommerzielles Produkt](../adr/0004-commercial-consumer-product.md).

> ⚠️ **Produkt-Pivot (ADR 0004):** Seiton wird ein kommerzielles, self-hosted
> Consumer-Produkt (buy-once, BYO-Key). Schwerpunkt: **UI** (E19), **Packaging**
> (E20), **Lizenzierung** (E21). **Repo bleibt vorerst public** fürs Portfolio —
> siehe [ADR 0005](../adr/0005-repo-and-license-strategy.md). n8n-Custom-Node
> entfällt; REST-API + Beispiel-Workflows bleiben für Power-User.

| Dokument | Inhalt |
|----------|--------|
| [n8n.md](./n8n.md) | n8n per REST + Webhooks (kein Custom Node, ADR 0004) |
| [`examples/n8n/`](../../examples/n8n/README.md) | Importierbare Workflow-JSONs für Power-User |
| [`examples/mcp/`](../../examples/mcp/README.md) | MCP-Server für Cursor/Claude (`search_notes`, `ask_brain`, `get_note`) |
| [setup-onboarding.md](./setup-onboarding.md) | Easy Setup, TUI/CLI, API-Key-Handling, `seiton doctor` |
| [vault-backends.md](./vault-backends.md) | Obsidian-Alternative, `VaultBackend`-Interface, Backends |
| [knowledge-retrieval.md](./knowledge-retrieval.md) | Brain als Wissensquelle: Suche, RAG-Q&A, Retrieval-API, MCP-Server |

**Phasen-Reihenfolge:** Erst Phase B (Append, Tags) → Phase C (REST-API,
Self-Hosting) → Phase D (Public v1.0, Setup-CLI) → Phase E (n8n-Ökosystem,
zweites Vault-Backend) → Phase F (Brain als Wissensquelle: Retrieval, RAG,
MCP-Server).

Details und User Stories: [`ROADMAP.md`](../../ROADMAP.md) — Phase E/F, Epics E13–E17.
