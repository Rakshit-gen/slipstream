"""The strategy interface and the context it trades through.

A strategy subclasses :class:`Strategy` and implements :meth:`on_bar`. Each
step it receives a :class:`Context` exposing the current bars and prices,
its cash and positions, and a few order helpers. Orders placed now are
filled by the broker against the next bar, so nothing here can peek ahead.
"""

from __future__ import annotations

import math
from datetime import datetime

from .broker import Broker
from .portfolio import Portfolio
from .types import Bar, Order, OrderType


class Context:
    def __init__(self, portfolio: Portfolio, broker: Broker) -> None:
        self._portfolio = portfolio
        self._broker = broker
        self.now: datetime | None = None
        self.bars: dict[str, Bar] = {}
        self.prices: dict[str, float] = {}  # last seen close for every symbol

    @property
    def cash(self) -> float:
        return self._portfolio.cash

    def equity(self) -> float:
        return self._portfolio.equity(self.prices)

    def position(self, symbol: str) -> float:
        return self._portfolio.position(symbol).quantity

    def order(self, symbol: str, quantity: float) -> Order | None:
        """Buy (positive) or sell (negative) *quantity* shares. Rounded to a
        whole share; a zero after rounding places nothing."""
        quantity = math.trunc(quantity)
        if quantity == 0:
            return None
        return self._broker.submit(Order(symbol, quantity, created_at=self.now))

    def limit_order(self, symbol: str, quantity: float, price: float) -> Order | None:
        """Buy/sell *quantity* shares only at *price* or better."""
        quantity = math.trunc(quantity)
        if quantity == 0:
            return None
        return self._broker.submit(
            Order(symbol, quantity, OrderType.LIMIT, price, created_at=self.now)
        )

    def stop_order(self, symbol: str, quantity: float, price: float) -> Order | None:
        """A market order that arms once *price* trades through."""
        quantity = math.trunc(quantity)
        if quantity == 0:
            return None
        return self._broker.submit(
            Order(symbol, quantity, OrderType.STOP, price, created_at=self.now)
        )

    def cancel(self, order: Order) -> bool:
        return self._broker.cancel(order.id)

    def order_target(self, symbol: str, target_quantity: float) -> Order | None:
        """Trade to leave the position at *target_quantity* shares."""
        return self.order(symbol, math.trunc(target_quantity) - self.position(symbol))

    def order_target_percent(self, symbol: str, fraction: float) -> Order | None:
        """Trade to leave *symbol* at *fraction* of current equity."""
        price = self.prices.get(symbol)
        if not price:
            return None
        return self.order_target(symbol, self.equity() * fraction / price)


class Strategy:
    """Override :meth:`on_bar`; the other hooks are optional."""

    def initialize(self, context: Context) -> None:
        """Called once before the first bar."""

    def on_bar(self, context: Context) -> None:
        raise NotImplementedError

    def finish(self, context: Context) -> None:
        """Called once after the last bar."""
