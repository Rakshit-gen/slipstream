"""The small immutable values that flow through a backtest.

A :class:`Bar` is one period of OHLCV data. A strategy turns bars into
:class:`Order` objects; the broker turns filled orders into :class:`Fill`
objects; the portfolio applies fills. Everything here is frozen -- once a
bar or a fill exists it doesn't change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

    @property
    def sign(self) -> int:
        return 1 if self is Side.BUY else -1


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.low > self.high:
            raise ValueError(f"bar low {self.low} is above high {self.high}")
        for name in ("open", "close"):
            price = getattr(self, name)
            if not self.low <= price <= self.high:
                raise ValueError(f"bar {name} {price} outside [{self.low}, {self.high}]")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("bar prices must be positive")


@dataclass(frozen=True)
class Order:
    """A request to change position in *symbol* by *quantity* shares, signed
    (positive buys, negative sells). ``id`` is assigned by the broker."""

    symbol: str
    quantity: float
    type: OrderType = OrderType.MARKET
    price: float | None = None  # limit price for LIMIT, trigger level for STOP
    created_at: datetime | None = None
    id: int = 0

    def __post_init__(self) -> None:
        if self.quantity == 0:
            raise ValueError("order quantity must be non-zero")
        needs_price = self.type in (OrderType.LIMIT, OrderType.STOP)
        if needs_price and self.price is None:
            raise ValueError(f"{self.type.value} order needs a price")
        if not needs_price and self.price is not None:
            raise ValueError("market order takes no price")

    @property
    def side(self) -> Side:
        return Side.BUY if self.quantity > 0 else Side.SELL


@dataclass(frozen=True)
class Fill:
    order_id: int
    symbol: str
    timestamp: datetime
    quantity: float
    price: float
    commission: float = 0.0

    @property
    def value(self) -> float:
        """Signed notional traded, before costs."""
        return self.quantity * self.price

    @property
    def cash_flow(self) -> float:
        """What the account balance does: a buy costs cash, a sell raises it,
        and commission is always a drain."""
        return -self.quantity * self.price - self.commission
