from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import uuid4

import jwt
from pydantic import BaseModel

from core.config.settings import Settings
from core.exceptions.base import AuthenticationError


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str
    refresh_expires_at: datetime


class TokenService:
    """Creates, validates and fingerprints short-lived and refresh JWTs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.algorithm = "HS256"

    def create_access_token(self, subject: str, roles: list[str]) -> str:
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self.settings.access_token_expire_minutes)
        payload: dict[str, Any] = {
            "sub": subject,
            "roles": roles,
            "type": "access",
            "jti": uuid4().hex,
            "iat": now,
            "exp": expires,
        }
        return jwt.encode(payload, self.settings.jwt_secret, algorithm=self.algorithm)

    def create_refresh_token(self, subject: str, session_id: str) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        expires = now + timedelta(days=self.settings.refresh_token_expire_days)
        payload: dict[str, Any] = {
            "sub": subject,
            "sid": session_id,
            "type": "refresh",
            "jti": uuid4().hex,
            "iat": now,
            "exp": expires,
        }
        token = jwt.encode(payload, self.settings.jwt_secret, algorithm=self.algorithm)
        return token, expires

    def create_pair(
        self,
        subject: str,
        roles: list[str],
        session_id: str | None = None,
    ) -> TokenPair:
        sid = session_id or f"session_{uuid4().hex}"
        refresh_token, refresh_expires_at = self.create_refresh_token(subject, sid)
        return TokenPair(
            access_token=self.create_access_token(subject, roles),
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_expire_minutes * 60,
            session_id=sid,
            refresh_expires_at=refresh_expires_at,
        )

    def decode(self, token: str, expected_type: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=[self.algorithm],
                options={"require": ["exp", "iat", "jti", "sub", "type"]},
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        if payload.get("type") != expected_type:
            raise AuthenticationError("Invalid token type")
        if not payload.get("sub"):
            raise AuthenticationError("Token subject is missing")
        if expected_type == "refresh" and not payload.get("sid"):
            raise AuthenticationError("Refresh session is missing")
        return payload

    @staticmethod
    def fingerprint(token: str) -> str:
        return sha256(token.encode("utf-8")).hexdigest()
