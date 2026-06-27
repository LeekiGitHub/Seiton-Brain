# Seiton Brain MCP (E17-6)

MCP-Server, der die [Seiton-Brain REST-API](../../docs/integrations/knowledge-retrieval.md)
als **Tools** fuer LLM-Clients exponiert (Cursor, Claude Desktop, VS Code Continue, …).

Kein zweites Backend — nur ein duenner stdio-Wrapper um `GET /v1/notes/search`,
`POST /v1/ask` und Lese-Endpunkte.

## Voraussetzungen

1. Seiton Brain laeuft (`docker compose up -d`), Migrationen applied
2. In `.env` gesetzt: `SEITON_API_KEY` (REST-API aktiv)
3. Python 3.10+

```bash
pip install -r requirements.txt
```

## Tools

| MCP-Tool | REST | Beschreibung |
|----------|------|--------------|
| `search_notes` | `GET /v1/notes/search` | Keyword- oder semantische Trefferliste |
| `ask_brain` | `POST /v1/ask` | RAG-Antwort mit Quellen |
| `get_note` | `GET /v1/entries/{id}` oder `GET /v1/notes/content` | Volle Notiz nachladen |

Auth: `SEITON_API_KEY` im MCP-Prozess-Env (Header `X-Seiton-Api-Key`).

## Cursor konfigurieren

**Settings → MCP → Add server** (oder `.cursor/mcp.json` im Projekt):

```json
{
  "mcpServers": {
    "seiton-brain": {
      "command": "python",
      "args": ["/ABSOLUTER/PFAD/zu/Seiton-Brain/examples/mcp/seiton-brain-mcp/server.py"],
      "env": {
        "SEITON_API_URL": "http://localhost:8000",
        "SEITON_API_KEY": "dein-seiton-api-key"
      }
    }
  }
}
```

`python` durch den Pfad zu deinem venv ersetzen, wenn `mcp` dort installiert ist.

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "seiton-brain": {
      "command": "python",
      "args": ["/ABSOLUTER/PFAD/zu/Seiton-Brain/examples/mcp/seiton-brain-mcp/server.py"],
      "env": {
        "SEITON_API_URL": "http://localhost:8000",
        "SEITON_API_KEY": "dein-seiton-api-key"
      }
    }
  }
}
```

Nach Aenderung Cursor/Claude neu starten.

## Manuell testen

```bash
export SEITON_API_KEY=...
export SEITON_API_URL=http://localhost:8000
python server.py
# stdio — normalerweise startet das der MCP-Client, nicht du interaktiv
```

Client-Logik separat testen: `pytest tests/` in diesem Ordner.

## Architektur

```
Cursor / Claude  --stdio-->  server.py (MCP)
                                |
                                v  httpx
                         Seiton REST /v1/*
                                |
                                v
                         Engine (RAG, Vault, DB)
```

Details: [`docs/integrations/knowledge-retrieval.md`](../../docs/integrations/knowledge-retrieval.md)
