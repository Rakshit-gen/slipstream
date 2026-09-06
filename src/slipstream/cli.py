"""Command-line runner.

    slipstream run my_strategy.py --data AAPL=aapl.csv --cash 100000 \\
        --commission pct:0.0005 --slippage bps:5

The strategy file is a plain Python module that either defines a module-level
``strategy`` object or exactly one :class:`~slipstream.strategy.Strategy`
subclass (instantiated with no arguments).
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path

from .costs import (
    FixedBps,
    NoCommission,
    NoSlippage,
    PercentOfValue,
    PerShare,
    PerTrade,
    VolumeShare,
)
from .csv_data import load_csv_feed
from .engine import Engine
from .report import format_report
from .strategy import Strategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slipstream")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a strategy over CSV data")
    run.add_argument("strategy", help="path to a Python file defining the strategy")
    run.add_argument(
        "--data",
        action="append",
        default=[],
        metavar="SYMBOL=PATH",
        help="a CSV per symbol (repeatable); PATH alone uses the file stem as the symbol",
    )
    run.add_argument("--cash", type=float, default=100_000.0)
    run.add_argument("--commission", default="none", metavar="none|per-trade:F|per-share:C|pct:R")
    run.add_argument("--slippage", default="none", metavar="none|bps:N|volume:ETA")
    run.add_argument("--json", action="store_true", help="print the summary as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        feed = load_csv_feed(dict(_parse_data(args.data)))
        strategy = _load_strategy(Path(args.strategy))
        engine = Engine(
            feed,
            strategy,
            starting_cash=args.cash,
            commission=_commission(args.commission),
            slippage=_slippage(args.slippage),
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"slipstream: {exc}", file=sys.stderr)
        return 2

    result = engine.run()
    if args.json:
        print(json.dumps(result.summary(), indent=2, default=str))
    else:
        print(format_report(result, name=Path(args.strategy).stem))
    return 0


def _parse_data(specs: list[str]) -> list[tuple[str, str]]:
    if not specs:
        raise ValueError("no --data given")
    out = []
    for spec in specs:
        symbol, sep, path = spec.partition("=")
        if not sep:
            path = spec
            symbol = Path(spec).stem.upper()
        out.append((symbol, path))
    return out


def _load_strategy(path: Path) -> Strategy:
    if not path.exists():
        raise FileNotFoundError(f"strategy file {path} not found")
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if isinstance(getattr(module, "strategy", None), Strategy):
        return module.strategy
    subclasses = [
        obj
        for obj in vars(module).values()
        if inspect.isclass(obj)
        and issubclass(obj, Strategy)
        and obj.__module__ == module.__name__
    ]
    if len(subclasses) == 1:
        return subclasses[0]()
    raise ValueError(
        f"{path}: define a module-level `strategy` object or exactly one Strategy subclass"
    )


def _commission(spec: str):
    kind, _, value = spec.partition(":")
    if kind in ("none", ""):
        return NoCommission()
    if kind == "per-trade":
        return PerTrade(float(value or 1.0))
    if kind == "per-share":
        return PerShare(float(value or 0.5))
    if kind == "pct":
        return PercentOfValue(float(value or 0.0005))
    raise ValueError(f"unknown commission spec {spec!r}")


def _slippage(spec: str):
    kind, _, value = spec.partition(":")
    if kind in ("none", ""):
        return NoSlippage()
    if kind == "bps":
        return FixedBps(float(value or 5.0))
    if kind == "volume":
        return VolumeShare(float(value or 0.1))
    raise ValueError(f"unknown slippage spec {spec!r}")


if __name__ == "__main__":
    raise SystemExit(main())
