from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from apps.backend.main import create_app
from core.config.settings import Settings


def _test_settings(tmp_path: Path, database_name: str, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "ENVIRONMENT": "testing",
        "DEBUG": False,
        "API_PORT": 8000,
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / database_name}",
        "AUTO_CREATE_TABLES": True,
        "SEED_DEMO_USER": False,
        "SECRET_KEY": "test-secret-key-with-more-than-32-characters",
        "JWT_SECRET": "test-jwt-secret-with-more-than-32-characters",
        "CORS_ORIGINS": "http://localhost",
        "TRUSTED_HOSTS": "testserver,localhost",
        "RATE_LIMIT_REQUESTS": 1000,
        "AUTH_RATE_LIMIT_REQUESTS": 1000,
        "DEFAULT_PROVIDER": "mock",
        "FEATURE_RAG": False,
        "ENABLE_LEGACY_ROUTES": False,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(_test_settings(tmp_path, "test.db"))) as test_client:
        yield test_client


@pytest.fixture
def rag_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = _test_settings(tmp_path, "rag-test.db", FEATURE_RAG=True)
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def legacy_client(tmp_path: Path) -> Iterator[TestClient]:
    settings = _test_settings(tmp_path, "legacy-test.db", ENABLE_LEGACY_ROUTES=True)
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def register_user(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "StrongPass123!",
    display_name: str = "Test User",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    result: dict[str, Any] = response.json()
    return result


def auth_headers(tokens: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
