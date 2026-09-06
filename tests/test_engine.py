from slipstream.engine import Engine
from slipstream.feed import BarFeed
from slipstream.strategies import BuyAndHold
from slipstream.strategy import Strategy
from support import bars, const_bars


class DoNothing(Strategy):
    def on_bar(self, context):
        pass


class BuyOnce(Strategy):
    def __init__(self, symbol, shares):
        self.symbol = symbol
        self.shares = shares
        self.done = False

    def on_bar(self, context):
        if not self.done:
            context.order(self.symbol, self.shares)
            self.done = True


def test_a_do_nothing_strategy_keeps_equity_flat():
    feed = BarFeed({"AAPL": bars([10, 11, 12, 13])})
    result = Engine(feed, DoNothing(), starting_cash=10_000).run()
    assert len(result.equity_curve) == 4
    assert [round(v, 6) for v in result.equity] == [10_000] * 4


def test_buy_and_hold_tracks_the_underlying():
    feed = BarFeed({"AAPL": bars([100, 110, 120, 130])})
    result = Engine(feed, BuyAndHold(), starting_cash=10_000).run()
    # bought ~100 shares at bar 2's open (== bar 1 close of 100); by the end
    # the position is worth roughly 100 * 130 with the rest in cash.
    assert result.equity[-1] > 12_000
    assert result.fills  # something actually traded


def test_orders_fill_on_the_next_bar_not_the_current_one():
    feed = BarFeed({"AAPL": bars([10, 20, 40])})
    result = Engine(feed, BuyOnce("AAPL", 100), starting_cash=10_000).run()
    assert len(result.fills) == 1
    # order placed looking at bar 0 (close 10), filled at bar 1 open (== 10)
    assert result.fills[0].price == 10


def test_an_order_on_the_final_bar_never_fills():
    feed = BarFeed({"AAPL": const_bars(3, 10)})

    class BuyLate(Strategy):
        def on_bar(self, context):
            if context.now == feed._series["AAPL"][-1].timestamp:
                context.order("AAPL", 10)

    result = Engine(feed, BuyLate(), starting_cash=1_000).run()
    assert result.fills == []
    assert len(result.unfilled_orders) == 1
