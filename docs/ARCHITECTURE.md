# Detailed Architecture Audit

## System shape

MyAgent v3 is one FastAPI process with explicit internal modules. This is the
smallest architecture that satisfies authentication, providers, tools, memory,
persistence, logging, and health checks while preserving a clean extension path.

### Layers

| Layer | Primary paths | Responsibility |
|---|---|---|
| Entry/API | `apps/backend` | HTTP/WebSocket, middleware, validation, dependency injection |
| Services | `services` | Authentication and chat use cases |
| Domain capabilities | `core` | Settings, providers, memory, tools, security, optional RAG |
| Persistence | `repositories`, `models` | SQL queries, entities, schemas |
| Composition | `core/container.py` | Construct required runtime dependencies |
| Schema evolution | `migrations` | SQLite/PostgreSQL Alembic history |

Dependencies point inward toward capabilities and persistence interfaces. Routes
do not create provider/database clients directly.

## Startup graph

`create_app()` loads typed settings, configures logging, builds the container, and
registers middleware/routes. The lifespan starts schema creation only when
explicitly enabled and closes HTTP/database resources on shutdown.

Default startup constructs no Redis, Qdrant, queue, worker, marketplace,
analytics, metrics, monitoring, cluster, or enterprise-provider dependency.
`FEATURE_RAG=false` also prevents the chat service from importing RAG search.

## Persistence

SQLite uses `aiosqlite`, foreign-key pragmas, and `NullPool`. PostgreSQL uses
`asyncpg`. SQLAlchemy models and migrations agree on key relationships:

- user → refresh sessions/projects/conversations/knowledge/audit events;
- project → conversations/knowledge;
- conversation → messages.

Ownership checks remain in services/routes even with relational constraints.
Foreign keys protect integrity; authorization protects access.

## Request path

1. Trusted-host/CORS/security/request-ID/body-size/rate-limit middleware.
2. Pydantic request validation.
3. Bearer token decode and active-user lookup.
4. RBAC/ownership enforcement.
5. Service execution using one async SQLAlchemy session.
6. Provider/tool/memory/RAG orchestration as configured.
7. Commit/rollback and bounded response/error mapping.

## Provider architecture

A registry stores implementations; a router selects default/fallback providers,
retries transient failures with bounded backoff, and preserves provider-neutral
messages/responses. One lazy shared HTTP client avoids per-call connection-pool
creation. The mock provider keeps the entire Community path offline-capable.

## Memory and RAG

Conversation memory is bounded by message count and character count and uses a
rolling summary. RAG is an optional in-process repository search, not a mandatory
vector database. Retrieved content is delimited as untrusted context before it is
sent to a model.

## Rejected alternatives

- Blindly replacing v2 with the fixed repository: rejected because it restored a
  v1 base and duplicated API/client/build layers.
- Mandatory Redis/Qdrant/workers: rejected because they block zero-infrastructure
  startup and increase operating burden.
- Microservices: rejected because current scale and ownership boundaries do not
  justify network/distributed-state complexity.
- New React/Express workspace: rejected because it duplicates the existing API
  and PWA without replacing them cleanly.

## Scalability boundaries

PostgreSQL and stateless API replicas support the primary scale path. Process-
local rate limits and in-process optional RAG are deliberately Community-grade.
Distributed rate limiting, vector search, queueing, and background processing
should be separately packaged extensions behind the existing feature contract.
