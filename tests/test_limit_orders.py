from datetime import datetime

import pytest

from slipstream.broker import Broker
from slipstream.types import Bar, Order, OrderType

TS = datetime(2024, 1, 3)


def bar(open_, high, low, close):
    return Bar(TS, open_, high, low, close, volume=1000)


def test_limit_and_stop_orders_require_a_price():
    with pytest.raises(ValueError):
        Order("AAPL", 10, OrderType.LIMIT)
    with pytest.raises(ValueError):
        Order("AAPL", 10, OrderType.STOP)


def test_a_market_order_rejects_a_price():
    with pytest.raises(ValueError):
        Order("AAPL", 10, OrderType.MARKET, price=100)


def test_buy_limit_fills_when_the_bar_dips_to_it():
    broker = Broker()
    broker.submit(Order("AAPL", 10, OrderType.LIMIT, price=99))
    assert broker.execute({"AAPL": bar(101, 102, 100, 101)}) == []   # never traded down
    (fill,) = broker.execute({"AAPL": bar(101, 101, 98, 100)})       # low pierced 99
    assert fill.price == 99


def test_buy_limit_takes_a_better_open():
    broker = Broker()
    broker.submit(Order("AAPL", 10, OrderType.LIMIT, price=100))
    (fill,) = broker.execute({"AAPL": bar(97, 99, 96, 98)})
    assert fill.price == 97  # opened below the limit, filled there


def test_sell_limit_fills_when_the_bar_rallies_to_it():
    broker = Broker()
    broker.submit(Order("AAPL", -10, OrderType.LIMIT, price=105))
    assert broker.execute({"AAPL": bar(101, 104, 100, 103)}) == []
    (fill,) = broker.execute({"AAPL": bar(103, 106, 102, 105)})
    assert fill.price == 105


def test_buy_stop_triggers_on_a_breakout():
    broker = Broker()
    broker.submit(Order("AAPL", 10, OrderType.STOP, price=110))
    assert broker.execute({"AAPL": bar(101, 108, 100, 107)}) == []
    (fill,) = broker.execute({"AAPL": bar(108, 112, 107, 111)})
    assert fill.price == 110  # max(open 108, stop 110)


def test_cancel_removes_a_pending_order():
    broker = Broker()
    order = broker.submit(Order("AAPL", 10, OrderType.LIMIT, price=90))
    assert broker.cancel(order.id) is True
    assert broker.pending == []
    assert broker.cancel(order.id) is False
