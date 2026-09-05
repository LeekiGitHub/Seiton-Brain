## Summary

<!-- What changes and why? Include ROADMAP ID when applicable (e.g. E47-1). -->

## Change type

<!-- Primary type (stricter column wins if mixed): docs | backend/api | ui | migration | security | chore -->

## Test plan

Gates by type: see [docs/engineering.md](../docs/engineering.md) (E45-14 DoD).

- [ ] Acceptance criteria met (ROADMAP story / this summary)
- [ ] `ruff check app tests`
- [ ] `pytest`
- [ ] New/updated tests (backend/UI/migration/security) — or N/A for docs/chore
- [ ] CI green (lint, pytest, docker build, migrate smoke as applicable)
- [ ] CHANGELOG updated under `[Unreleased]` (if user-visible or story complete)
- [ ] ROADMAP status updated (if completing a story)
- [ ] Visual smoke (`SEITON_VISUAL=1 pytest -m visual`) if UI shell/CSS/JS changed — or N/A
- [ ] CodeRabbit review completed (auto-triggered on code PRs; advisory only)
- [ ] ADR considered (architecture / schema / security) — or N/A

## Mini-Handcheck (~2 min)

<!-- Required for UI, security, migrations, and visible backend behavior.
     Skip for docs/chore-only — write "N/A". Agent: three concrete steps, not "test the app". -->

1.
2.
3.
