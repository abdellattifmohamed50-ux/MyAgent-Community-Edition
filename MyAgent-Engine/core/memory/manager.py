from __future__ import annotations

from dataclasses import dataclass

from core.providers.base import ProviderMessage
from models.entities import Message


@dataclass(frozen=True)
class MemoryPolicy:
    recent_message_limit: int = 30
    character_limit: int = 60_000
    summary_trigger: int = 40
    summary_max_chars: int = 4_000


class ConversationMemory:
    """Builds bounded short memory and a deterministic long-memory summary."""

    def __init__(self, policy: MemoryPolicy) -> None:
        self.policy = policy

    def recent_context(self, history: list[Message]) -> list[ProviderMessage]:
        selected: list[ProviderMessage] = []
        used = 0
        for item in reversed(history[-self.policy.recent_message_limit :]):
            if item.role not in {"user", "assistant"}:
                continue
            remaining = self.policy.character_limit - used
            if remaining <= 0:
                break
            content = item.content if len(item.content) <= remaining else item.content[-remaining:]
            selected.append(ProviderMessage(role=item.role, content=content))
            used += len(content)
        selected.reverse()
        return selected

    def summarize(self, history: list[Message], previous_summary: str = "") -> str:
        if len(history) <= self.policy.summary_trigger:
            return previous_summary
        older = history[: -self.policy.recent_message_limit]
        new_lines = [
            f"{item.role}: {' '.join(item.content.split())[:600]}"
            for item in older
            if item.role in {"user", "assistant"}
        ]
        previous_lines = [line for line in previous_summary.splitlines() if line]
        summary = "\n".join(dict.fromkeys([*previous_lines, *new_lines]))
        if len(summary) > self.policy.summary_max_chars:
            summary = summary[-self.policy.summary_max_chars :]
            first_break = summary.find("\n")
            if first_break >= 0:
                summary = summary[first_break + 1 :]
        return summary
