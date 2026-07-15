from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from tests.conftest import auth_headers, register_user


def test_health_and_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["database"] is True
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-request-id"]


def test_readiness_uses_service_unavailable_when_database_is_down(
    client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def database_is_down() -> bool:
        return False

    app = cast(FastAPI, client.app)
    monkeypatch.setattr(app.state.container.database, "health", database_is_down)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"] is False


def test_register_and_me(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
    assert response.json()["display_name"] == "Test User"


def test_duplicate_registration_is_rejected(client: TestClient) -> None:
    register_user(client)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPass123!",
            "display_name": "Duplicate",
        },
    )
    assert response.status_code == 422


def test_weak_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "abcdefghij", "display_name": "Weak"},
    )
    assert response.status_code == 422
    assert "abcdefghij" not in response.text
    assert "Password must include" in response.json()["message"]


def test_request_size_limit_and_request_id_sanitization(client: TestClient) -> None:
    oversized = client.post(
        "/api/v1/auth/login",
        headers={"content-length": "4000000"},
        content=b"{}",
    )
    assert oversized.status_code == 413
    response = client.get("/api/v1/health/live", headers={"x-request-id": "bad value"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad value"


def test_invalid_content_length_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        headers={"content-length": "not-a-number"},
        content=b"{}",
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_content_length"


def test_request_size_limit_rejects_chunked_body(client: TestClient) -> None:
    def oversized_body() -> Iterator[bytes]:
        yield b"x" * 1_100_000
        yield b"x" * 1_100_000
        yield b"x" * 1_100_000

    response = client.post(
        "/api/v1/auth/login",
        headers={"transfer-encoding": "chunked", "content-type": "application/json"},
        content=oversized_body(),
    )
    assert response.status_code == 413
    assert response.json()["error"] == "request_too_large"


def test_login_rejects_bad_password(client: TestClient) -> None:
    register_user(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_account(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"


def test_login_returns_new_token_pair(client: TestClient) -> None:
    original = register_user(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"] != original["access_token"]


def test_refresh_rotates_token_and_detects_reuse(client: TestClient) -> None:
    tokens = register_user(client)
    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != tokens["refresh_token"]
    reused = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert reused.status_code == 401


def test_refresh_rotation_is_atomic_under_concurrency(client: TestClient) -> None:
    current_token = register_user(client, email="race@example.com")["refresh_token"]

    for _ in range(5):
        barrier = Barrier(3)

        def rotate(start_barrier: Barrier, token: str) -> tuple[int, dict[str, object]]:
            start_barrier.wait()
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": token},
            )
            return response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(rotate, barrier, current_token) for _ in range(2)]
            barrier.wait()
            results = [future.result() for future in futures]

        assert sorted(status for status, _ in results) == [200, 401]
        current_token = next(
            str(body["refresh_token"]) for status, body in results if status == 200
        )


def test_auth_metadata_and_refresh_token_inputs_are_bounded(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        headers={"user-agent": "agent/" + "x" * 5_000},
        json={
            "email": "metadata@example.com",
            "password": "StrongPass123!",
            "display_name": "Metadata User",
        },
    )
    assert response.status_code == 201

    oversized = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "x" * 4_097},
    )
    assert oversized.status_code == 422


def test_logout_revokes_refresh_session(client: TestClient) -> None:
    tokens = register_user(client)
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 401


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/conversations")
    assert response.status_code == 401


def test_legacy_auth_path_remains_compatible(legacy_client: TestClient) -> None:
    response = legacy_client.post(
        "/auth/register",
        json={
            "email": "legacy@example.com",
            "password": "StrongPass123!",
            "display_name": "Legacy User",
        },
    )
    assert response.status_code == 201
