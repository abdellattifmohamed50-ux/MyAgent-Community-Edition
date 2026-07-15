from __future__ import annotations

from core.exceptions.base import ValidationError

MAX_MESSAGE_LENGTH = 20_000


def validate_chat_input(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        raise ValidationError("Message cannot be empty")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValidationError("Message is too large")
    return cleaned
