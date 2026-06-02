# Vault Backends (Obsidian & Alternativen)

Obsidian ist für Seiton Brain im Kern **ein Markdown-Ordner mit Wiki-Links**.
Eine „Obsidian-Alternative“ bedeutet nicht zwingend eine eigene Notiz-App.

> **Heute:** Filesystem-Markdown unter `OBSIDIAN_VAULT_PATH` (`app/vault/reader.py`,
> `app/vault/writer.py`).  
> **Langfristig:** `VaultBackend`-Interface, Obsidian-kompatibles FS als erste
> Implementierung.

Siehe [ADR 0003](../adr/0003-engine-and-adapters.md).

---

## Geplantes Interface (Entwurf)

```python
# Konzept — noch nicht implementiert
class VaultBackend(Protocol):
    async def list_notes(self, limit: int = 80) -> list[VaultNote]: ...
    async def write_note(self, result: ClassificationResult) -> str:
        """Returns vault-relative path, e.g. Ideas/My Note.md"""
    async def append_to_note(self, vault_path: str, content: str) -> None: ...
    async def note_exists(self, vault_path: str) -> bool: ...
```

Service-Layer (`process_message.py`) spricht nur noch mit `VaultBackend`, nicht
direkt mit `Path`/`os`.

**Story:** `E15-1` — Interface extrahieren + Filesystem-Backend.

---

## Backend-Optionen

| Backend | Beschreibung | Aufwand | Phase | Story |
|---------|--------------|---------|-------|-------|
| **Filesystem Markdown** | Heutiges Verhalten; Obsidian, Logseq, VS Code, jeder Editor | ✅ existiert | — | — |
| **Plain folder + Doku** | README: „Obsidian optional“ | Minimal | D | `E15-2` |
| **Atomares Schreiben** | Tempfile + `os.replace` (Obsidian-Sync-sicher) | Gering | B | `E3-4` |
| **Git-backed vault** | Commit pro Note/Push (Backup + History) | Mittel | E | `E15-3` |
| **S3 / Object Storage** | Vault in Bucket (Cloud-Self-Hoster) | Mittel | E | Backlog |
| **Read-only Web-UI** | Browser-Ansicht ohne Obsidian | Hoch | E | `E15-4` |
| **Notion / Google Docs API** | Fremdes Ökosystem | Hoch | später | Backlog |

**Bewusst ausgeschlossen:** Vollwertige Obsidian-Ersatz-App (Editor, Graph, Plugins)
— wäre ein separates Produkt.

---

## Was „Obsidian optional“ für User bedeutet

1. Vault = beliebiger Ordner mit Unterordnern (`School`, `Work`, `Ideas`, …)
2. Notizen = `.md` mit YAML-Frontmatter + optional `[[Wiki-Links]]`
3. Sync: Syncthing, iCloud, Git — unabhängig von Obsidian
4. Obsidian-Nutzer profitieren von Graph, Plugins, Daily Notes — optional

`vault.example/` im Repo bleibt Template für Selfhoster.

---

## Abhängigkeiten

- **E3-2 Append** braucht `append_to_note(vault_path)` — guter Zeitpunkt für
  Interface-Extraktion (`E15-1` parallel oder direkt danach)
- **E5-1 Vault-Index** kann backend-agnostisch in Postgres spiegeln
- REST-API `/v1/notes/*` nutzt dasselbe Backend wie Telegram-Pipeline

---

## Offene Fragen

- Sync-Konflikte: Was passiert, wenn User manuell editiert während Append läuft?
- Git-Backend: ein Commit pro Capture vs. batch?
- Web-UI: nur Read oder auch Edit (Scope explodiert)?
