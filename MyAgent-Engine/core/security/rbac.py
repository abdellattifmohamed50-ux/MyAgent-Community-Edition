from __future__ import annotations

from enum import StrEnum

from core.exceptions.base import AuthorizationError


class Role(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


ROLE_RANK: dict[Role, int] = {Role.USER: 1, Role.DEVELOPER: 2, Role.ADMIN: 3}


def require_role(user_roles: list[str], required: Role) -> None:
    best = max((ROLE_RANK.get(Role(role), 0) for role in user_roles if role in Role), default=0)
    if best < ROLE_RANK[required]:
        raise AuthorizationError(f"Role {required.value} required")
