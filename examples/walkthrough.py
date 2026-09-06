"""Run a couple of strategies over the same synthetic series and print their
tearsheets side by side. No files needed.

    python examples/walkthrough.py
"""

from __future__ import annotations

from datetime import datetime, timedelta

from slipstream import BarFeed, Engine, FixedBps, PercentOfValue, format_report
from slipstream.strategies import BuyAndHold, MeanReversion, SMACrossover
from slipstream.types import Bar

from generate import generate  # examples/ is on the path when run directly


def build_feed(symbol: str = "AAPL", rows: int = 750) -> BarFeed:
    lines = generate(rows, seed=7)[1:]  # drop the header
    bars = []
    for line in lines:
        day, o, h, low, c, v = line.split(",")
        bars.append(
            Bar(datetime.fromisoformat(day), float(o), float(h), float(low), float(c), float(v))
        )
    return BarFeed({symbol: bars})


def main() -> int:
    feed = build_feed()
    strategies = {
        "buy & hold": BuyAndHold(fraction=1.0),
        "sma 20/50": SMACrossover("AAPL", 20, 50),
        "mean reversion": MeanReversion("AAPL", lookback=20, entry_z=-1.0),
    }
    for name, strategy in strategies.items():
        result = Engine(
            feed,
            strategy,
            starting_cash=100_000,
            commission=PercentOfValue(rate=0.0005),
            slippage=FixedBps(bps=2),
        ).run()
        print(format_report(result, name=name))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
