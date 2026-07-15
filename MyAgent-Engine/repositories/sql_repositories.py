from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from sqlalchemy import or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from models.entities import (
    AuditEvent,
    Conversation,
    KnowledgeDocument,
    Message,
    Project,
    RefreshSession,
    User,
)


class SqlRepository:
    """Base class for transaction-aware SQLAlchemy repositories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session


class UserRepository(SqlRepository):
    async def get(self, user_id: str) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user


class RefreshSessionRepository(SqlRepository):
    async def get(self, session_id: str) -> RefreshSession | None:
        return await self.session.get(RefreshSession, session_id)

    async def rotate_if_active(
        self,
        session_id: str,
        current_token_hash: str,
        new_token_hash: str,
        new_expires_at: datetime,
        now: datetime,
    ) -> bool:
        """Atomically rotate one active refresh token across SQLite and PostgreSQL."""
        result = await self.session.execute(
            update(RefreshSession)
            .where(
                RefreshSession.id == session_id,
                RefreshSession.token_hash == current_token_hash,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > now,
            )
            .values(token_hash=new_token_hash, expires_at=new_expires_at)
            .execution_options(synchronize_session=False)
        )
        cursor = cast(CursorResult[Any], result)
        return cursor.rowcount == 1

    async def add(self, refresh_session: RefreshSession) -> RefreshSession:
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session

    async def revoke(self, refresh_session: RefreshSession, revoked_at: datetime) -> None:
        refresh_session.revoked_at = revoked_at
        await self.session.flush()


class ProjectRepository(SqlRepository):
    async def list_for_user(
        self, user_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .where(Project.owner_id == user_id)
            .order_by(Project.updated_at.desc(), Project.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def get_for_user(self, project_id: str, user_id: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id, Project.owner_id == user_id)
        )
        return result.scalar_one_or_none()

    async def add(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)


class ConversationRepository(SqlRepository):
    async def list_for_user(
        self, user_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def get_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(reversed(list(result.scalars())))

    async def delete(self, conversation: Conversation) -> None:
        await self.session.delete(conversation)


class KnowledgeRepository(SqlRepository):
    async def add(self, document: KnowledgeDocument) -> KnowledgeDocument:
        self.session.add(document)
        await self.session.flush()
        return document

    async def list_for_user(
        self,
        user_id: str,
        project_id: str | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        statement = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)
        if project_id is not None:
            statement = statement.where(KnowledgeDocument.project_id == project_id)
        result = await self.session.execute(
            statement.order_by(KnowledgeDocument.created_at.desc(), KnowledgeDocument.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def get_for_user(self, document_id: str, user_id: str) -> KnowledgeDocument | None:
        result = await self.session.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.id == document_id,
                KnowledgeDocument.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def search_candidates(
        self,
        user_id: str,
        terms: list[str],
        project_id: str | None = None,
        limit: int = 20,
    ) -> list[KnowledgeDocument]:
        statement = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)
        if project_id is not None:
            statement = statement.where(
                or_(
                    KnowledgeDocument.project_id == project_id,
                    KnowledgeDocument.project_id.is_(None),
                )
            )
        unique_terms = list(dict.fromkeys(terms))[:12]
        if unique_terms:
            conditions = []
            for term in unique_terms:
                pattern = f"%{term[:100]}%"
                conditions.extend(
                    [
                        KnowledgeDocument.title.ilike(pattern),
                        KnowledgeDocument.content.ilike(pattern),
                    ]
                )
            statement = statement.where(or_(*conditions))
        result = await self.session.execute(
            statement.order_by(KnowledgeDocument.created_at.desc()).limit(limit)
        )
        return list(result.scalars())

    async def delete(self, document: KnowledgeDocument) -> None:
        await self.session.delete(document)


class AuditRepository(SqlRepository):
    async def add(self, event: AuditEvent) -> AuditEvent:
        self.session.add(event)
        await self.session.flush()
        return event
