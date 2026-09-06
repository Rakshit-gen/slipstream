"""The backtest engine: walk the feed, run the strategy, track equity.

Each timestamp is processed in a fixed order:

1. fill any orders the strategy queued on the previous bar, against this
   bar's open (via the broker);
2. refresh the context -- current bars, last-seen prices;
3. call ``strategy.on_bar``, whose orders will fill on the *next* bar;
4. record equity marked at this bar's closes.

Orders queued on the final bar never fill, which is the honest outcome.
"""

from __future__ import annotations

from datetime import datetime

from .broker import Broker
from .costs import CommissionModel, SlippageModel
from .feed import BarFeed
from .portfolio import Portfolio
from .result import BacktestResult
from .strategy import Context, Strategy
from .types import Fill, Order


class Engine:
    def __init__(
        self,
        feed: BarFeed,
        strategy: Strategy,
        *,
        starting_cash: float = 100_000.0,
        commission: CommissionModel | None = None,
        slippage: SlippageModel | None = None,
        periods_per_year: float | None = None,
        close_at_end: bool = True,
    ) -> None:
        self.feed = feed
        self.strategy = strategy
        self.starting_cash = starting_cash
        self.periods_per_year = periods_per_year
        self.close_at_end = close_at_end
        self.portfolio = Portfolio(starting_cash)
        self.broker = Broker(commission, slippage)
        self.context = Context(self.portfolio, self.broker)
        self.equity_curve: list[tuple[datetime, float]] = []
        self.exposure_curve: list[tuple[datetime, float]] = []
        self.fills: list[Fill] = []

    def run(self) -> BacktestResult:
        ctx = self.context
        self.strategy.initialize(ctx)
        for when, bars in self.feed:
            for fill in self.broker.execute(bars):
                self.portfolio.apply_fill(fill)
                self.fills.append(fill)

            ctx.now = when
            ctx.bars = bars
            for symbol, bar in bars.items():
                ctx.prices[symbol] = bar.close

            self.strategy.on_bar(ctx)
            self.equity_curve.append((when, self.portfolio.equity(ctx.prices)))
            self.exposure_curve.append((when, self.portfolio.gross_exposure(ctx.prices)))

        self.strategy.finish(ctx)
        if self.close_at_end and ctx.now is not None:
            self._flatten(ctx.now, ctx.prices)
        return BacktestResult(
            equity_curve=self.equity_curve,
            exposure_curve=self.exposure_curve,
            fills=self.fills,
            starting_cash=self.starting_cash,
            unfilled_orders=self.broker.pending,
            periods_per_year=self.periods_per_year,
        )

    def _flatten(self, when: datetime, prices: dict[str, float]) -> None:
        """Book any position still open at the final mark price, at no cost,
        so the realised trade record lines up with the equity curve."""
        for position in list(self.portfolio.positions.values()):
            if position.quantity == 0:
                continue
            price = prices.get(position.symbol)
            if price is None:
                continue
            closing = Fill(0, position.symbol, when, -position.quantity, price, 0.0)
            self.portfolio.apply_fill(closing)
            self.fills.append(closing)

    @property
    def unfilled_orders(self) -> list[Order]:
        return self.broker.pending
