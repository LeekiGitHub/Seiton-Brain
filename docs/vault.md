# Vault — Obsidian optional (E15-2)

Seiton Brain speichert Notizen als **Markdown-Dateien** in einem Ordner auf
deiner Festplatte. **Obsidian ist optional** — du brauchst keine Obsidian-Lizenz
und keine Obsidian-Installation.

> Technisch: Der Vault ist ein normaler Ordner mit `.md`-Dateien. Obsidian ist
> nur ein beliebter Editor dafür.

---

## Was du brauchst

| Pflicht | Optional |
|---------|----------|
| Ein **beschreibbarer Ordner** auf dem Host (z. B. `./vault` oder `~/Notes/Seiton`) | [Obsidian](https://obsidian.md) zum Lesen/Bearbeiten |
| Pfad in `.env`: `OBSIDIAN_VAULT_HOST_PATH` (Host) / `OBSIDIAN_VAULT_PATH=/vault` (Docker) | Anderer Markdown-Editor (VS Code, Zettlr, Logseq, …) |
| | Sync (Syncthing, iCloud, Git) |

Die Web-UI unter http://localhost:8000/notes kann Notizen **ohne Obsidian**
anzeigen und bearbeiten (E19-4).

---

## Schnellstart ohne Obsidian

### Consumer-Installer

```bash
./scripts/install.sh
```

Legt `./vault` an und kopiert bei Bedarf `vault.example/` hinein.

### Manuell

```bash
mkdir -p ~/SeitonBrain/vault/{School,Work,Private,Ideas,Travel,Notes}
```

In `.env`:

```env
OBSIDIAN_VAULT_HOST_PATH=/Users/du/SeitonBrain/vault
OBSIDIAN_VAULT_PATH=/vault
```

Oder aus der Vorlage:

```bash
cp -r vault.example ~/SeitonBrain/vault
```

> **`vault.example/`** im Repo ist nur eine **Vorlage** — nie direkt als
> produktiven Vault mounten (würde ins Git-Working-Tree schreiben).

---

## Ordnerstruktur

Seiton legt neue Notizen nach **Kategorie** in feste Unterordner:

| Kategorie (LLM) | Ordner | Beispiel |
|-----------------|--------|----------|
| `school` | `School/` | Prüfungsvorbereitung |
| `work` | `Work/` | Meeting-Notizen |
| `private` | `Private/` | Persönliches |
| `idea` | `Ideas/` | Projektideen |
| `travel` | `Travel/` | Reiseplanung |
| `note` (Default) | `Notes/` | Alles andere |

Mapping im Code: `app/vault/writer.py` → `CATEGORY_FOLDERS`. In der
Settings-UI siehst du die Zuordnung.

Beispielnotizen: [`vault.example/`](../vault.example/).

---

## Dateiformat

Jede Notiz ist eine `.md`-Datei mit optionalem YAML-Frontmatter:

```markdown
---
title: Meine Idee
category: idea
tags: [side-project, api]
created: 2026-07-13
---

# Meine Idee

Kurze Zusammenfassung …

Verwandt: [[Andere Notiz]]
```

- **`[[Wiki-Links]]`** werden vom LLM gesetzt und von Obsidian/Logseq erkannt
- **Append** fügt einen `## Update YYYY-MM-DD`-Block an bestehende Dateien an
- Schreiben ist **atomar** (Tempfile + Rename) — sicher bei laufendem Sync

Unterstützte **Leseformate** für den Index (nicht für neue Captures): `.md`,
`.txt`, `.pdf`, `.docx`, `.pptx` (Epic E18).

---

## Obsidian nutzen (optional)

Wenn du Obsidian bereits hast:

1. Vault-Ordner in Obsidian als Vault öffnen („Open folder as vault“)
2. Graph, Daily Notes, Plugins — alles optional
3. Seiton schreibt Dateien; Obsidian zeigt sie nach Sync/Reload

**Tipp:** Gleichen Ordner in `.env` und in Obsidian verwenden — kein
zusätzlicher Export nötig.

---

## Andere Editoren & Sync

| Tool | Rolle |
|------|--------|
| **VS Code / Cursor** | Markdown direkt im Vault-Ordner bearbeiten |
| **Logseq** | Wiki-Links, Outliner — gleicher Ordner möglich |
| **Syncthing / iCloud** | Vault zwischen Geräten syncen |
| **Git** | Versionshistorie (manuell; Git-Backend E15-3 ist Backlog) |
| **Web-UI `/notes`** | Suchen, öffnen, speichern, löschen — localhost only |

Seiton **ersetzt** keine Notiz-App — es **befüllt** deinen Ordner strukturiert.

---

## Docker & Pfade

| Umgebung | Variable | Beispiel |
|----------|----------|----------|
| Host (dein Rechner) | `OBSIDIAN_VAULT_HOST_PATH` | `/Users/du/vault` |
| Im Container | `OBSIDIAN_VAULT_PATH` | `/vault` (Standard) |

Compose mountet: `${OBSIDIAN_VAULT_HOST_PATH}:/vault`

Container-User ist **UID 1000** — der Host-Ordner muss beschreibbar sein
(siehe [`troubleshooting.md`](troubleshooting.md)).

---

## Backups

```bash
./scripts/backup.sh
```

Sichert Postgres **und** den Vault-Ordner nach `backups/`. Details:
[`setup.md` — Backups](setup.md#backups-lokal).

---

## Für Entwickler

Langfristig: `VaultBackend`-Interface und weitere Backends (Git, S3) —
[`docs/integrations/vault-backends.md`](integrations/vault-backends.md) (E15-1).

---

## Referenzen

- Template: [`vault.example/README.md`](../vault.example/README.md)
- Setup: [`setup.md`](setup.md)
- Self-Hosting: [`self-hosting.md`](self-hosting.md)
- Troubleshooting (Vault-Rechte): [`troubleshooting.md`](troubleshooting.md)
