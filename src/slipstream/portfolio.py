"""Cash, open positions, and what the account is worth at a set of prices.

Positions use average-cost accounting: adding to a position rolls the
average entry price, reducing it realises PnL on the closed part, and
trading through zero closes the old side and opens the new one fresh.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .types import Fill


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0

    def market_value(self, price: float) -> float:
        return self.quantity * price

    def unrealized_pnl(self, price: float) -> float:
        return (price - self.avg_price) * self.quantity

    def apply(self, delta: float, price: float) -> None:
        quantity = self.quantity
        if quantity == 0 or (quantity > 0) == (delta > 0):
            # opening, or adding in the direction we already hold
            new_quantity = quantity + delta
            self.avg_price = (
                (quantity * self.avg_price + delta * price) / new_quantity
                if new_quantity != 0
                else 0.0
            )
            self.quantity = new_quantity
            return

        # delta works against the position: realise PnL on the overlap
        closed = min(abs(delta), abs(quantity))
        direction = 1 if quantity > 0 else -1
        self.realized_pnl += (price - self.avg_price) * closed * direction
        self.quantity = quantity + delta
        if abs(delta) > abs(quantity):
            self.avg_price = price  # position flipped; remainder opens here
        elif self.quantity == 0:
            self.avg_price = 0.0


class Portfolio:
    def __init__(self, starting_cash: float) -> None:
        if starting_cash <= 0:
            raise ValueError("starting cash must be positive")
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.positions: dict[str, Position] = {}

    def position(self, symbol: str) -> Position:
        return self.positions.setdefault(symbol, Position(symbol))

    def apply_fill(self, fill: Fill) -> None:
        self.cash += fill.cash_flow
        self.position(fill.symbol).apply(fill.quantity, fill.price)

    def holdings_value(self, prices: Mapping[str, float]) -> float:
        return sum(
            pos.market_value(prices[pos.symbol])
            for pos in self.positions.values()
            if pos.quantity != 0
        )

    def equity(self, prices: Mapping[str, float]) -> float:
        return self.cash + self.holdings_value(prices)

    def gross_exposure(self, prices: Mapping[str, float]) -> float:
        """Sum of absolute position values over equity -- 1.0 is fully
        invested, >1 is levered."""
        gross = sum(
            abs(pos.market_value(prices[pos.symbol]))
            for pos in self.positions.values()
            if pos.quantity != 0
        )
        equity = self.equity(prices)
        return gross / equity if equity else 0.0

    def realized_pnl(self) -> float:
        return sum(pos.realized_pnl for pos in self.positions.values())
