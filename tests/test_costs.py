import pytest

from slipstream.costs import NoCommission, PercentOfValue, PerShare, PerTrade


def test_no_commission():
    assert NoCommission().calculate(100, 50) == 0.0


def test_per_trade_is_flat():
    model = PerTrade(fee=2.5)
    assert model.calculate(1, 10) == 2.5
    assert model.calculate(1000, 10) == 2.5


def test_per_share_respects_the_minimum():
    model = PerShare(cents_per_share=1.0, minimum=1.0)
    assert model.calculate(10, 50) == 1.0  # 10c would be below the floor
    assert model.calculate(500, 50) == pytest.approx(5.0)


def test_per_share_ignores_trade_direction():
    model = PerShare(cents_per_share=1.0, minimum=0.0)
    assert model.calculate(300, 50) == model.calculate(-300, 50)


def test_percent_of_value_is_basis_points_of_notional():
    model = PercentOfValue(rate=0.0005)
    assert model.calculate(100, 20) == pytest.approx(1.0)  # 5bps of 2000
    assert model.calculate(-100, 20) == pytest.approx(1.0)
