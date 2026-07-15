# AI Context — MyAgent Community Edition v3.0

## Current decision

`NOT READY` as of 2026-07-14. Source and SQLite runtime gates are green, but
Docker, PostgreSQL, Flutter, online Python advisory lookup, Electron packaging,
and PaaS staging evidence are unavailable.

## Architecture contract

- Preserve the FastAPI modular monolith.
- Community mode is SQLite-first and requires no Redis, Qdrant, queue, worker, or metrics stack.
- Production uses PostgreSQL and Alembic.
- Tools are enabled by default; RAG and enterprise capabilities are optional and default-off.
- Disabled optional features must not import or initialize their dependency graph.
- Web, Flutter, and Electron remain optional clients.

## Final release engineering finding

The prior refresh rotation used `SELECT ... FOR UPDATE`, which SQLite ignores.
Real concurrency testing produced two successes in 18/20 rounds. It was replaced
with an atomic conditional `UPDATE`; five automated and twenty real-server rounds
now each produce exactly one 200 and one 401. Do not revert this to row locking.

## Verified baseline

- 104 tests pass; 85.04% coverage.
- Ruff, strict mypy, compileall, Bandit, and `pip check` pass.
- SQLite migration round trip and full real-Uvicorn E2E pass.
- Clean offline npm install/audit pass with zero vulnerabilities.
- OpenAPI, syntax, manifest, import-cycle, duplicate, and benchmark checks pass.
- Benchmark medians: 756.6 ms bootstrap, 1.926 ms p50, 2.771 ms p95, 90,268 KB RSS.

## Evidence limits

- No Docker/Compose/Podman daemon.
- No PostgreSQL binaries/service.
- No Flutter/Dart or pnpm.
- DNS cannot resolve pypi.org or github.com.
- Electron rebuild passes but binary packaging is DNS-blocked.

## Next engineer rules

1. Do not redesign or weaken gates to force READY.
2. Run the existing GitHub Actions workflow unchanged first.
3. Fix any runtime failure in source, then repeat the exact failing gate.
4. Record immutable CI/staging links or logs in `RELEASE_CHECKLIST.md`.
5. Set READY only after every P0/P1 item in `PROJECT_STATUS.md` is closed.
