#!/usr/bin/env python3
"""Exercise the authenticated API against DATABASE_URL, normally PostgreSQL in CI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "MyAgent-Engine"))

from fastapi.testclient import TestClient  # noqa: E402

from apps.backend.main import create_app  # noqa: E402
from core.config.settings import Settings  # noqa: E402


def main() -> None:
    settings = Settings()
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL is required")
    email = f"ci-{uuid4().hex}@example.com"
    password = "PostgresSmoke123!"
    with TestClient(create_app(settings)) as client:
        ready = client.get("/api/v1/health/ready")
        ready.raise_for_status()
        registered = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "display_name": "CI Smoke"},
        )
        registered.raise_for_status()
        token = registered.json()["access_token"]
        chat = client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "PostgreSQL smoke test"},
        )
        chat.raise_for_status()
        assert chat.json()["provider"] == "mock"
    print("MYAGENT_POSTGRES_SMOKE=PASS")


if __name__ == "__main__":
    main()
