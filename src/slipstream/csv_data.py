"""Load bar series from CSV files.

Expected columns (case-insensitive, any order): a date column named one of
``date`` / ``timestamp`` / ``datetime`` / ``time``, then ``open``, ``high``,
``low``, ``close`` and optionally ``volume``. ``adj close`` is accepted as
the close. Extra columns are ignored. Dates are tried as ISO-8601 and a few
common formats; pass *date_format* to force one.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .feed import BarFeed
from .types import Bar

_ALIASES = {
    "date": "timestamp",
    "timestamp": "timestamp",
    "datetime": "timestamp",
    "time": "timestamp",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "adj close": "close",
    "adj_close": "close",
    "volume": "volume",
    "vol": "volume",
}

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y")


def load_csv(path: str | Path, *, date_format: str | None = None) -> list[Bar]:
    path = Path(path)
    out: list[Bar] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return out
        columns = {
            _ALIASES[name.strip().lower()]: name
            for name in reader.fieldnames
            if name.strip().lower() in _ALIASES
        }
        missing = {"timestamp", "open", "high", "low", "close"} - columns.keys()
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        for lineno, row in enumerate(reader, start=2):
            try:
                volume_text = row.get(columns.get("volume", ""), "") or "0"
                bar = Bar(
                    _parse_date(row[columns["timestamp"]], date_format),
                    float(row[columns["open"]]),
                    float(row[columns["high"]]),
                    float(row[columns["low"]]),
                    float(row[columns["close"]]),
                    float(volume_text),
                )
            except ValueError as exc:
                raise ValueError(f"{path} line {lineno}: {exc}") from exc
            out.append(bar)
    out.sort(key=lambda bar: bar.timestamp)
    return out


def load_csv_feed(paths: dict[str, str | Path], *, date_format: str | None = None) -> BarFeed:
    feed = BarFeed()
    for symbol, path in paths.items():
        feed.add(symbol, load_csv(path, date_format=date_format))
    return feed


def _parse_date(text: str, fmt: str | None) -> datetime:
    text = text.strip()
    if fmt:
        return datetime.strptime(text, fmt)
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for candidate in _DATE_FORMATS:
        try:
            return datetime.strptime(text, candidate)
        except ValueError:
            continue
    raise ValueError(f"unrecognised date {text!r}")
