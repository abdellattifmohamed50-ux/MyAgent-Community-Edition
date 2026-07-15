# Production Audit

**Date:** 2026-07-14  
**Decision:** **NOT READY**

## Verified

- Production configuration fails closed for SQLite, weak secrets, unsafe CORS,
  debug, automatic schema creation, and demo seeding.
- SQLite Alembic round trip passes.
- Real Uvicorn readiness, auth, refresh concurrency, providers, tools, chat,
  WebSocket, logout, and graceful shutdown pass.
- Shared database/provider resources close during lifespan shutdown.
- Atomic refresh rotation is database-neutral SQL and regression-tested on SQLite.
- Structured logs, request IDs, deterministic OpenAPI, and package checksum exist.
- Local performance medians remain below one-second bootstrap and 3 ms health p95.

## Unverified mandatory paths

Docker/Compose, PostgreSQL runtime, Render, Railway, TLS/proxy behavior,
backup/restore, failover, and rollback could not be executed here.

The remaining work is external verification plus fixes discovered by it; no
architecture rewrite is justified.
