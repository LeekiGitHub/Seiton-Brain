# Notiz-Templates (E26)

Du bestimmst selbst, **wie** Seiton neue Notizen im Vault ablegt.

## Schnellstart

Lege im Vault die Datei **`_seiton/templates/note.md`** an (der Ordner
`_seiton/` ist reserviert und wird nicht als Notiz indexiert), z. B.:

```markdown
## {{title}}

> {{date}} · {{category}} · {{tags}}

{{summary}}{{related}}
```

Ab der nächsten erfassten Notiz wird der **Body** nach dieser Vorlage
gerendert. Keine Datei = bisheriges Default-Layout.

## Platzhalter

| Platzhalter | Wert |
|-------------|------|
| `{{title}}` | Titel der Notiz |
| `{{summary}}` | Aufbereiteter Inhalt (**Pflicht** im Template) |
| `{{tags}}` | Tags als `#tag1 #tag2` (leer, wenn keine) |
| `{{date}}` | Erstelldatum `YYYY-MM-DD` |
| `{{category}}` | Kategorie (idea, task, note, …) |
| `{{related}}` | Kompletter `## Related`-Abschnitt mit `[[Links]]`, beginnt mit einer Leerzeile; leer ohne Verweise — am besten direkt hinter `{{summary}}` platzieren |

## Leitplanken

- Das Template steuert **nur den Body**. Der YAML-Frontmatter (title,
  category, created, tags) bleibt fix — darauf bauen Append-Logik, Suche
  und Index auf.
- **Kaputte Templates brechen nichts:** unbekannte Platzhalter, eigenes
  Frontmatter (`---` am Anfang) oder fehlendes `{{summary}}` → Seiton
  rendert mit dem Default-Layout und schreibt eine Warnung ins Log. Den
  Status siehst du in **Settings → Kategorien/Vault** (`default` /
  `custom` / `invalid`).
- **Appends** an bestehende Notizen (`## Update`-Blöcke) behalten ihr
  festes Format — das Template gilt für neue Notizen.

## Geplant (siehe ROADMAP E26)

KI-Felder (`{{ai:…}}`, E26-3), Template-Editor mit Vorschau in der
Settings-UI (E26-4), visueller Builder (E26-5), Template pro Kategorie
(E26-6).
