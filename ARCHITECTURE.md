# Architecture

## Decision

MyAgent Community Edition v3.0 is a modular monolith. This preserves the mature
v2 provider, memory, security, and client implementations while integrating the
best relational, pagination, migration, deployment, and safety improvements from
the fixed reference. The project was evolved rather than rewritten.

## Runtime boundary

The required runtime is:

1. FastAPI application and middleware;
2. typed settings and structured logging;
3. JWT authentication, rotating refresh sessions, and RBAC;
4. SQLAlchemy persistence using SQLite or PostgreSQL;
5. provider registry/router and mock provider;
6. bounded conversation memory;
7. optional built-in tools;
8. liveness/readiness checks.

No Redis, Qdrant, queue, worker, marketplace, analytics, monitoring, metrics, or
cluster component is imported or initialized on the default path.

## Module flow

```text
HTTP/WebSocket routes
        │
        ▼
Dependencies + auth/RBAC
        │
        ▼
Application services (AuthService, ChatService)
        │
        ├── Provider router/registry
        ├── Bounded memory
        ├── Tool registry
        ├── Optional in-process RAG search
        └── Repositories
                 │
                 ▼
         SQLAlchemy AsyncSession
                 │
          SQLite / PostgreSQL
```

## Data ownership

Users own projects, conversations, and knowledge documents. Foreign keys enforce
ownership graph integrity. Mandatory children cascade on deletion; optional
project links use `SET NULL`. Alembic is the production schema authority.

## Feature isolation

Feature flags are evaluated by typed configuration. `FEATURE_RAG=false` avoids
importing the RAG search module in the chat path. Enterprise flags are represented
for compatible configuration handoff but Community Edition rejects attempts to
enable unbundled extensions with a clear message.

## API and clients

The canonical API is `/api/v1`. Legacy unprefixed aliases are off by default and
may be enabled temporarily with `ENABLE_LEGACY_ROUTES=true`. WebSocket browser
authentication uses a non-secret protocol plus a token-bearing subprotocol; query
string tokens are rejected.

The web, mobile, and desktop clients are optional consumers. They do not affect
engine startup.

## Scale path

Scale vertically first, then move SQLite to PostgreSQL. Multiple stateless API
replicas require shared PostgreSQL and an external implementation for rate-limit
coordination or other enterprise extensions. Those distributed components remain
outside Community Edition rather than creating dormant complexity.

Detailed diagrams and trade-offs are in `docs/ARCHITECTURE.md`.
