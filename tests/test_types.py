from datetime import datetime

import pytest

from slipstream.types import Bar, Fill, Order, OrderType, Side

TS = datetime(2024, 1, 2)


def test_side_sign():
    assert Side.BUY.sign == 1
    assert Side.SELL.sign == -1


def test_a_well_formed_bar_is_accepted():
    bar = Bar(TS, open=10.0, high=11.0, low=9.5, close=10.5, volume=1000)
    assert bar.close == 10.5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"open": 10, "high": 9, "low": 8, "close": 8.5},  # high below low
        {"open": 10, "high": 11, "low": 9, "close": 12},  # close above high
        {"open": 8, "high": 11, "low": 9, "close": 10},  # open below low
        {"open": 10, "high": 11, "low": -1, "close": 10},  # negative price
    ],
)
def test_a_corrupt_bar_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Bar(TS, **kwargs)


def test_order_side_follows_the_sign_of_quantity():
    assert Order("AAPL", 10).side is Side.BUY
    assert Order("AAPL", -10).side is Side.SELL
    assert Order("AAPL", 10).type is OrderType.MARKET


def test_a_zero_quantity_order_is_rejected():
    with pytest.raises(ValueError):
        Order("AAPL", 0)


def test_fill_cash_flow_and_value():
    buy = Fill(1, "AAPL", TS, quantity=10, price=100.0, commission=1.0)
    assert buy.value == 1000.0
    assert buy.cash_flow == -1001.0

    sell = Fill(2, "AAPL", TS, quantity=-10, price=100.0, commission=1.0)
    assert sell.value == -1000.0
    assert sell.cash_flow == 999.0
