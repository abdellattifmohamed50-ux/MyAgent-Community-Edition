# MyAgent Engine v3.0

FastAPI backend for MyAgent Community Edition.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn apps.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Development API docs are available at `http://127.0.0.1:8000/docs`.

## Default runtime

- SQLite via `aiosqlite`;
- mock provider;
- JWT authentication and rotating refresh sessions;
- RBAC and resource ownership;
- providers, bounded memory, tools, logging, and health checks;
- RAG disabled;
- no Redis/Qdrant/worker/queue requirement.

## Quality

```bash
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/mypy core apps agents services repositories models tests
.venv/bin/pytest -q
.venv/bin/bandit -q -r apps core agents services repositories models
.venv/bin/pip-audit --strict
```

Use Alembic for production. `AUTO_CREATE_TABLES` is a development convenience and
must be false in production.
