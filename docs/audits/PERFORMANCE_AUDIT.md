# Performance Audit

## Improvements

- Default startup excludes Redis, Qdrant, queues, workers, analytics, monitoring,
  metrics, clustering, enterprise providers, and disabled RAG search imports.
- Providers share one lazy async HTTP client and bounded connection pool.
- Memory/context is bounded by count and characters.
- Collection queries use limit/offset and deterministic indexes/order.
- SQLite uses `NullPool` to avoid retained connections in the local path.
- Docker uses multi-stage builds and copies only runtime dependencies.

## Measurement

Median of five clean workers, 100 health requests each:

- bootstrap 890.323 ms;
- p50 2.206 ms;
- p95 3.157 ms;
- max RSS 91,208 KB.

## Limitations

No production PostgreSQL, model-provider, Docker cold-start, concurrency, or load
benchmark was possible. Offset pagination may degrade at very high offsets.

**Performance score:** 8.7/10 based on 15 rubric checks, with deductions for
missing production load data and cursor pagination.
