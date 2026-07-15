# Roadmap

## Release gate for v3.0

- Execute the existing GitHub Actions workflow on a clean hosted runner.
- Confirm Docker engine/web builds, Compose startup, and authenticated smoke test.
- Confirm PostgreSQL migration and API smoke test.
- Complete online `pip-audit`; clean offline `npm ci` and npm audit already pass.
- Complete Flutter format, analyze, and test gates.
- Perform one Render and one Railway staging deployment with readiness checks.

These are evidence gates, not missing implementation. They are listed in
`NEXT_STEPS.md` in priority order.

## v3.1 — operational hardening

- Add retention jobs for expired refresh sessions and old audit events.
- Add cursor pagination where very large collections justify it.
- Add browser automation for the static PWA.
- Execute the existing refresh-token concurrency regression on PostgreSQL in CI.
- Add signed release provenance and SBOM generation.

## v3.2 — extension SDK

- Define a stable, versioned provider/tool extension contract.
- Publish a separate optional package for Redis-backed distributed rate limits.
- Publish a separate optional vector-store/RAG extension.
- Keep every extension out of the Community startup dependency graph.

## Not planned for Community core

A service mesh, mandatory broker, always-on worker fleet, embedded marketplace,
cluster manager, or analytics warehouse. These belong in independently versioned
extensions and must not make the solo-developer path harder.
