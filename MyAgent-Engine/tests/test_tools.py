from __future__ import annotations

import pytest

from core.tools.builtins import CalculatorTool, DateTimeTool, TextStatsTool


@pytest.mark.asyncio
async def test_calculator_operations() -> None:
    result = await CalculatorTool().execute(expression="2 ** 8 + 4")
    assert result.ok
    assert result.output == "260"


@pytest.mark.asyncio
async def test_calculator_rejects_large_exponent() -> None:
    result = await CalculatorTool().execute(expression="2 ** 1000")
    assert not result.ok


@pytest.mark.asyncio
async def test_datetime_tool_uses_utc() -> None:
    result = await DateTimeTool().execute()
    assert result.ok
    assert result.metadata["timezone"] == "UTC"


@pytest.mark.asyncio
async def test_text_stats_handles_empty_input() -> None:
    result = await TextStatsTool().execute(text="")
    assert result.metadata == {"characters": 0, "words": 0, "lines": 1}
