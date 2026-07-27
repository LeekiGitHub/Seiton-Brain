# Document Chunking (E18-4)

Lange Vault-Dateien (PDF, Office, große Markdown-Notizen) werden beim Indexieren
in überlappende Textabschnitte zerlegt und in `vault_chunk` gespeichert.

## Warum

`vault_note_index.body_snippet` bleibt auf ~2000 Zeichen begrenzt (UI-Preview).
Ohne Chunks wären Keyword- und semantische Suche hinter diesem Limit blind.

## Schema

- **Parent:** `vault_note_index` — eine Zeile pro Datei (Metadaten, UI-Liste)
- **Child:** `vault_chunk` — N Zeilen pro Datei (`note_id`, `chunk_index`,
  `content`, optional `embedding`), `ON DELETE CASCADE`

## Config

```env
SEITON_CHUNK_SIZE=1500
SEITON_CHUNK_OVERLAP=200
```

## Verhalten

1. Extractor liefert vollen Text → `chunk_text()` → Chunks ersetzen
2. Bei `EMBEDDINGS_ENABLED=true`: Embedding **pro Chunk** (Titel + Chunk)
3. Semantische Suche: kNN auf Chunks, Deduplizierung nach `vault_path`
4. Keyword-Suche: Titel zuerst, dann Body/Chunk-Inhalt

Nach dem Upgrade (`alembic upgrade head`) einmal Vault-Sync / Index-Refresh,
damit Bestandsdateien Chunks bekommen.
