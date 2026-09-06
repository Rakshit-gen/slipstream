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
    ) -> None:
        self.feed = feed
        self.strategy = strategy
        self.starting_cash = starting_cash
        self.portfolio = Portfolio(starting_cash)
        self.broker = Broker(commission, slippage)
        self.context = Context(self.portfolio, self.broker)
        self.equity_curve: list[tuple[datetime, float]] = []
        self.fills: list[Fill] = []

    def run(self) -> list[tuple[datetime, float]]:
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

        self.strategy.finish(ctx)
        return self.equity_curve

    @property
    def unfilled_orders(self) -> list[Order]:
        return self.broker.pending
