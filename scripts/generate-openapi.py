#!/usr/bin/env python3
"""Generate the committed OpenAPI contract from deterministic settings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "MyAgent-Engine"
sys.path.insert(0, str(ENGINE))

from apps.backend.main import create_app  # noqa: E402
from core.config.settings import Settings  # noqa: E402


def build_schema() -> dict[str, object]:
    settings = Settings(
        ENVIRONMENT="testing",
        API_PORT=8000,
        DATABASE_URL="sqlite+aiosqlite:///./openapi-generation.db",
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
    return create_app(settings).openapi()


def main() -> None:
    output = ROOT / "docs" / "openapi.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
