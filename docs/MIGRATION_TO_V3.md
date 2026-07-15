# Migration to MyAgent Community Edition v3.0

## Before upgrading

1. Back up the database and environment configuration.
2. Stop all v1/v2 application instances.
3. Record the current Alembic revision.
4. Remove unsupported environment flags or keep enterprise flags `false`.
5. Validate production secrets, HTTPS CORS origins, and trusted hosts.

## Database

Run:

```bash
cd MyAgent-Engine
alembic upgrade head
```

The head revision is `0004_relational_integrity`. It removes/detaches orphaned
relationships before adding foreign keys, then creates the project lookup index.
Review orphan cleanup behavior against a restored backup before production use.

SQLite and PostgreSQL are supported. Production mode accepts only
`postgresql+asyncpg://` URLs; common PaaS `postgres://` and `postgresql://` values
are normalized automatically.

## Configuration changes

- Default database is SQLite.
- `SEED_DEMO_USER=false` by default.
- `FEATURE_RAG=false` by default.
- `ENABLE_LEGACY_ROUTES=false` by default.
- Production requires `AUTO_CREATE_TABLES=false` and Alembic.
- Query-string WebSocket tokens are no longer accepted.
- Legacy Redis/Qdrant/queue/worker settings do not activate Community features.

## Client changes

Clients should use `/api/v1`. Browser WebSocket clients send the protocols
`myagent-v1` and `myagent.jwt.<access-token>`. Native clients may send an
`Authorization: Bearer` header.

## Rollback

Code rollback without database review is unsafe after relational constraints are
introduced. Test `alembic downgrade` against a backup, understand the lost v2/v3
columns and constraints, and never perform an unplanned production downgrade.
