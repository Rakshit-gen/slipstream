from datetime import datetime, timedelta

import pytest

from slipstream.trades import extract_trades, trade_stats
from slipstream.types import Fill

DAY = timedelta(days=1)
T0 = datetime(2024, 1, 1)


def fill(day, symbol, qty, price, commission=0.0):
    return Fill(0, symbol, T0 + day * DAY, qty, price, commission)


def test_a_simple_long_round_trip():
    trades = extract_trades([fill(0, "AAPL", 10, 100), fill(1, "AAPL", -10, 120)])
    assert len(trades) == 1
    t = trades[0]
    assert t.quantity == 10
    assert t.pnl == pytest.approx(200)
    assert t.return_pct == pytest.approx(0.2)
    assert t.duration == DAY


def test_commission_comes_out_of_pnl():
    trades = extract_trades(
        [fill(0, "AAPL", 10, 100, commission=5), fill(1, "AAPL", -10, 120, commission=5)]
    )
    assert trades[0].pnl == pytest.approx(190)
    assert trades[0].commission == pytest.approx(10)


def test_a_partial_exit_splits_into_two_trades_fifo():
    trades = extract_trades(
        [
            fill(0, "AAPL", 10, 100),
            fill(1, "AAPL", -4, 110),
            fill(2, "AAPL", -6, 90),
        ]
    )
    assert [t.quantity for t in trades] == [4, 6]
    assert trades[0].pnl == pytest.approx(40)
    assert trades[1].pnl == pytest.approx(-60)


def test_a_short_round_trip_makes_money_when_price_falls():
    trades = extract_trades([fill(0, "AAPL", -10, 100), fill(1, "AAPL", 10, 90)])
    assert trades[0].quantity == -10
    assert trades[0].pnl == pytest.approx(100)


def test_an_unclosed_position_produces_no_trade():
    assert extract_trades([fill(0, "AAPL", 10, 100)]) == []


def test_trade_stats_summary():
    trades = extract_trades(
        [
            fill(0, "AAPL", 10, 100),
            fill(1, "AAPL", -10, 130),  # +300
            fill(2, "AAPL", 10, 100),
            fill(3, "AAPL", -10, 90),   # -100
        ]
    )
    stats = trade_stats(trades)
    assert stats["trades"] == 2
    assert stats["win_rate"] == pytest.approx(0.5)
    assert stats["profit_factor"] == pytest.approx(3.0)
    assert stats["expectancy"] == pytest.approx(100)
