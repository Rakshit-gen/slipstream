"""Performance metrics computed from an equity curve.

The ratio metrics all work off the series of per-period simple returns
``r_t = equity_t / equity_{t-1} - 1``. Annualisation multiplies by
``periods_per_year`` (or its square root for volatility); 252 is the default,
i.e. daily bars over trading days.
"""

from __future__ import annotations

import math
from datetime import datetime
from statistics import fmean, pstdev

TRADING_DAYS = 252


def returns(equity: list[float]) -> list[float]:
    return [b / a - 1.0 for a, b in zip(equity, equity[1:]) if a != 0]


def total_return(equity: list[float]) -> float:
    if len(equity) < 2 or equity[0] == 0:
        return 0.0
    return equity[-1] / equity[0] - 1.0


def cagr(equity: list[float], periods_per_year: float = TRADING_DAYS) -> float:
    if len(equity) < 2 or equity[0] <= 0 or equity[-1] <= 0:
        return 0.0
    years = (len(equity) - 1) / periods_per_year
    if years <= 0:
        return 0.0
    return (equity[-1] / equity[0]) ** (1.0 / years) - 1.0


def annualized_volatility(rets: list[float], periods_per_year: float = TRADING_DAYS) -> float:
    if len(rets) < 2:
        return 0.0
    return pstdev(rets) * math.sqrt(periods_per_year)


def sharpe(
    rets: list[float],
    risk_free: float = 0.0,
    periods_per_year: float = TRADING_DAYS,
) -> float:
    if len(rets) < 2:
        return 0.0
    per_period_rf = risk_free / periods_per_year
    excess = [r - per_period_rf for r in rets]
    spread = pstdev(excess)
    if spread == 0:
        return 0.0
    return fmean(excess) / spread * math.sqrt(periods_per_year)


def drawdown_series(equity: list[float]) -> list[float]:
    """Fractional distance below the running peak at each point, <= 0."""
    out: list[float] = []
    peak = equity[0] if equity else 0.0
    for value in equity:
        peak = max(peak, value)
        out.append(value / peak - 1.0 if peak else 0.0)
    return out


def max_drawdown(equity: list[float]) -> float:
    """The worst peak-to-trough drop, as a negative fraction."""
    return min(drawdown_series(equity), default=0.0)


def worst_drawdown_window(equity: list[float]) -> tuple[int, int, int | None, float]:
    """Locate the deepest drawdown: ``(peak_index, trough_index,
    recovery_index or None, depth)``. Depth is a negative fraction; recovery
    is the first point back at the old peak, or None if it never got there.
    """
    if len(equity) < 2:
        return (0, 0, 0 if equity else None, 0.0)
    peak_idx = 0
    best = (0, 0, 0, 0.0)
    for i, value in enumerate(equity):
        if value > equity[peak_idx]:
            peak_idx = i
        drop = value / equity[peak_idx] - 1.0
        if drop < best[3]:
            recovery = next(
                (j for j in range(i, len(equity)) if equity[j] >= equity[peak_idx]),
                None,
            )
            best = (peak_idx, i, recovery, drop)
    return best


def sortino(
    rets: list[float],
    risk_free: float = 0.0,
    periods_per_year: float = TRADING_DAYS,
    target: float = 0.0,
) -> float:
    if len(rets) < 2:
        return 0.0
    per_period_rf = risk_free / periods_per_year
    excess = [r - per_period_rf for r in rets]
    downside = [min(0.0, e - target) for e in excess]
    downside_dev = math.sqrt(fmean(d * d for d in downside))
    if downside_dev == 0:
        return 0.0
    return fmean(excess) / downside_dev * math.sqrt(periods_per_year)


def calmar(equity: list[float], periods_per_year: float = TRADING_DAYS) -> float:
    worst = abs(max_drawdown(equity))
    if worst == 0:
        return 0.0
    return cagr(equity, periods_per_year) / worst


def infer_periods_per_year(timestamps: list[datetime]) -> float:
    """Guess the annualisation factor from the spacing between timestamps:
    daily bars → 252, weekly → 52, monthly → 12, otherwise scale a calendar
    year by the median gap."""
    if len(timestamps) < 3:
        return TRADING_DAYS
    gaps = sorted(
        (b - a).total_seconds()
        for a, b in zip(timestamps, timestamps[1:])
        if b > a
    )
    if not gaps:
        return TRADING_DAYS
    median = gaps[len(gaps) // 2]
    day = 86_400
    if median <= 1.5 * day:
        return TRADING_DAYS
    if median <= 10 * day:
        return 52.0
    if median <= 45 * day:
        return 12.0
    if median <= 135 * day:
        return 4.0
    return 365.25 * day / median
