from __future__ import annotations

from core.exceptions.base import ToolExecutionError
from core.tools.base import BaseTool


class ToolRegistry:
    """Registry for built-in and plugin tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ToolExecutionError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolExecutionError(f"Tool not registered: {name}")
        return tool

    def names(self) -> list[str]:
        return sorted(self._tools)

    def all(self) -> list[BaseTool]:
        return [self._tools[name] for name in self.names()]
