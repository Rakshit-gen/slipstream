"""Shared test helpers: cheap synthetic bar series."""

from __future__ import annotations

from datetime import datetime, timedelta

from slipstream.types import Bar

START = datetime(2024, 1, 1)


def bars(closes, *, start=START, step=timedelta(days=1), spread=0.0):
    """A bar series from a list of closing prices. Each bar opens at the
    previous close (the first opens at its own close) and the high/low sit
    *spread* fraction either side."""
    out = []
    prev = closes[0]
    for i, close in enumerate(closes):
        open_ = prev
        hi = max(open_, close) * (1 + spread)
        lo = min(open_, close) * (1 - spread)
        out.append(Bar(start + i * step, open_, hi, lo, close, volume=1_000_000))
        prev = close
    return out


def const_bars(n, price, **kw):
    return bars([price] * n, **kw)
