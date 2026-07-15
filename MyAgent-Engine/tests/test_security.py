from __future__ import annotations

import jwt
import pytest

from core.config.settings import Settings
from core.exceptions.base import AuthenticationError, ValidationError
from core.security.jwt import TokenService
from core.security.password import hash_password, validate_password_strength, verify_password


def _settings() -> Settings:
    return Settings(
        ENVIRONMENT="testing",
        JWT_SECRET="jwt-test-secret-with-at-least-32-characters",
        SECRET_KEY="app-test-secret-with-at-least-32-characters",
    )


def test_password_hash_roundtrip() -> None:
    password_hash = hash_password("StrongPass123!")
    assert password_hash != "StrongPass123!"
    assert verify_password("StrongPass123!", password_hash)
    assert not verify_password("WrongPass123!", password_hash)


def test_password_strength_rules() -> None:
    validate_password_strength("StrongPass123!")
    with pytest.raises(ValidationError):
        validate_password_strength("onlylowercase")


def test_access_token_roundtrip() -> None:
    service = TokenService(_settings())
    token = service.create_access_token("usr_1", ["admin"])
    payload = service.decode(token, "access")
    assert payload["sub"] == "usr_1"
    assert payload["roles"] == ["admin"]


def test_refresh_token_cannot_be_used_as_access_token() -> None:
    service = TokenService(_settings())
    token, _ = service.create_refresh_token("usr_1", "session_1")
    with pytest.raises(AuthenticationError, match="Invalid token type"):
        service.decode(token, "access")


def test_token_fingerprint_is_deterministic() -> None:
    assert TokenService.fingerprint("token") == TokenService.fingerprint("token")
    assert TokenService.fingerprint("token") != TokenService.fingerprint("other")


def test_signed_token_missing_mandatory_claims_is_rejected() -> None:
    settings = _settings()
    token = jwt.encode(
        {"sub": "usr_1", "type": "access"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError, match="Invalid or expired token"):
        TokenService(settings).decode(token, "access")


def test_refresh_token_without_session_is_rejected() -> None:
    settings = _settings()
    service = TokenService(settings)
    access = service.create_access_token("usr_1", ["user"])
    payload = jwt.decode(
        access,
        settings.jwt_secret,
        algorithms=["HS256"],
    )
    payload["type"] = "refresh"
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(AuthenticationError, match="Refresh session is missing"):
        service.decode(token, "refresh")
