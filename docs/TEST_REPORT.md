# Test Report

**Date:** 2026-07-14

| Gate | Result |
|---|---|
| Pytest | 104 passed |
| Coverage | 85.04% measured; threshold 84% |
| Ruff format/lint | Pass |
| Mypy strict | Pass on 86 source files |
| Bandit | Pass |
| `pip check` | Pass |
| SQLite migration round trip | Pass |
| Real Uvicorn E2E | Pass |
| Refresh concurrency | Pass: 5 automated + 20 real-server cycles |
| OpenAPI contract | Pass |
| JavaScript/shell/YAML/JSON | Pass |
| Clean offline npm install/audit | Pass; zero vulnerabilities |
| Import cycles / exact duplicates | 0 / 0 |

The E2E path covers readiness, register, `/me`, login, refresh rotation and reuse,
providers, calculator execution, chat, WebSocket streaming, logout, and graceful
shutdown. A long User-Agent is accepted safely after persistence bounding.

`pip-audit --strict` could not resolve pypi.org. Electron packaging completed
native dependency rebuild and reached packaging, then failed resolving github.com.
Docker, PostgreSQL, Flutter, Render, and Railway were unavailable. These are
release blockers, not test failures hidden as passes.
