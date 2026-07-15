# MyAgent Community Edition v3.0 Release Notes

MyAgent v3.0 consolidates the mature v2 architecture and the strongest fixes from
the fixed reference into one simpler Community Edition repository. It does not
rebuild the product and does not reintroduce the v1 distributed topology.

## Highlights

- SQLite-first zero-infrastructure startup with mock AI provider.
- Official PostgreSQL production path.
- Strong production configuration validation.
- Optional RAG and tools with isolated feature loading.
- Explicit inert enterprise-extension flags.
- Foreign-key enforcement and tested Alembic migrations.
- Pagination across collection APIs.
- Hardened WebSocket authentication, request-size limits, auth throttling, JWT,
  atomic one-winner refresh rotation, RAG delimiters, provider key handling, and calculator tools.
- Docker/Compose, Render, Railway, and SHA-pinned GitHub Actions configuration.
- Generated OpenAPI contract and comprehensive AI/maintainer handoff.

## Compatibility

The canonical API remains `/api/v1`. Legacy unprefixed aliases are disabled by
default and can be temporarily enabled with `ENABLE_LEGACY_ROUTES=true`.
Database upgrades proceed through migrations `0001` → `0004`. Back up production
data before upgrading.

## Release qualification

This repository is a v3.0 source candidate. Local and SQLite gates pass, but the
formal status is `NOT READY` until Docker, PostgreSQL, the online Python dependency audit,
Electron packaging, Flutter, and PaaS staging evidence are completed. Clean offline npm
installation and audit already pass. See `PROJECT_STATUS.md`.
