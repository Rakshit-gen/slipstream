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
    engine = Engine(feed, DoNothing(), starting_cash=10_000)
    curve = engine.run()
    assert len(curve) == 4
    assert [round(v, 6) for _, v in curve] == [10_000] * 4


def test_buy_and_hold_tracks_the_underlying():
    prices = [100, 110, 120, 130]
    feed = BarFeed({"AAPL": bars(prices)})
    engine = Engine(feed, BuyAndHold(), starting_cash=10_000)
    curve = engine.run()
    # bought ~100 shares at bar 2's open (== bar 1 close of 100); by the end
    # the position is worth roughly 100 * 130 with the rest in cash.
    final = curve[-1][1]
    assert final > 12_000
    assert engine.fills  # something actually traded


def test_orders_fill_on_the_next_bar_not_the_current_one():
    feed = BarFeed({"AAPL": bars([10, 20, 40])})
    engine = Engine(feed, BuyOnce("AAPL", 100), starting_cash=10_000)
    engine.run()
    assert len(engine.fills) == 1
    # order placed looking at bar 0 (close 10), filled at bar 1 open (== 10)
    assert engine.fills[0].price == 10


def test_an_order_on_the_final_bar_never_fills():
    feed = BarFeed({"AAPL": const_bars(3, 10)})

    class BuyLate(Strategy):
        def on_bar(self, context):
            if context.now == feed._series["AAPL"][-1].timestamp:
                context.order("AAPL", 10)

    engine = Engine(feed, BuyLate(), starting_cash=1_000)
    engine.run()
    assert engine.fills == []
    assert len(engine.unfilled_orders) == 1
