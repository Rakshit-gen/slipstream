import pytest

from slipstream.engine import Engine
from slipstream.feed import BarFeed
from slipstream.strategies import MeanReversion, SMACrossover
from support import bars


def test_sma_crossover_rejects_a_bad_window_pair():
    with pytest.raises(ValueError):
        SMACrossover("AAPL", fast=50, slow=20)


def test_sma_crossover_goes_long_in_an_uptrend_and_exits_the_reversal():
    # 30 bars up, then 30 down
    prices = list(range(50, 110)) + list(range(110, 50, -1))
    feed = BarFeed({"AAPL": bars(prices)})
    strategy = SMACrossover("AAPL", fast=5, slow=15, fraction=0.9)
    result = Engine(feed, strategy, starting_cash=100_000).run()

    assert len(result.fills) >= 2  # at least one entry and one exit
    assert result.fills[0].quantity > 0  # first trade is a buy
    # it should have given back less than a naive buy-and-hold of the round trip
    assert result.equity[-1] > 90_000


def test_mean_reversion_buys_the_dips():
    # a sawtooth: drops then recovers, repeatedly
    leg = [100, 96, 92, 96, 100, 104, 100, 96, 92, 96, 100]
    feed = BarFeed({"AAPL": bars(leg * 4)})
    strategy = MeanReversion("AAPL", lookback=5, entry_z=-1.0)
    result = Engine(feed, strategy, starting_cash=100_000).run()

    assert result.fills
    assert result.fills[0].quantity > 0  # entries are buys


def test_mean_reversion_rejects_a_non_negative_entry_z():
    with pytest.raises(ValueError):
        MeanReversion("AAPL", entry_z=0.5)
