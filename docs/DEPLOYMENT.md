# Deployment Guide

## Local

```bash
cp .env.example .env
make setup
make migrate
make run
```

SQLite is created locally. The mock provider needs no key.

## Community Docker Compose

```bash
docker compose config --quiet
docker compose up --build -d
./scripts/smoke-test.sh
```

The engine applies Alembic migrations before Uvicorn starts. SQLite data lives in
`engine_data`; the PWA is served at port 8080.

## Production Docker Compose

```bash
cp .env.production.example .env
# Replace secrets, database password, HTTPS CORS origin, and trusted host.
docker compose -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.production.yml up --build -d
```

The production topology contains PostgreSQL, a read-only engine filesystem with
`/tmp` tmpfs, and the static web service. The database network is internal.
Terminate TLS at a reverse proxy/load balancer and back up PostgreSQL separately.

## Render

`render.yaml` defines a Docker web service and managed PostgreSQL database. Set
`CORS_ORIGINS` to the final HTTPS frontend origin. Render provides a standard
PostgreSQL URL, which settings normalize to the asyncpg scheme. Readiness uses
`/api/v1/health/ready`.

## Railway

`railway.json` selects the root Dockerfile, runs Alembic before Uvicorn, listens
on the platform `PORT`, and defines the readiness path. Add PostgreSQL and set
production secrets/CORS/trusted hosts in Railway variables.

## Required production settings

- `ENVIRONMENT=production`
- PostgreSQL `DATABASE_URL`
- distinct random `SECRET_KEY` and `JWT_SECRET` of at least 32 characters
- HTTPS-only `CORS_ORIGINS`
- restrictive `TRUSTED_HOSTS`
- `AUTO_CREATE_TABLES=false`
- `SEED_DEMO_USER=false`
- provider keys only through secret management

## Operational checks

After every deploy, verify readiness, registration/login, refresh/logout, chat,
restart persistence, migration revision, logs without secrets, and provider
fallback. Roll back code only with a reviewed database compatibility plan.

The files are structurally validated, but the 2026-07-14 audit environment could
not execute Docker, PostgreSQL, Render, or Railway. These remain release blockers.
