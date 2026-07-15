from core.memory.manager import ConversationMemory, MemoryPolicy
from models.entities import Message


def _message(index: int, role: str = "user") -> Message:
    return Message(
        id=f"m{index}",
        conversation_id="c1",
        role=role,
        content=f"event-{index}",
    )


def test_conversation_memory_bounds_recent_context() -> None:
    memory = ConversationMemory(MemoryPolicy(recent_message_limit=3, character_limit=100))
    context = memory.recent_context([_message(index) for index in range(8)])
    assert [item.content for item in context] == ["event-5", "event-6", "event-7"]


def test_conversation_memory_respects_character_budget() -> None:
    memory = ConversationMemory(MemoryPolicy(recent_message_limit=10, character_limit=7))
    context = memory.recent_context([_message(1), _message(2)])
    assert [item.content for item in context] == ["event-2"]


def test_conversation_summary_is_bounded_and_excludes_recent_messages() -> None:
    memory = ConversationMemory(
        MemoryPolicy(
            recent_message_limit=2,
            summary_trigger=3,
            summary_max_chars=100,
        )
    )
    summary = memory.summarize([_message(index) for index in range(5)])
    assert "event-0" in summary
    assert "event-2" in summary
    assert "event-3" not in summary


def test_conversation_summary_rolls_forward_previous_context() -> None:
    memory = ConversationMemory(
        MemoryPolicy(
            recent_message_limit=2,
            summary_trigger=3,
            summary_max_chars=200,
        )
    )
    summary = memory.summarize(
        [_message(index) for index in range(5)],
        "user: durable-earlier-fact",
    )
    assert "durable-earlier-fact" in summary
    assert summary.count("event-0") == 1
