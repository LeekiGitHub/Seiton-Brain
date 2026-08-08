# Vault Backends (Obsidian & Alternativen)

Obsidian ist für Seiton Brain im Kern **ein Markdown-Ordner mit Wiki-Links**.
Eine „Obsidian-Alternative“ bedeutet nicht zwingend eine eigene Notiz-App.

> **Heute (E15-1):** `VaultBackend`-Protocol + `FilesystemVaultBackend`
> (`app/vault/backend.py`, `app/vault/filesystem.py`). Aufrufer über
> `get_vault_backend()` bzw. Kompatibilitäts-Wrapper in `writer.py`.

Siehe [ADR 0003](../adr/0003-engine-and-adapters.md).

---

## Interface

```python
from typing import Protocol
from app.llm.schemas import ClassificationResult

class VaultBackend(Protocol):
    def write_note(self, result: ClassificationResult) -> str:
        """Vault-relativer Pfad, z. B. Ideas/My Note.md"""
    def append_to_note(self, vault_path: str, result: ClassificationResult) -> str: ...
    def save_note_content(self, vault_path: str, content: str) -> str: ...
    def delete_note(self, vault_path: str) -> bool: ...
    def note_exists(self, vault_path: str) -> bool: ...
```

Config: `VAULT_BACKEND=filesystem` (Default; Aliase `fs`, `obsidian`) oder `VAULT_BACKEND=git` für Commit pro Note.

Service-Layer (`process_message.py`) spricht `get_vault_backend()`, nicht
direkt `Path`/`os`.

---

## Backend-Optionen

| Backend | Beschreibung | Aufwand | Phase | Story |
|---------|--------------|---------|-------|-------|
| **Filesystem Markdown** | Obsidian, Logseq, VS Code, jeder Editor | ✅ `FilesystemVaultBackend` | D | `E15-1` 🟢 |
| **Plain folder + Doku** | User-Doku „Obsidian optional“ | Minimal | D | `E15-2` 🟢 → [`vault.md`](../vault.md) |
| **Atomares Schreiben** | Tempfile + `os.replace` (Obsidian-Sync-sicher) | Gering | B | `E3-4` |
| **Git-backed vault** | Commit pro Note, optionaler Push auf Remote | ✅ `GitVaultBackend` | E | `E15-3` 🟢 |
| **S3 / Object Storage** | Vault in Bucket (Cloud-Self-Hoster) | Mittel | E | Backlog |
| **Read-only Web-UI** | Browser-Ansicht ohne Obsidian → **aufgegangen in UI-Epic** | Hoch | G | ➡️ `E19` |
| **Notion / Google Docs API** | Fremdes Ökosystem (API, Block-Modell statt Markdown-Dateien) | Hoch | H+ | `E15-5` ⚪ (Evaluation zuerst: Export/Sync vs. Backend) |

**Bewusst ausgeschlossen:** Vollwertige Obsidian-Ersatz-App (Editor, Graph, Plugins)
— wäre ein separates Produkt.

---

## Was „Obsidian optional“ für User bedeutet

Ausführlich: **[`docs/vault.md`](../vault.md)** (E15-2).

1. Vault = beliebiger Ordner mit Unterordnern (`School`, `Work`, `Ideas`, …)
2. Notizen = `.md` mit YAML-Frontmatter + optional `[[Wiki-Links]]`
3. Sync: Syncthing, iCloud, Git — unabhängig von Obsidian
4. Obsidian-Nutzer profitieren von Graph, Plugins, Daily Notes — optional

`vault.example/` im Repo bleibt Template für Selfhoster.

---

## Abhängigkeiten

- **E3-2 Append** nutzt `append_to_note(vault_path)` am Backend
- **E5-1 Vault-Index** spiegelt Relativpfade backend-agnostisch in Postgres
- REST-API `/v1/notes/*` und UI nutzen dieselben Writer-Wrapper / dasselbe Backend

---

## Offene Fragen

- Sync-Konflikte: Was passiert, wenn User manuell editiert während Append läuft?
- Push-Strategie: sofort pro Änderung oder nur periodisch? (heute: optional sofort)

## Git-Backend Config

```env
VAULT_BACKEND=git
VAULT_GIT_PUSH=false
VAULT_GIT_REMOTE=origin
VAULT_GIT_BRANCH=
VAULT_GIT_AUTHOR_NAME="Seiton Brain"
VAULT_GIT_AUTHOR_EMAIL="seiton@example.invalid"
```

- `VAULT_GIT_PUSH=false`: nur lokaler Commit pro Änderung
- `VAULT_GIT_PUSH=true`: nach jedem Commit zusätzlich `git push`
- `VAULT_GIT_BRANCH` leer: aktueller Branch; sonst `HEAD:<branch>` auf Remote
