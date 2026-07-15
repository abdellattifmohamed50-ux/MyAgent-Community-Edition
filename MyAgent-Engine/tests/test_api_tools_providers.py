from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_provider_catalog_marks_mock_ready(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.get("/api/v1/providers", headers=auth_headers(tokens))
    assert response.status_code == 200
    providers = {item["name"]: item for item in response.json()}
    assert providers["mock"]["configured"] is True
    assert providers["mock"]["healthy"] is True
    assert "openai" in providers
    assert "gemini" in providers


def test_tool_catalog(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.get("/api/v1/tools", headers=auth_headers(tokens))
    assert {item["name"] for item in response.json()} == {
        "calculator",
        "datetime",
        "text_stats",
    }


def test_calculator_tool(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.post(
        "/api/v1/tools/calculator/execute",
        headers=auth_headers(tokens),
        json={"arguments": {"expression": "(12 + 3) * 4"}},
    )
    assert response.status_code == 200
    assert response.json()["output"] == "60"


def test_calculator_blocks_code_execution(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.post(
        "/api/v1/tools/calculator/execute",
        headers=auth_headers(tokens),
        json={"arguments": {"expression": "__import__('os').getcwd()"}},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_text_stats_tool(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.post(
        "/api/v1/tools/text_stats/execute",
        headers=auth_headers(tokens),
        json={"arguments": {"text": "one two\nthree"}},
    )
    assert response.json()["metadata"] == {"characters": 13, "words": 3, "lines": 2}
