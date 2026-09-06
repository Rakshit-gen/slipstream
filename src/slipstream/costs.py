"""Trading cost models.

A commission model turns a trade (signed quantity, fill price) into a cash
fee. They're small callables wrapped in classes so a backtest can be handed
one by configuration. Slippage models live here too and are added alongside.
"""

from __future__ import annotations

from typing import Protocol


class CommissionModel(Protocol):
    def calculate(self, quantity: float, price: float) -> float: ...


class NoCommission:
    def calculate(self, quantity: float, price: float) -> float:
        return 0.0


class PerTrade:
    """A flat fee per fill, regardless of size."""

    def __init__(self, fee: float = 1.0) -> None:
        self.fee = fee

    def calculate(self, quantity: float, price: float) -> float:
        return self.fee


class PerShare:
    """A rate per share with a per-fill minimum, the way many US brokers
    price it. *cents_per_share* is in cents."""

    def __init__(self, cents_per_share: float = 0.5, minimum: float = 1.0) -> None:
        self.per_share = cents_per_share / 100.0
        self.minimum = minimum

    def calculate(self, quantity: float, price: float) -> float:
        return max(self.minimum, abs(quantity) * self.per_share)


class PercentOfValue:
    """A fraction of the traded notional. *rate* 0.0005 is 5 basis points."""

    def __init__(self, rate: float = 0.0005, minimum: float = 0.0) -> None:
        self.rate = rate
        self.minimum = minimum

    def calculate(self, quantity: float, price: float) -> float:
        return max(self.minimum, abs(quantity * price) * self.rate)
