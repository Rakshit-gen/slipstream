from datetime import datetime

from slipstream.broker import Broker
from slipstream.portfolio import Portfolio
from slipstream.strategy import Context

TS = datetime(2024, 1, 2)


def make_context(cash=10_000, prices=None):
    portfolio = Portfolio(cash)
    broker = Broker()
    ctx = Context(portfolio, broker)
    ctx.now = TS
    ctx.prices = {"AAPL": 100.0} if prices is None else prices
    return ctx, portfolio, broker


def test_order_rounds_to_whole_shares():
    ctx, _, broker = make_context()
    ctx.order("AAPL", 10.9)
    assert broker.pending[0].quantity == 10


def test_a_zero_order_places_nothing():
    ctx, _, broker = make_context()
    assert ctx.order("AAPL", 0.4) is None
    assert broker.pending == []


def test_order_target_trades_the_difference():
    ctx, portfolio, broker = make_context()
    portfolio.position("AAPL").quantity = 30
    ctx.order_target("AAPL", 50)
    assert broker.pending[0].quantity == 20


def test_order_target_percent_sizes_off_equity():
    ctx, _, broker = make_context(cash=10_000, prices={"AAPL": 100.0})
    ctx.order_target_percent("AAPL", 0.5)
    # half of 10k equity / $100 = 50 shares
    assert broker.pending[0].quantity == 50


def test_order_target_percent_without_a_price_does_nothing():
    ctx, _, broker = make_context(prices={})
    assert ctx.order_target_percent("AAPL", 0.5) is None
    assert broker.pending == []
