# Changelog

All notable changes are recorded here. The format follows Keep a Changelog and
versioning follows semantic versioning.

## [3.0.0] - 2026-07-14

### Added

- SQLite-first Community Edition defaults and production PostgreSQL validation.
- Enterprise feature-flag contract with zero-import disabled behavior.
- Relational-integrity migration `0004_relational_integrity`.
- Pagination for projects, conversations, messages, and knowledge.
- Project detail endpoint and committed OpenAPI contract.
- SQLite migration upgrade/downgrade, refresh concurrency, and v3 quality tests.
- Root PaaS Dockerfile, Render Blueprint, Railway config, production Compose file,
  smoke tests, package checksum, and SHA-pinned GitHub Actions.
- `AI_CONTEXT.md`, `PROJECT_STATUS.md`, `NEXT_STEPS.md`, release checklist, open
  source policies, and independent audit set.

### Changed

- Evolved the v2 modular monolith instead of restoring v1 service complexity.
- RAG is disabled by default and imported only when enabled.
- Document parsing moved out of the RAG namespace so uploads remain independent.
- Database relationships now use foreign keys and deterministic pagination.
- WebSocket authentication no longer accepts URL query tokens.
- Refresh rotation now uses atomic compare-and-swap semantics across SQLite/PostgreSQL;
  concurrent replay permits exactly one winner.
- Login/register have a dedicated rate limit; request-size enforcement also
  covers chunked bodies.
- Safer local host binding, stricter production validation, and expanded security
  headers.
- Community Docker Compose now needs only the engine, web client, and SQLite.
- Root Docker build context and release packaging exclude secrets, local databases,
  dependencies, caches, raw evidence, and generated builds.
- Version metadata synchronized to `3.0.0` across engine, desktop, mobile, web,
  deployment, and documentation.

### Removed

- Stale v2 audit/delivery documents and old v1-to-v2 migration guide.
- Mandatory Redis, Qdrant, event bus, queue, and worker topology from the default
  architecture.
- Query-string WebSocket tokens and unconditional legacy route duplication.
- Duplicate repository assets, generated builds, and experimental React/Express
  scaffolding from the fixed reference (not imported into v3).

### Security

- Stronger JWT/refresh flow, enumeration resistance, bounded request bodies,
  user-aware limiting, safer provider key transport, untrusted RAG delimiters,
  calculator limits, and production fail-closed configuration.

## [2.0.0] - 2026-07-13

Reference release that introduced the simplified modular monolith, bounded
memory, provider routing, usage tracking, and the primary security hardening.

## [1.0.0]

Historical ecosystem release. No longer supported.
