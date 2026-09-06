"""The broker: holds pending orders and fills them against the next bar.

A backtest must not let a strategy act on a price it couldn't have known.
Orders submitted while the strategy is looking at one bar are queued and
executed against the *next* bar's open, moved by slippage, with commission
charged on top. An order for a symbol that has no bar at the execution step
stays queued.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .costs import CommissionModel, NoCommission, NoSlippage, SlippageModel
from .types import Bar, Fill, Order, OrderType


class Broker:
    def __init__(
        self,
        commission: CommissionModel | None = None,
        slippage: SlippageModel | None = None,
    ) -> None:
        self.commission = commission or NoCommission()
        self.slippage = slippage or NoSlippage()
        self._pending: list[Order] = []
        self._next_id = 1

    def submit(self, order: Order) -> Order:
        stamped = replace(order, id=self._next_id)
        self._next_id += 1
        self._pending.append(stamped)
        return stamped

    @property
    def pending(self) -> list[Order]:
        return list(self._pending)

    def cancel(self, order_id: int) -> bool:
        for i, order in enumerate(self._pending):
            if order.id == order_id:
                del self._pending[i]
                return True
        return False

    def execute(self, bars: Mapping[str, Bar]) -> list[Fill]:
        fills: list[Fill] = []
        still_pending: list[Order] = []
        for order in self._pending:
            bar = bars.get(order.symbol)
            price = None if bar is None else self._execution_price(order, bar)
            if bar is None or price is None:
                still_pending.append(order)
                continue
            commission = self.commission.calculate(order.quantity, price)
            fills.append(
                Fill(order.id, order.symbol, bar.timestamp, order.quantity, price, commission)
            )
        self._pending = still_pending
        return fills

    def _execution_price(self, order: Order, bar: Bar) -> float | None:
        """The price this order fills at against *bar*, or None if the bar
        doesn't reach it. Limit fills are capped at the limit (no slippage);
        market and triggered stop orders take slippage."""
        quantity = order.quantity
        if order.type is OrderType.MARKET:
            return self.slippage.fill_price(bar.open, bar, quantity)

        level = order.price
        assert level is not None  # guaranteed by Order.__post_init__

        if order.type is OrderType.LIMIT:
            if quantity > 0:  # buy limit: fill at or below the limit
                if bar.open <= level:
                    return bar.open
                return level if bar.low <= level else None
            else:  # sell limit: fill at or above the limit
                if bar.open >= level:
                    return bar.open
                return level if bar.high >= level else None

        # STOP: becomes a market order once the level trades through
        if quantity > 0:  # buy stop
            if bar.high >= level:
                return self.slippage.fill_price(max(bar.open, level), bar, quantity)
            return None
        if bar.low <= level:  # sell stop
            return self.slippage.fill_price(min(bar.open, level), bar, quantity)
        return None
