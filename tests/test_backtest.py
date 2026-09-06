"""End-to-end backtests that lean on the whole stack at once."""

import pytest

from slipstream.costs import PercentOfValue
from slipstream.engine import Engine
from slipstream.feed import BarFeed
from slipstream.strategies import BuyAndHold
from slipstream.strategy import Strategy
from support import bars

RISING = [100, 101, 103, 102, 105, 108, 107, 110, 114, 120]


def run(strategy, prices=RISING, **kw):
    return Engine(BarFeed({"AAPL": bars(prices)}), strategy, starting_cash=100_000, **kw).run()


def test_buy_and_hold_matches_the_underlying_return_without_costs():
    result = run(BuyAndHold(fraction=1.0))
    # entered at bar 1 open (== 100), rode it to 120: about +20%, minus the
    # small cash drag from buying whole shares.
    underlying = RISING[-1] / RISING[0] - 1
    assert result.total_return == pytest.approx(underlying, abs=0.01)


def test_a_strategy_that_never_trades_is_perfectly_flat():
    class Idle(Strategy):
        def on_bar(self, context):
            pass

    result = run(Idle(), prices=[50] * 20)
    assert result.total_return == 0.0
    assert result.volatility == 0.0
    assert result.sharpe() == 0.0
    assert result.trades == []


def test_costs_only_ever_reduce_the_return():
    free = run(BuyAndHold(fraction=1.0))
    costly = run(BuyAndHold(fraction=1.0), commission=PercentOfValue(rate=0.002))
    assert costly.total_return < free.total_return


def test_perfect_foresight_beats_buy_and_hold():
    prices = [100, 90, 110, 95, 130, 105, 150]

    class Oracle(Strategy):
        """Hold only into the bars that are about to rise."""

        def __init__(self):
            self.step = -1

        def on_bar(self, context):
            self.step += 1
            nxt = self.step + 1
            going_up = nxt < len(prices) and prices[nxt] > prices[self.step]
            context.order_target_percent("AAPL", 1.0 if going_up else 0.0)

    oracle = run(Oracle(), prices=prices)
    hold = run(BuyAndHold(fraction=1.0), prices=prices)
    assert oracle.total_return > hold.total_return


def test_a_backtest_is_deterministic():
    a = run(BuyAndHold(fraction=0.8))
    b = run(BuyAndHold(fraction=0.8))
    assert a.equity == b.equity
    assert [f.price for f in a.fills] == [f.price for f in b.fills]
