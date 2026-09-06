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
from .types import Bar, Fill, Order


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

    def execute(self, bars: Mapping[str, Bar]) -> list[Fill]:
        fills: list[Fill] = []
        still_pending: list[Order] = []
        for order in self._pending:
            bar = bars.get(order.symbol)
            if bar is None:
                still_pending.append(order)
                continue
            price = self.slippage.fill_price(bar.open, bar, order.quantity)
            commission = self.commission.calculate(order.quantity, price)
            fills.append(
                Fill(order.id, order.symbol, bar.timestamp, order.quantity, price, commission)
            )
        self._pending = still_pending
        return fills
