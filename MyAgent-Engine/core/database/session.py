from __future__ import annotations

from typing import Any

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.database.base import Base


class DatabaseManager:
    """Async SQLAlchemy engine/session factory supporting SQLite and PostgreSQL."""

    def __init__(self, database_url: str, *, echo: bool = False) -> None:
        kwargs: dict[str, object] = {"pool_pre_ping": True, "echo": echo}
        if database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["poolclass"] = NullPool
        self.engine = create_async_engine(database_url, **kwargs)
        if database_url.startswith("sqlite"):
            event.listen(self.engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def close(self) -> None:
        await self.engine.dispose()

    async def create_schema(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def health(self) -> bool:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True


def _enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    """Enable relational enforcement for every SQLite connection."""
    del connection_record
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()
