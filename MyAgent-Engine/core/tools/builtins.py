from __future__ import annotations

import ast
import operator
from datetime import UTC, datetime
from typing import Any, cast

from core.tools.base import ToolResult

_MAX_EXPRESSION_LENGTH = 500
_MAX_AST_NODES = 100
_MAX_AST_DEPTH = 20
_MAX_ABSOLUTE_RESULT = 10**100


class CalculatorTool:
    name = "calculator"
    description = "Evaluate a safe arithmetic expression. Argument: expression."

    async def execute(self, **kwargs: Any) -> ToolResult:
        expression = str(kwargs.get("expression", ""))
        if not expression.strip():
            return ToolResult(False, "Expression is required", {})
        if len(expression) > _MAX_EXPRESSION_LENGTH:
            return ToolResult(False, "Expression is too long", {})
        try:
            tree = ast.parse(expression, mode="eval")
            if sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
                raise ValueError("Expression is too complex")
            value = _evaluate(tree.body)
        except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
            return ToolResult(False, f"Invalid expression: {exc}", {})
        return ToolResult(True, str(value), {"expression": expression})


class DateTimeTool:
    name = "datetime"
    description = "Return the current UTC date and time."

    async def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        now = datetime.now(UTC)
        return ToolResult(True, now.isoformat(), {"timezone": "UTC"})


class TextStatsTool:
    name = "text_stats"
    description = "Count characters, words and lines. Argument: text."

    async def execute(self, **kwargs: Any) -> ToolResult:
        text = str(kwargs.get("text", ""))
        if len(text) > 100_000:
            return ToolResult(False, "Text is too long", {})
        metadata: dict[str, Any] = {
            "characters": len(text),
            "words": len(text.split()),
            "lines": len(text.splitlines()) or 1,
        }
        return ToolResult(True, str(metadata), metadata)


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _evaluate(node: ast.AST, depth: int = 0) -> int | float:
    if depth > _MAX_AST_DEPTH:
        raise ValueError("Expression is too deeply nested")
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int | float)
        and not isinstance(node.value, bool)
    ):
        if abs(node.value) > _MAX_ABSOLUTE_RESULT:
            raise ValueError("Number is too large")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left, depth + 1)
        right = _evaluate(node.right, depth + 1)
        if isinstance(node.op, ast.Pow):
            if abs(right) > 20:
                raise ValueError("Exponent is too large")
            if abs(left) > 10**10:
                raise ValueError("Power base is too large")
        result = cast(int | float, _BINARY_OPERATORS[type(node.op)](left, right))
        if abs(result) > _MAX_ABSOLUTE_RESULT:
            raise ValueError("Result is too large")
        return result
    if isinstance(node, ast.UnaryOp):
        value = _evaluate(node.operand, depth + 1)
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.USub):
            return -value
    raise ValueError("Only arithmetic operations are allowed")
