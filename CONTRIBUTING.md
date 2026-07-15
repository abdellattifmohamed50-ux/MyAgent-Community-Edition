# Contributing

## Development setup

```bash
git clone <repository>
cd MyAgent-Community-Edition-v3.0
cp .env.example .env
make setup
make migrate
make check
```

Python 3.11–3.13 is supported. Node.js 22 is used for desktop checks. Flutter is
required only for mobile work. Docker is required for container and production
Compose validation.

## Architecture rules

- Preserve the modular monolith unless evidence proves a simpler alternative.
- Keep route logic thin; business behavior belongs in services.
- Keep persistence behind repositories and SQLAlchemy sessions.
- Do not import optional infrastructure on the default path.
- New optional capabilities require a feature flag, isolated dependencies,
  startup-disabled tests, documentation, and a removal path.
- Do not create a second implementation when an existing module can be evolved.
- Do not commit generated builds, databases, secrets, virtual environments, or
  copied repositories.

## Required checks

```bash
make lint
make typecheck
make coverage
make security
make openapi
git diff --exit-code -- docs/openapi.json
```

Changes to models require Alembic migrations and upgrade/downgrade tests. Changes
to routes or schemas require regenerating `docs/openapi.json`. Security-sensitive
changes require tests for both allowed and rejected paths.

## Pull requests

Keep pull requests focused. Include the problem, design decision, compatibility
impact, test evidence, migration impact, security considerations, and docs
updated. A release-affecting pull request must update `CHANGELOG.md`,
`PROJECT_STATUS.md`, and `AI_CONTEXT.md` when relevant.

## Commit hygiene

Use clear imperative commit messages. Never include credentials, customer data,
private prompts, model transcripts, or generated dependency folders.
