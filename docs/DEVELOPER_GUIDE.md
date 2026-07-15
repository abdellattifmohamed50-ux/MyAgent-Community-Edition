# Developer Guide

## Repository setup

```bash
make setup
cp .env.example .env
make migrate
make check
```

Run `make run` for a reload server. Use the mock provider for deterministic local
development.

## Change workflow

1. Identify the existing module that owns the behavior.
2. Add or update tests before broad refactoring.
3. Keep optional imports inside the enabled path.
4. Add a migration for model changes.
5. Run formatting, lint, strict typing, coverage, security checks, and OpenAPI
   generation.
6. Synchronize architecture/status/handoff docs when behavior changes.

## Database changes

Create additive Alembic migrations where possible. Migrations must run on both
SQLite and PostgreSQL. SQLite constraint changes require batch operations. Add an
upgrade/downgrade test and test orphan-data behavior before adding constraints.

## API changes

Use Pydantic schemas and repository/service methods; do not put SQL in routes.
Regenerate the contract:

```bash
make openapi
git diff -- docs/openapi.json
```

Intentional breaking changes require a versioning decision and migration note.

## Optional capability rules

An optional feature must have:

- a default-off flag;
- no import or package requirement while off;
- no startup/resource initialization while off;
- a focused module boundary;
- tests proving disabled startup;
- documentation and operational failure behavior.

## Test strategy

Unit tests cover providers, tools, memory, security, and config. API tests cover
auth, ownership, chat, pagination, health, request limits, and WebSocket auth.
Migration tests exercise SQLite head/base. CI adds PostgreSQL, containers, online
audits, desktop packaging, and Flutter.
