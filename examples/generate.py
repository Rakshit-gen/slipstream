"""Write a synthetic OHLCV CSV so the other examples have something to chew on.

    python examples/generate.py AAPL 750 > aapl.csv

Geometric random walk with a mild drift and a bit of intraday range. Not
meant to be realistic, just well-formed.
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta


def generate(rows: int, *, start_price: float = 100.0, seed: int = 0) -> list[str]:
    rng = random.Random(seed)
    out = ["date,open,high,low,close,volume"]
    day = date(2021, 1, 4)
    price = start_price
    for i in range(rows):
        open_ = price
        price *= 1 + rng.gauss(0.0003, 0.013)
        close = price
        span = abs(rng.gauss(0, 0.004))
        high = max(open_, close) * (1 + span)
        low = min(open_, close) * (1 - span)
        volume = int(rng.uniform(5e5, 5e6))
        out.append(f"{day + timedelta(days=i)},{open_:.2f},{high:.2f},{low:.2f},{close:.2f},{volume}")
    return out


def main(argv: list[str]) -> int:
    name = argv[1] if len(argv) > 1 else "SYNTH"
    rows = int(argv[2]) if len(argv) > 2 else 750
    seed = sum(ord(c) for c in name)
    print("\n".join(generate(rows, seed=seed)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
