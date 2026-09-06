from datetime import datetime

import pytest

from slipstream.costs import FixedBps, NoSlippage, VolumeShare
from slipstream.types import Bar

BAR = Bar(datetime(2024, 1, 2), 100, 101, 99, 100, volume=10_000)


def test_no_slippage_is_the_identity():
    assert NoSlippage().fill_price(100.0, BAR, 50) == 100.0


def test_fixed_bps_moves_the_price_against_the_trade():
    model = FixedBps(bps=10)  # 0.1%
    assert model.fill_price(100.0, BAR, 5) == pytest.approx(100.1)
    assert model.fill_price(100.0, BAR, -5) == pytest.approx(99.9)


def test_volume_share_impact_scales_with_participation():
    model = VolumeShare(eta=0.5, cap=1.0)
    light = model.fill_price(100.0, BAR, 100)   # 1% of volume
    heavy = model.fill_price(100.0, BAR, 1000)  # 10% of volume
    assert heavy > light > 100.0


def test_volume_share_impact_is_capped():
    model = VolumeShare(eta=10.0, cap=0.02)
    assert model.fill_price(100.0, BAR, 9_000) == pytest.approx(102.0)


def test_volume_share_needs_volume():
    dry = Bar(datetime(2024, 1, 2), 100, 100, 100, 100, volume=0)
    assert VolumeShare().fill_price(100.0, dry, 500) == 100.0
