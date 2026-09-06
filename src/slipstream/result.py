"""What a backtest hands back: the equity curve, the fills, and the metrics
derived from them."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from . import metrics
from .types import Fill, Order


@dataclass
class BacktestResult:
    equity_curve: list[tuple[datetime, float]]
    fills: list[Fill]
    starting_cash: float
    unfilled_orders: list[Order] = field(default_factory=list)
    periods_per_year: float | None = None

    def __post_init__(self) -> None:
        if self.periods_per_year is None:
            self.periods_per_year = metrics.infer_periods_per_year(self.timestamps)

    @property
    def timestamps(self) -> list[datetime]:
        return [ts for ts, _ in self.equity_curve]

    @property
    def equity(self) -> list[float]:
        return [value for _, value in self.equity_curve]

    @property
    def returns(self) -> list[float]:
        return metrics.returns(self.equity)

    @property
    def total_return(self) -> float:
        return metrics.total_return(self.equity)

    @property
    def cagr(self) -> float:
        return metrics.cagr(self.equity, self.periods_per_year)

    @property
    def volatility(self) -> float:
        return metrics.annualized_volatility(self.returns, self.periods_per_year)

    def sharpe(self, risk_free: float = 0.0) -> float:
        return metrics.sharpe(self.returns, risk_free, self.periods_per_year)

    def summary(self) -> dict[str, float]:
        return {
            "start_equity": self.equity[0] if self.equity else self.starting_cash,
            "end_equity": self.equity[-1] if self.equity else self.starting_cash,
            "total_return": self.total_return,
            "cagr": self.cagr,
            "volatility": self.volatility,
            "sharpe": self.sharpe(),
            "trades": len(self.fills),
        }
