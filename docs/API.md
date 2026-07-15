# API Guide

The canonical base path is `/api/v1`. The generated source of truth is
`docs/openapi.json`; development environments also expose `/docs` and `/redoc`.
Production disables interactive docs by default.

## Health

- `GET /health/live` — process liveness.
- `GET /health/ready` — readiness including database connectivity; returns 503
  when the database check fails.

## Authentication

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

Access tokens are JWT bearer tokens. Refresh tokens rotate and are tracked as
hashed server-side sessions. Login/register have stricter throttling than normal
API calls.

## Core resources

- Projects: create, list with `limit`/`offset`, fetch by ID, update, delete.
- Conversations: list with pagination, fetch messages with pagination, delete.
- Knowledge: create/upload, list with pagination, fetch, delete.
- Chat: synchronous response and SSE streaming.
- Providers/tools: list configured capabilities.

Collection limits are validated and deterministic ordering includes a stable ID
tie-breaker.

## WebSocket

Endpoint: `/api/v1/ws/chat`.

Native clients may send `Authorization: Bearer <token>`. Browser clients request
both `myagent-v1` and `myagent.jwt.<token>` subprotocols. The server echoes only
the non-secret protocol. URL query tokens are rejected because URLs are commonly
logged.

## Errors

Errors use bounded JSON objects with an `error` code and safe `message`. Internal
provider/database/token details are logged server-side and not returned to the
client. Validation errors use HTTP 422, auth failures 401/403, rate limits 429,
oversized bodies 413, and degraded readiness 503.
