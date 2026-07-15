from __future__ import annotations

import re

from pwdlib import PasswordHash

from core.exceptions.base import ValidationError

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hash.verify(password, stored_hash)


def verify_and_update_password(password: str, stored_hash: str) -> tuple[bool, str | None]:
    return password_hash.verify_and_update(password, stored_hash)


def validate_password_strength(password: str) -> None:
    if len(password) < 10:
        raise ValidationError("Password must contain at least 10 characters")
    rules = [
        (r"[A-Z]", "an uppercase letter"),
        (r"[a-z]", "a lowercase letter"),
        (r"\d", "a number"),
        (r"[^A-Za-z0-9]", "a symbol"),
    ]
    missing = [label for pattern, label in rules if re.search(pattern, password) is None]
    if missing:
        raise ValidationError("Password must include " + ", ".join(missing))
