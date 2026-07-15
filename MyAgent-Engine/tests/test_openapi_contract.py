from __future__ import annotations

import json
from pathlib import Path

from apps.backend.main import create_app
from core.config.settings import Settings


def test_committed_openapi_contract_is_current() -> None:
    root = Path(__file__).resolve().parents[2]
    committed = json.loads((root / "docs" / "openapi.json").read_text(encoding="utf-8"))
    settings = Settings(
        ENVIRONMENT="testing",
        API_PORT=8000,
        DATABASE_URL="sqlite+aiosqlite:///./openapi-test.db",
        AUTO_CREATE_TABLES=False,
        SEED_DEMO_USER=False,
        SECRET_KEY="openapi-secret-key-with-more-than-32-characters",
        JWT_SECRET="openapi-jwt-secret-with-more-than-32-characters",
        CORS_ORIGINS="http://localhost",
        TRUSTED_HOSTS="testserver",
        DEFAULT_PROVIDER="mock",
        FEATURE_RAG=False,
        ENABLE_LEGACY_ROUTES=False,
    )
    generated = create_app(settings).openapi()
    assert generated == committed
    assert generated["info"]["version"] == "3.0.0"
    assert "/api/v1/health/ready" in generated["paths"]
    assert "/api/v1/ws/chat" not in generated["paths"]
