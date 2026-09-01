# Contributing

Thanks for your interest in Seiton Brain.

This is a **real product** under active development — not a demo or learning
exercise. The repository is public under [MIT](LICENSE) while a commercial
self-hosted edition is planned ([ADR 0005](docs/adr/0005-repo-and-license-strategy.md)).

---

## Maintainer model

Development is led by a **solo maintainer**. There is no large community governance
layer. That means:

- **Bug reports and small PRs** (docs, tests, clear fixes) are appreciated
- **Large features** need a [ROADMAP](ROADMAP.md) story or an issue discussion first
- **Response time** is best-effort, not SLA-backed
- **Language for new GitHub artifacts:** English (issues, PR titles/descriptions, commit messages on new work)

---

## Before you start

1. **Current state:** [docs/current-state.md](docs/current-state.md)
2. **Roadmap:** [ROADMAP.md](ROADMAP.md) — is there already a story?
3. **Engineering workflow:** [docs/engineering.md](docs/engineering.md) (CI, review, CodeRabbit)
4. **Security issues:** **not** as public issues — see [SECURITY.md](SECURITY.md)
5. **Architecture changes:** read [ARCHITECTURE.md](ARCHITECTURE.md) and relevant [ADRs](docs/adr/)

Self-hosting questions: [docs/self-hosting.md](docs/self-hosting.md),
[docs/setup.md](docs/setup.md).

---

## Development setup

```bash
git clone https://github.com/LeekiGitHub/Seiton-Brain.git
cd Seiton-Brain
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # adjust for local testing
pytest
ruff check app tests
```

Docker-based setup: [docs/setup.md](docs/setup.md).

---

## Branches & pull requests

`main` is protected (PR + CI required). Use short-lived branches:

| Prefix | Use |
|--------|-----|
| `feat/` | new behavior |
| `fix/` | bugfix |
| `chore/` | tooling, deps |
| `docs/` | documentation only |

One roadmap story → one branch → one PR. Reference the story ID (e.g. `E47-1`)
in the title or description.

**Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/)
in English, e.g. `feat(ui): E30-4 toast feedback layer`.

### PR checklist

- [ ] `ruff check app tests` and `pytest` pass
- [ ] [CHANGELOG.md](CHANGELOG.md) updated under `[Unreleased]` when user-visible
- [ ] [ROADMAP.md](ROADMAP.md) status updated if completing a story
- [ ] ADR considered for non-obvious architecture decisions
- [ ] Manually tested when behavior changes (Telegram, UI, API)
- [ ] Wait for CodeRabbit review on code PRs (auto-triggered; advisory only)

Template: [.github/pull_request_template.md](.github/pull_request_template.md).

---

## Code conventions

| Topic | Rule |
|-------|------|
| Config / secrets | Only via `app/config.py` and `.env` — never hardcode |
| Celery tasks | Use `worker_session()` ([ADR 0001](docs/adr/0001-async-engine-per-celery-task.md)) |
| Vault paths | `app/vault/paths.py` — prevent path traversal |
| Prompts | Versioned files under `prompts/` |
| Migrations | Alembic under `alembic/versions/` |
| `.gitignore` | `/vault/` and `/models/` at repo root only ([ADR 0002](docs/adr/0002-gitignore-vault-and-models-pitfall.md)) |

---

## License

By contributing, you agree that your contributions are licensed under the
repository's [MIT License](LICENSE).
