# Performance Benchmark

## Method

`scripts/benchmark-engine.py` launches five independent worker processes. Each
worker builds a testing application with SQLite and mock provider, starts a
TestClient lifespan, and issues 100 `/api/v1/health/live` requests. Results use
the median across workers.

## v3.0 result — 2026-07-14

| Metric | Median |
|---|---:|
| Bootstrap | 890.323 ms |
| Health p50 | 2.206 ms |
| Health p95 | 3.157 ms |
| Maximum RSS | 91,208 KB |

## Interpretation

The result confirms bounded Community startup and low health-check overhead in
the audit environment. It does not measure network, model latency, PostgreSQL,
concurrency saturation, streaming throughput, or container cold starts.

The architecture reduces default dependency/import work by excluding enterprise
services and disabled RAG search. A single lazy provider HTTP client reuses
connections. SQLite uses no persistent connection pool; PostgreSQL retains the
SQLAlchemy async pool.

Future benchmarking should run in containers with PostgreSQL, profile import
cost by module, and add authenticated chat/load tests using a deterministic mock
provider.
