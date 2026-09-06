from datetime import datetime

import pytest

from slipstream.broker import Broker
from slipstream.costs import FixedBps, PerTrade
from slipstream.types import Bar, Order

TS = datetime(2024, 1, 3)
BAR = Bar(TS, open=100, high=105, low=99, close=104, volume=10_000)


def test_submit_assigns_incrementing_ids():
    broker = Broker()
    first = broker.submit(Order("AAPL", 10))
    second = broker.submit(Order("AAPL", -5))
    assert (first.id, second.id) == (1, 2)
    assert len(broker.pending) == 2


def test_a_market_order_fills_at_the_next_open():
    broker = Broker()
    broker.submit(Order("AAPL", 10))
    (fill,) = broker.execute({"AAPL": BAR})
    assert fill.price == 100
    assert fill.quantity == 10
    assert fill.timestamp == TS
    assert broker.pending == []


def test_slippage_and_commission_are_applied():
    broker = Broker(commission=PerTrade(1.0), slippage=FixedBps(bps=50))
    broker.submit(Order("AAPL", 10))
    (fill,) = broker.execute({"AAPL": BAR})
    assert fill.price == pytest.approx(100.5)  # +50 bps on a buy
    assert fill.commission == 1.0


def test_an_order_without_a_bar_stays_queued():
    broker = Broker()
    broker.submit(Order("MSFT", 10))
    assert broker.execute({"AAPL": BAR}) == []
    assert len(broker.pending) == 1
    assert broker.execute({"MSFT": BAR}) != []
