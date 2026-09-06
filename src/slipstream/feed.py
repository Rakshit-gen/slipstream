"""Turning per-symbol bar series into one chronological stream.

The engine walks time forward once, and at each timestamp it wants every
symbol that has a bar there. A :class:`BarFeed` holds one series per symbol
and merges them on the way out.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime

from .types import Bar


class BarFeed:
    def __init__(self, series: Mapping[str, Iterable[Bar]] | None = None) -> None:
        self._series: dict[str, list[Bar]] = {}
        for symbol, bars in (series or {}).items():
            self.add(symbol, bars)

    def add(self, symbol: str, bars: Iterable[Bar]) -> None:
        ordered = sorted(bars, key=lambda bar: bar.timestamp)
        for earlier, later in zip(ordered, ordered[1:]):
            if earlier.timestamp == later.timestamp:
                raise ValueError(f"{symbol} has two bars at {later.timestamp}")
        self._series[symbol] = ordered

    @property
    def symbols(self) -> list[str]:
        return list(self._series)

    def __len__(self) -> int:
        return sum(len(series) for series in self._series.values())

    def __iter__(self) -> Iterator[tuple[datetime, dict[str, Bar]]]:
        # A plain k-way merge by scanning the cursor heads. k is the symbol
        # count, which is small; not worth a heap.
        cursors = dict.fromkeys(self._series, 0)
        while True:
            heads = [
                self._series[symbol][i]
                for symbol, i in cursors.items()
                if i < len(self._series[symbol])
            ]
            if not heads:
                return
            when = min(bar.timestamp for bar in heads)
            group: dict[str, Bar] = {}
            for symbol, i in cursors.items():
                series = self._series[symbol]
                if i < len(series) and series[i].timestamp == when:
                    group[symbol] = series[i]
                    cursors[symbol] = i + 1
            yield when, group
