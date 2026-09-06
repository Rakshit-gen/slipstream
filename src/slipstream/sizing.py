"""Position sizing helpers: pure functions that turn a view into a whole
share count. A strategy calls one of these and passes the result to
``context.order_target``.
"""

from __future__ import annotations

import math


def fraction_of_equity(equity: float, price: float, fraction: float) -> int:
    """Put *fraction* of equity into the name at *price*."""
    if price <= 0:
        return 0
    return math.trunc(equity * fraction / price)


def risk_based(equity: float, price: float, stop_price: float, risk_fraction: float) -> int:
    """Size the position so that being stopped out (price moving from *price*
    to *stop_price*) costs *risk_fraction* of equity."""
    per_share_risk = abs(price - stop_price)
    if per_share_risk == 0:
        return 0
    return math.trunc(equity * risk_fraction / per_share_risk)


def volatility_target(
    equity: float,
    price: float,
    annual_vol: float,
    target_vol: float,
    max_leverage: float = 1.0,
) -> int:
    """Scale exposure so the position's annualised volatility is about
    *target_vol*, never levering past *max_leverage*."""
    if annual_vol <= 0 or price <= 0:
        return 0
    weight = min(max_leverage, target_vol / annual_vol)
    return math.trunc(equity * weight / price)
