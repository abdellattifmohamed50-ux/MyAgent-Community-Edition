from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_project_crud(client: TestClient) -> None:
    tokens = register_user(client)
    headers = auth_headers(tokens)
    created = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Research", "instructions": "Answer concisely."},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]
    assert client.get("/api/v1/projects", headers=headers).json()[0]["name"] == "Research"
    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"description": "Private research workspace"},
    )
    assert updated.json()["description"] == "Private research workspace"
    assert client.delete(f"/api/v1/projects/{project_id}", headers=headers).status_code == 204


def test_chat_can_be_attached_to_project(client: TestClient) -> None:
    tokens = register_user(client)
    headers = auth_headers(tokens)
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Project One"}).json()
    chat = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "Project question", "project_id": project["id"]},
    )
    assert chat.status_code == 200
    conversation = client.get(
        f"/api/v1/conversations/{chat.json()['conversation_id']}",
        headers=headers,
    ).json()
    assert conversation["project_id"] == project["id"]


def test_knowledge_create_list_and_delete(client: TestClient) -> None:
    tokens = register_user(client)
    headers = auth_headers(tokens)
    created = client.post(
        "/api/v1/knowledge",
        headers=headers,
        json={"title": "Policy", "content": "Refunds are available for 14 days."},
    )
    assert created.status_code == 201
    document_id = created.json()["id"]
    listed = client.get("/api/v1/knowledge", headers=headers).json()
    assert listed[0]["title"] == "Policy"
    deleted = client.delete(f"/api/v1/knowledge/{document_id}", headers=headers)
    assert deleted.status_code == 204


def test_knowledge_file_upload(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=auth_headers(tokens),
        files={"file": ("notes.md", b"# Notes\nPrivate facts", "text/markdown")},
    )
    assert response.status_code == 201
    assert response.json()["source_type"] == "file"


def test_knowledge_rejects_binary_upload(client: TestClient) -> None:
    tokens = register_user(client)
    response = client.post(
        "/api/v1/knowledge/upload",
        headers=auth_headers(tokens),
        files={"file": ("image.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 422


def test_project_ownership_is_enforced(client: TestClient) -> None:
    first = register_user(client, "first@example.com")
    second = register_user(client, "second@example.com")
    project = client.post(
        "/api/v1/projects",
        headers=auth_headers(first),
        json={"name": "Private"},
    ).json()
    response = client.post(
        "/api/v1/chat",
        headers=auth_headers(second),
        json={"message": "Read it", "project_id": project["id"]},
    )
    assert response.status_code == 403


def test_project_delete_preserves_conversations_and_knowledge(client: TestClient) -> None:
    tokens = register_user(client)
    headers = auth_headers(tokens)
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Temporary"}).json()
    document = client.post(
        "/api/v1/knowledge",
        headers=headers,
        json={
            "title": "Keep me",
            "content": "Persistent knowledge",
            "project_id": project["id"],
        },
    ).json()
    chat = client.post(
        "/api/v1/chat",
        headers=headers,
        json={"message": "Keep this chat", "project_id": project["id"]},
    ).json()

    assert client.delete(f"/api/v1/projects/{project['id']}", headers=headers).status_code == 204
    conversation = client.get(
        f"/api/v1/conversations/{chat['conversation_id']}", headers=headers
    ).json()
    knowledge = client.get("/api/v1/knowledge", headers=headers).json()
    assert conversation["project_id"] is None
    assert next(item for item in knowledge if item["id"] == document["id"])["project_id"] is None
