from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from apps.backend.main import create_app
from core.config.settings import Settings
from tests.conftest import auth_headers, register_user


def test_community_defaults_disable_optional_features(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in list(os.environ):
        if name.startswith("FEATURE_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    settings = Settings.model_validate({})
    assert settings.feature_tools is True
    assert settings.feature_rag is False
    assert settings.requested_enterprise_features == ()
    assert settings.enabled_features == ("tools",)


def test_enterprise_flag_fails_with_actionable_message() -> None:
    with pytest.raises(ValueError, match="does not bundle enterprise extensions: redis"):
        Settings(API_PORT=8000, FEATURE_REDIS=True)


def test_rag_module_is_not_imported_when_disabled(tmp_path: Path) -> None:
    engine_dir = Path(__file__).resolve().parents[1]
    script = """
import json
import sys
from apps.backend.main import create_app
from core.config.settings import Settings
settings = Settings(
    ENVIRONMENT='testing', API_PORT=8000,
    DATABASE_URL='sqlite+aiosqlite:///./feature-import-test.db',
    AUTO_CREATE_TABLES=False, SEED_DEMO_USER=False,
    SECRET_KEY='s' * 40, JWT_SECRET='j' * 40,
    CORS_ORIGINS='http://localhost', TRUSTED_HOSTS='testserver',
    FEATURE_RAG=False,
)
create_app(settings)
print(json.dumps({'rag_search_imported': 'core.rag.search' in sys.modules}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=engine_dir,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "API_PORT": "8000"},
    )
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result == {"rag_search_imported": False}
    (engine_dir / "feature-import-test.db").unlink(missing_ok=True)


def test_project_pagination_and_get(client: TestClient) -> None:
    tokens = register_user(client)
    headers = auth_headers(tokens)
    created = [
        client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": f"Project {index}"},
        ).json()
        for index in range(3)
    ]
    page = client.get("/api/v1/projects?limit=1&offset=1", headers=headers)
    assert page.status_code == 200
    assert len(page.json()) == 1
    detail = client.get(f"/api/v1/projects/{created[0]['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == created[0]["id"]


def test_legacy_routes_are_disabled_by_default(client: TestClient) -> None:
    assert client.get("/health/live").status_code == 404


def test_websocket_query_token_is_rejected(client: TestClient) -> None:
    tokens = register_user(client)
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(f"/api/v1/ws/chat?token={tokens['access_token']}") as websocket,
    ):
        websocket.receive_json()


def test_auth_rate_limit_is_separate_and_strict(tmp_path: Path) -> None:
    settings = Settings(
        ENVIRONMENT="testing",
        API_PORT=8000,
        DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'rate-limit.db'}",
        AUTO_CREATE_TABLES=True,
        SEED_DEMO_USER=False,
        SECRET_KEY="test-secret-key-with-more-than-32-characters",
        JWT_SECRET="test-jwt-secret-with-more-than-32-characters",
        CORS_ORIGINS="http://localhost",
        TRUSTED_HOSTS="testserver",
        RATE_LIMIT_REQUESTS=100,
        AUTH_RATE_LIMIT_REQUESTS=2,
    )
    with TestClient(create_app(settings)) as limited_client:
        for index in range(2):
            response = limited_client.post(
                "/api/v1/auth/login",
                json={"email": f"missing-{index}@example.com", "password": "NoSuchPass123!"},
            )
            assert response.status_code == 401
        blocked = limited_client.post(
            "/api/v1/auth/login",
            json={"email": "missing-3@example.com", "password": "NoSuchPass123!"},
        )
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "60"
