from datetime import datetime, timedelta

import pytest

from slipstream.result import BacktestResult

DAY = timedelta(days=1)


def curve(values, start=datetime(2024, 1, 1)):
    return [(start + i * DAY, v) for i, v in enumerate(values)]


def test_summary_has_the_headline_numbers():
    result = BacktestResult(curve([100, 105, 103, 110]), fills=[], starting_cash=100)
    s = result.summary()
    assert s["end_equity"] == 110
    assert s["total_return"] == pytest.approx(0.1)
    assert s["trades"] == 0


def test_periods_per_year_is_inferred_from_the_curve_when_not_given():
    daily = BacktestResult(curve([100] * 10), fills=[], starting_cash=100)
    assert daily.periods_per_year == 252


def test_an_empty_curve_falls_back_to_starting_cash():
    result = BacktestResult([], fills=[], starting_cash=5_000)
    s = result.summary()
    assert s["start_equity"] == 5_000
    assert s["end_equity"] == 5_000
