# Security Audit

## Verified controls

- Argon2 and password-strength checks.
- Timing-equalized unknown-user login.
- Required/type-checked JWT claims and active-user validation.
- Hashed, revocable refresh sessions.
- Atomic one-winner refresh rotation on SQLite; subject/session owner matching.
- RBAC and per-resource ownership.
- Auth/general rate limits and request-size enforcement.
- Trusted hosts, CORS, security headers, bounded errors and metadata.
- WebSocket query-token rejection and bounded error disclosure.
- Provider secret isolation, timeouts/retries, untrusted RAG context, tool limits.
- Production fail-closed settings and pinned GitHub Action SHAs.
- Bandit and `pip check` pass; npm audit reports zero vulnerabilities.
- Root Docker context now excludes secrets and local artifacts.

## Residual evidence gaps

`pip-audit` was DNS-blocked. No container scan, DAST, deployed TLS/proxy test,
penetration test, SBOM verification, or PostgreSQL concurrency run was possible.
The release security gate therefore remains open despite no known critical
source-level finding.
