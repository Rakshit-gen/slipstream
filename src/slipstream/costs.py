"""Trading cost models.

A commission model turns a trade (signed quantity, fill price) into a cash
fee. They're small callables wrapped in classes so a backtest can be handed
one by configuration. Slippage models live here too and are added alongside.
"""

from __future__ import annotations

from typing import Protocol

from .types import Bar


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


class SlippageModel(Protocol):
    def fill_price(self, price: float, bar: Bar, quantity: float) -> float: ...


# Slippage always works against the trader: a buy fills above the reference
# price, a sell fills below it.


class NoSlippage:
    def fill_price(self, price: float, bar: Bar, quantity: float) -> float:
        return price


class FixedBps:
    """A flat *bps* haircut against the reference price."""

    def __init__(self, bps: float = 5.0) -> None:
        self.fraction = bps / 10_000.0

    def fill_price(self, price: float, bar: Bar, quantity: float) -> float:
        sign = 1 if quantity > 0 else -1
        return price * (1 + self.fraction * sign)


class VolumeShare:
    """Price impact that grows with how much of the bar's volume the order
    takes. ``impact = eta * (|qty| / volume)``, capped, applied against the
    trader. A bar with no volume gets no impact."""

    def __init__(self, eta: float = 0.1, cap: float = 0.05) -> None:
        self.eta = eta
        self.cap = cap

    def fill_price(self, price: float, bar: Bar, quantity: float) -> float:
        if bar.volume <= 0:
            return price
        participation = abs(quantity) / bar.volume
        impact = min(self.cap, self.eta * participation)
        sign = 1 if quantity > 0 else -1
        return price * (1 + impact * sign)
