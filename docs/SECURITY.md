# Security Design

## Authentication and authorization

Passwords use Argon2 through `pwdlib`. Unknown-user login performs fixed-hash
verification to reduce timing-based enumeration. Access and refresh JWTs require
`exp`, `iat`, `jti`, `sub`, and `type`; refresh JWTs also require `sid`. Token type,
expiry, subject, and active user are validated. RBAC and resource ownership are
enforced independently of relational constraints.

Refresh tokens are fingerprinted server-side and rotate through an atomic
compare-and-swap update that works on both SQLite and PostgreSQL. Concurrent use
allows one winner only. A token subject must match the stored session owner.

## Request and transport protection

- Trusted hosts, configured CORS, security headers, sanitized request IDs.
- Declared and chunked request-body size limits.
- Dedicated authentication and general rate limits.
- Bounded Pydantic inputs, refresh JWT length, User-Agent, IP, and error bodies.
- WebSocket tokens are rejected in query strings; native Authorization headers or
  browser subprotocol transport are supported without echoing the secret protocol.

## Provider, RAG, and tool protection

Provider keys remain in environment/secrets and are never returned. HTTP clients
use bounded timeouts, pools, retries, and disabled environment proxy trust. RAG
content is marked untrusted. Calculator input has AST, depth, exponent, length,
and output bounds.

## Production behavior

Production rejects SQLite, default/weak secrets, wildcard or non-HTTPS CORS,
debug mode, automatic schema creation, and demo seeding. PostgreSQL and Alembic
are mandatory. Community rate limiting is process-local; multi-replica deployments
need the optional distributed extension.

## Audit status

Bandit, `pip check`, and npm audit pass. Online `pip-audit` was DNS-blocked.
Container scanning, DAST, and deployed TLS/proxy controls remain unverified and
must pass before READY.
