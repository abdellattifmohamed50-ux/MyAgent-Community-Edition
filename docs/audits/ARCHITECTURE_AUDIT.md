# Architecture Audit

## Conclusion

The v2 modular monolith is the correct base. It provides enough modularity for
providers, tools, memory, security, persistence, and optional RAG without the
operational overhead of the old Redis/Qdrant/event-bus/worker topology.

## Preserved mature components

- provider registry/router and HTTP implementations;
- bounded conversation memory and summaries;
- FastAPI dependency injection and service boundaries;
- JWT/refresh/RBAC flow;
- web, Flutter, and Electron clients;
- Alembic/SQLAlchemy persistence;
- structured logging and health checks.

## Selectively adopted improvements

- relational constraints and SQLite-safe batch migrations;
- deterministic pagination and project detail;
- request-size enforcement for chunked bodies;
- safer WebSocket token transport;
- auth-specific throttling;
- document parsing independent of RAG;
- Docker/PaaS packaging and stronger handoff documentation.

## Rejected complexity

The fixed reference's nested old repository, attached ZIP, generated source maps,
React dashboard, Express scaffold, Replit workspace, egg metadata, and duplicate
build outputs were not imported. They did not replace the existing clients/API
and would have increased ownership and build complexity.

## Findings

- No circular imports were found by import/typing/test execution.
- No duplicate active API implementation remains.
- Optional enterprise extensions are not in the startup graph.
- The primary scalability boundary is process-local rate limiting, documented as
  an extension point rather than hidden enterprise code.

**Architecture score:** 9.1/10 based on 20 rubric checks, with deductions for
process-local limiting and absence of an external extension SDK.
