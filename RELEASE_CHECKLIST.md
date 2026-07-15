# Release Checklist

Every mandatory item requires direct evidence. Configuration files alone are not
runtime proof.

## Source and quality

- [x] Version and documentation are synchronized.
- [x] Community startup excludes disabled enterprise imports/dependencies.
- [x] Ruff format and lint pass.
- [x] Mypy strict passes on 86 source files.
- [x] 104 tests pass.
- [x] Coverage exceeds 84% (85.04% measured).
- [x] Bandit and `pip check` pass.
- [x] OpenAPI is regenerated and contract-tested.
- [x] No import cycles or exact duplicate source/artifact groups were found.
- [ ] Online `pip-audit --strict` passes.

## Authentication and runtime

- [x] SQLite migration upgrade/downgrade/upgrade passes.
- [x] Readiness, registration, login, refresh, chat, WebSocket, tools, providers,
  logout, and graceful shutdown pass against a real Uvicorn process.
- [x] Concurrent SQLite refresh rotation permits exactly one winner.
- [x] Oversized refresh-token input and persisted request metadata are bounded.
- [ ] PostgreSQL migration and authenticated smoke pass.
- [ ] Concurrent refresh rotation passes on PostgreSQL.

## Containers and deployment

- [x] Dockerfiles, Compose, Render, Railway, and CI manifests parse structurally.
- [x] Root `.dockerignore` excludes secrets, caches, local databases, evidence,
  dependencies, and build outputs.
- [ ] Root and web `docker build` succeed.
- [ ] Community `docker compose config/up/smoke/down` succeeds.
- [ ] Production PostgreSQL Compose startup, restart, persistence, and shutdown succeed.
- [ ] Render staging passes.
- [ ] Railway staging passes.

## Clients

- [x] Web/Electron JavaScript syntax passes.
- [x] Clean offline `npm ci` succeeds.
- [x] Offline npm audit reports zero vulnerabilities.
- [ ] Electron Linux packaging completes (binary download was DNS-blocked locally).
- [ ] Flutter format, analyze, and tests pass.
- [x] TypeScript/pnpm is not applicable; v3 intentionally contains no TS workspace.

## Packaging

- [x] Packaging excludes `.env*`, databases, caches, dependencies, builds, and raw evidence.
- [x] One ZIP and SHA-256 checksum are generated and verified.
- [ ] All mandatory external gates above are green.

**Current release decision: NOT READY**
