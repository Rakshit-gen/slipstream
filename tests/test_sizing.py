import pytest

from slipstream import sizing


def test_fraction_of_equity():
    assert sizing.fraction_of_equity(10_000, price=100, fraction=0.5) == 50
    assert sizing.fraction_of_equity(10_000, price=0, fraction=0.5) == 0


def test_risk_based_sizes_off_the_stop_distance():
    # 1% of 10k = $100 of risk, $2 per share to the stop => 50 shares
    assert sizing.risk_based(10_000, price=50, stop_price=48, risk_fraction=0.01) == 50


def test_risk_based_with_no_stop_distance_is_zero():
    assert sizing.risk_based(10_000, price=50, stop_price=50, risk_fraction=0.01) == 0


def test_volatility_target_scales_exposure_down_for_a_jumpy_asset():
    calm = sizing.volatility_target(10_000, price=100, annual_vol=0.10, target_vol=0.10)
    jumpy = sizing.volatility_target(10_000, price=100, annual_vol=0.40, target_vol=0.10)
    assert calm == 100  # fully invested
    assert jumpy == 25  # quarter weight


def test_volatility_target_respects_max_leverage():
    levered = sizing.volatility_target(
        10_000, price=100, annual_vol=0.05, target_vol=0.20, max_leverage=1.5
    )
    assert levered == 150  # capped at 1.5x, not 4x
