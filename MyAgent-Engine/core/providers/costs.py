from __future__ import annotations


class UsageCostEstimator:
    """Converts token usage into integer micro-USD using operator supplied rates.

    Catalog keys may be either ``provider:model`` or ``provider``. Each value
    contains ``input`` and ``output`` USD rates per one million tokens.
    """

    def __init__(self, catalog: dict[str, dict[str, float]]) -> None:
        self.catalog = catalog

    def estimate_microusd(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> int | None:
        rates = self.catalog.get(f"{provider}:{model}") or self.catalog.get(provider)
        if rates is None:
            return None
        # USD / 1M tokens converts directly to micro-USD per token.
        return round(input_tokens * rates["input"] + output_tokens * rates["output"])
