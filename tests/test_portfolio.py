from datetime import datetime

import pytest

from slipstream.portfolio import Portfolio, Position
from slipstream.types import Fill

TS = datetime(2024, 1, 2)


def fill(symbol, qty, price, commission=0.0):
    return Fill(0, symbol, TS, qty, price, commission)


def test_buying_spends_cash_and_builds_a_position():
    p = Portfolio(10_000)
    p.apply_fill(fill("AAPL", 10, 100))
    assert p.cash == 9_000
    assert p.position("AAPL").quantity == 10
    assert p.equity({"AAPL": 100}) == 10_000


def test_commission_is_a_straight_drain():
    p = Portfolio(10_000)
    p.apply_fill(fill("AAPL", 10, 100, commission=5))
    assert p.cash == 8_995
    assert p.equity({"AAPL": 100}) == 9_995


def test_a_partial_sale_realises_pnl_on_the_closed_part():
    p = Portfolio(10_000)
    p.apply_fill(fill("AAPL", 10, 100))
    p.apply_fill(fill("AAPL", -4, 120))
    pos = p.position("AAPL")
    assert pos.quantity == 6
    assert pos.avg_price == 100
    assert pos.realized_pnl == pytest.approx(80)


def test_selling_through_zero_flips_the_position():
    pos = Position("AAPL", quantity=10, avg_price=100)
    pos.apply(-15, 110)
    assert pos.quantity == -5
    assert pos.avg_price == 110
    assert pos.realized_pnl == pytest.approx(100)


def test_covering_a_short_at_a_lower_price_is_a_gain():
    pos = Position("AAPL", quantity=-10, avg_price=100)
    pos.apply(4, 90)
    assert pos.quantity == -6
    assert pos.realized_pnl == pytest.approx(40)


def test_equity_marks_holdings_at_the_given_prices():
    p = Portfolio(10_000)
    p.apply_fill(fill("AAPL", 10, 100))
    assert p.equity({"AAPL": 130}) == 10_300


def test_gross_exposure_reads_one_when_fully_invested():
    p = Portfolio(10_000)
    p.apply_fill(fill("AAPL", 100, 100))
    assert p.cash == 0
    assert p.gross_exposure({"AAPL": 100}) == pytest.approx(1.0)


def test_starting_cash_must_be_positive():
    with pytest.raises(ValueError):
        Portfolio(0)
