# ADR 0002: `.gitignore`-Pattern für `vault` und `models` mit führendem Slash

- **Status:** Accepted
- **Datum:** 2026-05-23
- **Entscheider:** Yannik
- **Phase / Epic:** Phase A · epic:infra

## Kontext

Die `.gitignore` enthielt initial:

```
vault/
models/
```

Das hat **zwei** Verzeichnisse stillschweigend mitignoriert, die im Repo bleiben müssen:

- `app/vault/` — Reader/Writer-Modul
- `app/models/` — SQLAlchemy-Modelle

`git status` zeigte „nothing to commit", obwohl Code existierte. Build im CI lief, lokal nicht klar reproduzierbar.

Hintergrund: `.gitignore`-Patterns ohne führenden Slash matchen **überall** im Repo, nicht nur im Root.

## Entscheidung

Patterns mit führendem Slash auf das Root einschränken:

```
/vault/
/models/
```

Damit:
- `/vault/` ignoriert nur den Bind-Mount-Vault im Repo-Root (echter Obsidian-Vault auf dem Host)
- `/models/` ignoriert nur den AI-Model-Cache im Root (z.B. lokale Whisper-Modelle), nicht das Python-Package `app/models/`

## Konsequenzen

### Positiv
- `app/vault/` und `app/models/` sind versioniert
- Klare Semantik: führender Slash = Root-Anker

### Negativ / Trade-offs
- Beim Hinzufügen ähnlicher Patterns immer dran denken (z.B. `prompts/` würde `app/prompts/` mitnehmen, falls je benötigt)

### Folgearbeiten
- Konvention dokumentiert in `ARCHITECTURE.md` (Conventions-Sektion)

## Alternativen, die wir nicht gewählt haben

| Alternative | Warum nicht? |
|-------------|--------------|
| `!app/vault/` und `!app/models/` als Whitelist | Weniger explizit, abhängig von Reihenfolge der Regeln |
| Verzeichnisse umbenennen (z.B. `app/orm/` statt `app/models/`) | Würde Refactoring-Aufwand erzeugen, ohne Mehrwert |

## Referenzen

- `.gitignore` (Sektionen „Obsidian vault" und „AI / transcription")
