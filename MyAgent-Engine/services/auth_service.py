from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import Settings
from core.exceptions.base import AuthenticationError, ValidationError
from core.security.jwt import TokenPair, TokenService
from core.security.password import (
    hash_password,
    validate_password_strength,
    verify_and_update_password,
)
from models.entities import AuditEvent, RefreshSession, User
from models.schemas import TokenResponse, UserResponse
from repositories.sql_repositories import (
    AuditRepository,
    RefreshSessionRepository,
    UserRepository,
)

_TIMING_EQUALIZER_HASH = (  # noqa: S105 - fixed non-secret hash equalizes login timing
    "$argon2id$v=19$m=65536,t=3,p=4$zEkQMT/T2uGqSCmmN/ActQ$"
    "dT6XyreV6+R/VzDxTcfjOWexWZ6OSR81/E9LsCSpfCQ"
)


class AuthService:
    """Repository-backed registration, login and rotating refresh-token lifecycle."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.tokens = TokenService(settings)
        self.users = UserRepository(session)
        self.sessions = RefreshSessionRepository(session)
        self.audit = AuditRepository(session)

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        email = email.lower().strip()
        display_name = display_name.strip()
        if len(display_name) < 2:
            raise ValidationError("Display name must contain at least 2 characters")
        if await self.users.get_by_email(email) is not None:
            raise ValidationError("An account with this email already exists")
        validate_password_strength(password)
        user = User(
            id=f"usr_{uuid4().hex}",
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            role="user",
            is_active=True,
        )
        await self.users.add(user)
        pair = self.tokens.create_pair(user.id, [user.role])
        await self._save_refresh_session(pair, user_agent, ip_address)
        await self._record("auth.register", user.id, ip_address)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ValidationError("An account with this email already exists") from exc
        await self.session.refresh(user)
        return self._response(pair, user)

    async def login(
        self,
        email: str,
        password: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        user = await self.users.get_by_email(email.lower().strip())
        if user is None:
            verify_and_update_password(password, _TIMING_EQUALIZER_HASH)
            raise AuthenticationError("Invalid email or password")
        verified, updated_hash = verify_and_update_password(password, user.password_hash)
        if not verified:
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        if updated_hash is not None:
            user.password_hash = updated_hash
        pair = self.tokens.create_pair(user.id, [user.role])
        await self._save_refresh_session(pair, user_agent, ip_address)
        await self._record("auth.login", user.id, ip_address)
        await self.session.commit()
        return self._response(pair, user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = self.tokens.decode(refresh_token, expected_type="refresh")
        session_id = str(payload.get("sid", ""))
        refresh_session = await self.sessions.get(session_id)
        if refresh_session is None or refresh_session.revoked_at is not None:
            raise AuthenticationError("Refresh session is not active")
        now = datetime.now(UTC)
        if refresh_session.expires_at.replace(tzinfo=UTC) <= now:
            raise AuthenticationError("Refresh session has expired")
        subject = str(payload.get("sub", ""))
        if not subject or subject != refresh_session.user_id:
            raise AuthenticationError("Refresh token does not match its session")
        current_fingerprint = self.tokens.fingerprint(refresh_token)
        if refresh_session.token_hash != current_fingerprint:
            raise AuthenticationError("Refresh token reuse was detected")
        user = await self.users.get(refresh_session.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Account is unavailable")
        pair = self.tokens.create_pair(user.id, [user.role], session_id=session_id)
        rotated = await self.sessions.rotate_if_active(
            session_id,
            current_fingerprint,
            self.tokens.fingerprint(pair.refresh_token),
            pair.refresh_expires_at,
            now,
        )
        if not rotated:
            await self.session.rollback()
            raise AuthenticationError("Refresh token reuse was detected")
        await self._record("auth.refresh", user.id, None)
        await self.session.commit()
        return self._response(pair, user)

    async def logout(self, refresh_token: str) -> None:
        payload = self.tokens.decode(refresh_token, expected_type="refresh")
        refresh_session = await self.sessions.get(str(payload.get("sid", "")))
        if refresh_session is not None and refresh_session.revoked_at is None:
            await self.sessions.revoke(refresh_session, datetime.now(UTC))
            await self._record("auth.logout", refresh_session.user_id, None)
            await self.session.commit()

    async def _save_refresh_session(
        self,
        pair: TokenPair,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        payload = self.tokens.decode(pair.refresh_token, expected_type="refresh")
        await self.sessions.add(
            RefreshSession(
                id=pair.session_id,
                user_id=str(payload["sub"]),
                token_hash=self.tokens.fingerprint(pair.refresh_token),
                expires_at=pair.refresh_expires_at,
                user_agent=self._bounded(user_agent, 500),
                ip_address=self._bounded(ip_address, 64),
            )
        )

    async def _record(
        self,
        event_type: str,
        user_id: str | None,
        ip_address: str | None,
    ) -> None:
        await self.audit.add(
            AuditEvent(
                id=f"audit_{uuid4().hex}",
                user_id=user_id,
                event_type=event_type,
                details=json.dumps({"source": "api"}),
                ip_address=self._bounded(ip_address, 64),
            )
        )

    @staticmethod
    def _bounded(value: str | None, maximum: int) -> str | None:
        return value[:maximum] if value is not None else None

    @staticmethod
    def _response(pair: TokenPair, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
            user=UserResponse.model_validate(user),
        )
