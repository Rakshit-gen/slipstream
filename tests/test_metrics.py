import math
from datetime import datetime, timedelta

import pytest

from slipstream import metrics


def test_returns_series():
    assert metrics.returns([100, 110, 99]) == pytest.approx([0.1, -0.1])


def test_total_return():
    assert metrics.total_return([100, 150]) == pytest.approx(0.5)
    assert metrics.total_return([100]) == 0.0


def test_cagr_of_a_doubling_over_one_year():
    equity = [100.0] * 253
    equity[-1] = 200.0
    # 252 periods == 1 year, so CAGR ~ 100%
    assert metrics.cagr(equity, periods_per_year=252) == pytest.approx(1.0, rel=1e-6)


def test_volatility_of_a_flat_curve_is_zero():
    assert metrics.annualized_volatility([0.0, 0.0, 0.0]) == 0.0


def test_sharpe_scales_with_the_annualisation_factor():
    rets = [0.001, 0.002, -0.001, 0.0015, 0.0005] * 20
    daily = metrics.sharpe(rets, periods_per_year=252)
    weekly = metrics.sharpe(rets, periods_per_year=52)
    assert daily > weekly > 0
    assert daily == pytest.approx(weekly * math.sqrt(252 / 52))


def test_sharpe_is_zero_without_variation():
    assert metrics.sharpe([0.01, 0.01, 0.01]) == 0.0


def test_max_drawdown_is_the_worst_peak_to_trough():
    # 100 -> 120 -> 90 -> 130: worst drop is 120 -> 90 = -25%
    assert metrics.max_drawdown([100, 120, 90, 130]) == pytest.approx(-0.25)


def test_max_drawdown_of_a_monotonic_curve_is_zero():
    assert metrics.max_drawdown([100, 101, 102, 103]) == 0.0


def test_sortino_ignores_upside_volatility():
    # all-positive returns => no downside => zero by convention
    assert metrics.sortino([0.01, 0.02, 0.015]) == 0.0
    mixed = metrics.sortino([0.02, -0.01, 0.03, -0.005] * 20)
    assert mixed != 0.0


def test_calmar_is_cagr_over_max_drawdown():
    equity = [100.0] * 253
    equity[100] = 80.0  # a 20% drawdown partway through
    equity[-1] = 110.0
    expected = metrics.cagr(equity) / 0.2
    assert metrics.calmar(equity) == pytest.approx(expected)


@pytest.mark.parametrize(
    "step, expected",
    [
        (timedelta(days=1), 252),
        (timedelta(days=7), 52),
        (timedelta(days=30), 12),
    ],
)
def test_infer_periods_per_year(step, expected):
    stamps = [datetime(2024, 1, 1) + i * step for i in range(10)]
    assert metrics.infer_periods_per_year(stamps) == expected
