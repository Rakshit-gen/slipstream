from datetime import datetime, timedelta

from slipstream.report import format_report, sparkline
from slipstream.result import BacktestResult

DAY = timedelta(days=1)


def curve(values):
    return [(datetime(2024, 1, 1) + i * DAY, v) for i, v in enumerate(values)]


def test_sparkline_tracks_direction():
    line = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert line[0] == "▁"
    assert line[-1] == "█"


def test_sparkline_of_a_flat_series_is_one_level():
    assert set(sparkline([5, 5, 5, 5])) == {"▁"}


def test_sparkline_downsamples_long_series():
    assert len(sparkline(list(range(1000)), width=40)) == 40


def test_format_report_mentions_the_headline_metrics():
    result = BacktestResult(curve([100, 110, 105, 130]), fills=[], starting_cash=100)
    text = format_report(result, name="demo")
    assert "demo" in text
    assert "Sharpe" in text
    assert "Total return" in text
    assert "130.00" in text
