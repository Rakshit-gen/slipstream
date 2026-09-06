"""A few ready-made strategies, useful as examples and as test fixtures."""

from __future__ import annotations

from .strategy import Context, Strategy


class BuyAndHold(Strategy):
    """Put *fraction* of equity into each symbol on the first bar it appears
    and never trade again."""

    def __init__(self, fraction: float | None = None) -> None:
        self.fraction = fraction
        self._bought: set[str] = set()

    def on_bar(self, context: Context) -> None:
        symbols = list(context.bars)
        weight = self.fraction if self.fraction is not None else 1.0 / len(symbols)
        for symbol in symbols:
            if symbol not in self._bought:
                context.order_target_percent(symbol, weight)
                self._bought.add(symbol)
