from datetime import datetime, timedelta

import pytest

from slipstream.feed import BarFeed
from slipstream.types import Bar
from support import bars

DAY = timedelta(days=1)


def test_empty_feed_yields_nothing():
    assert list(BarFeed()) == []


def test_single_symbol_comes_out_in_time_order():
    feed = BarFeed({"AAPL": bars([10, 11, 12])})
    stamps = [ts for ts, _ in feed]
    assert stamps == sorted(stamps)
    assert len(stamps) == 3


def test_unsorted_input_is_sorted_on_the_way_in():
    series = bars([10, 11, 12])
    feed = BarFeed({"AAPL": [series[2], series[0], series[1]]})
    closes = [group["AAPL"].close for _, group in feed]
    assert closes == [10, 11, 12]


def test_two_bars_at_the_same_timestamp_is_an_error():
    ts = datetime(2024, 1, 1)
    with pytest.raises(ValueError):
        BarFeed({"AAPL": [Bar(ts, 10, 10, 10, 10), Bar(ts, 11, 11, 11, 11)]})


def test_symbols_are_grouped_by_timestamp():
    feed = BarFeed({"AAPL": bars([10, 11, 12]), "MSFT": bars([20, 21, 22])})
    groups = list(feed)
    assert len(groups) == 3
    for _, group in groups:
        assert set(group) == {"AAPL", "MSFT"}


def test_a_symbol_that_starts_late_only_appears_once_it_has_bars():
    early = bars([10, 11, 12])
    late = bars([20, 21], start=datetime(2024, 1, 2))
    feed = BarFeed({"AAPL": early, "MSFT": late})
    seen = [(ts, set(group)) for ts, group in feed]
    assert seen[0][1] == {"AAPL"}
    assert seen[1][1] == {"AAPL", "MSFT"}
    assert seen[2][1] == {"AAPL", "MSFT"}
