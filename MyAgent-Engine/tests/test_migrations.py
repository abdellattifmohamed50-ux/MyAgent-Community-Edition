from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from alembic import command
from alembic.config import Config
from pytest import MonkeyPatch


def test_alembic_upgrade_and_downgrade_on_sqlite(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    monkeypatch.setenv("API_PORT", "8000")
    engine_dir = Path(__file__).resolve().parents[1]
    config = Config(str(engine_dir / "alembic.ini"))
    config.set_main_option("script_location", str(engine_dir / "migrations"))

    command.upgrade(config, "head")

    with closing(sqlite3.connect(database_path)) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        conversation_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(conversations)")
        }
        message_columns = {row[1] for row in connection.execute("PRAGMA table_info(messages)")}
        message_foreign_keys = {
            (row[2], row[3], row[4], row[6])
            for row in connection.execute("PRAGMA foreign_key_list(messages)")
        }
        conversation_indexes = {
            row[1] for row in connection.execute("PRAGMA index_list(conversations)")
        }

    assert revision == ("0004_relational_integrity",)
    assert {
        "users",
        "projects",
        "conversations",
        "messages",
        "refresh_sessions",
        "knowledge_documents",
        "audit_events",
    }.issubset(tables)
    assert "summary" in conversation_columns
    assert {"model", "estimated_cost_microusd"}.issubset(message_columns)
    assert ("conversations", "conversation_id", "id", "CASCADE") in message_foreign_keys
    assert {"ix_conversations_project_id", "ix_conversations_user_id"}.issubset(
        conversation_indexes
    )

    command.downgrade(config, "base")

    with closing(sqlite3.connect(database_path)) as connection:
        remaining = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert remaining <= {"alembic_version", "sqlite_sequence"}
