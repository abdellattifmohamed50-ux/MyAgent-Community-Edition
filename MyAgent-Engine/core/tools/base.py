from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str
    metadata: dict[str, Any]


class BaseTool(Protocol):
    name: str
    description: str

    async def execute(self, **kwargs: Any) -> ToolResult: ...
