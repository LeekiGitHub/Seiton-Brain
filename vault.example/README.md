# Example Vault

This folder is a **template only** — it shows the default folder structure
Seiton Brain expects. Your real vault stays local and is never committed.

## Setup

1. Copy this folder to your preferred location:

   ```bash
   cp -r vault.example ~/Obsidian/Seiton-Brain
   ```

2. Point `OBSIDIAN_VAULT_PATH` in your `.env` at that copy (not at `vault.example/`).

3. Open the folder in Obsidian and adjust categories to fit your life.

## Folder structure

| Folder    | Purpose                                      |
|-----------|----------------------------------------------|
| `School/` | Lectures, exams, study notes                 |
| `Work/`   | Projects, meetings, professional tasks       |
| `Private/`| Personal thoughts, goals, everyday life      |
| `Ideas/`  | Ideas and concepts (any area)                |
| `Travel/` | Trips, destinations, packing lists           |
| `Notes/`  | Everything that does not fit elsewhere       |

Each note uses frontmatter and `[[wikilinks]]` so Seiton Brain can classify
and link new input automatically.
