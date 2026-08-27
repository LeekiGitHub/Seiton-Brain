# Release-Prozess (E29-3)

Leichter Ablauf für SemVer-Releases (Keep a Changelog). Ziel: nachvollziehbare
Stände für Support, Self-Hoster und Dependabot — ohne schweren Release-Train.

## Wann releasen?

- Nach einem abgeschlossenen Feature-Block (z. B. Phase-L-Kern) oder bei
  sicherheitsrelevanten Fixes.
- Nicht für jeden einzelnen PR — `[Unreleased]` sammelt Änderungen bis zum Cut.

## Checkliste

1. **`main` ist grün** — CI (`lint-and-test`, `docker-build`,
   `migrate-and-vector-smoke`) auf dem Merge-Commit.
2. **CHANGELOG schneiden**
   - Inhalt unter `## [Unreleased]` nach `## [X.Y.Z] — YYYY-MM-DD` verschieben.
   - Oben wieder eine leere `## [Unreleased]`-Sektion anlegen.
   - Footer-Links aktualisieren (`[Unreleased]` → compare `vX.Y.Z...HEAD`,
     neuer `[X.Y.Z]`-Compare zum Vorgänger-Tag).
3. **PR mergen** mit dem CHANGELOG-Schnitt (und ggf. Doku-Anpassungen).
4. **Git-Tag** (annotated) auf dem Merge-Commit auf `main`:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z -m "Seiton Brain vX.Y.Z"
   git push origin vX.Y.Z
   ```

5. **GitHub Release** aus dem Tag (Notes = CHANGELOG-Abschnitt):

   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file - <<'EOF'
   Siehe CHANGELOG.md Abschnitt [X.Y.Z].
   EOF
   ```

   Oder interaktiv: GitHub → Releases → „Draft a new release“ → Tag wählen,
   CHANGELOG-Abschnitt einfügen.

6. Optional: README-/Statuszeile (`v0.x.x`) anheben, wenn sie Versionen nennt
   (größere Doku-Sync: Story E29-5).

## Hinweise

- **Keine Tags auf Feature-Branches** — immer auf `main` nach Merge.
- Historische Tags `v0.1.0` / `v0.2.0` können fehlen; Compare-Links im
  CHANGELOG bleiben trotzdem als Zielbild stehen. Ab `v0.3.0` werden Tags
  gepflegt.
- Docker-Images werden derzeit nicht separat versioniert gepusht (Self-Host
  baut lokal/`docker compose build`). Tag = Quellcode-Stand.
