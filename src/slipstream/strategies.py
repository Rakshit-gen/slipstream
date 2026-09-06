"""A few ready-made strategies, useful as examples and as test fixtures."""

from __future__ import annotations

from collections import deque
from statistics import fmean, pstdev

from .strategy import Context, Strategy


class BuyAndHold(Strategy):
    """Put *fraction* of equity into each symbol on the first bar it appears
    and never trade again. With no *fraction*, splits equity evenly."""

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


class SMACrossover(Strategy):
    """Long a single symbol while its fast moving average sits above the slow
    one, flat otherwise."""

    def __init__(
        self,
        symbol: str,
        fast: int = 20,
        slow: int = 50,
        fraction: float = 0.95,
    ) -> None:
        if fast >= slow:
            raise ValueError("fast window must be shorter than slow")
        self.symbol = symbol
        self.fast = fast
        self.slow = slow
        self.fraction = fraction
        self._closes: deque[float] = deque(maxlen=slow)

    def on_bar(self, context: Context) -> None:
        bar = context.bars.get(self.symbol)
        if bar is None:
            return
        self._closes.append(bar.close)
        if len(self._closes) < self.slow:
            return
        closes = list(self._closes)
        fast_ma = fmean(closes[-self.fast :])
        slow_ma = fmean(closes)
        holding = context.position(self.symbol) != 0
        if fast_ma > slow_ma and not holding:
            context.order_target_percent(self.symbol, self.fraction)
        elif fast_ma <= slow_ma and holding:
            context.order_target(self.symbol, 0)


class MeanReversion(Strategy):
    """Long a single symbol when its close is *entry_z* standard deviations or
    more below its rolling mean; exit once it climbs back to the mean."""

    def __init__(
        self,
        symbol: str,
        lookback: int = 20,
        entry_z: float = -1.0,
        fraction: float = 0.95,
    ) -> None:
        if entry_z >= 0:
            raise ValueError("entry_z should be negative (a dip below the mean)")
        self.symbol = symbol
        self.lookback = lookback
        self.entry_z = entry_z
        self.fraction = fraction
        self._closes: deque[float] = deque(maxlen=lookback)

    def on_bar(self, context: Context) -> None:
        bar = context.bars.get(self.symbol)
        if bar is None:
            return
        self._closes.append(bar.close)
        if len(self._closes) < self.lookback:
            return
        closes = list(self._closes)
        mean = fmean(closes)
        spread = pstdev(closes)
        if spread == 0:
            return
        z = (bar.close - mean) / spread
        holding = context.position(self.symbol) != 0
        if z <= self.entry_z and not holding:
            context.order_target_percent(self.symbol, self.fraction)
        elif z >= 0 and holding:
            context.order_target(self.symbol, 0)
