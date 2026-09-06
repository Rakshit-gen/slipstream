"""A plain-text tearsheet for a backtest result."""

from __future__ import annotations

import math

from .result import BacktestResult

_SPARK_TICKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float], width: int = 60) -> str:
    if not values:
        return ""
    if len(values) > width:
        step = len(values) / width
        values = [values[int(i * step)] for i in range(width)]
    low, high = min(values), max(values)
    if high == low:
        return _SPARK_TICKS[0] * len(values)
    scale = len(_SPARK_TICKS) - 1
    return "".join(
        _SPARK_TICKS[round((value - low) / (high - low) * scale)] for value in values
    )


def _pct(value: float) -> str:
    return f"{value:.2%}"


def _num(value: float) -> str:
    if math.isinf(value):
        return "inf"
    return f"{value:.2f}"


def format_report(result: BacktestResult, name: str = "strategy") -> str:
    summary = result.summary()
    stats = result.trade_stats()
    rows = [
        ("Start equity", f"{summary['start_equity']:,.2f}"),
        ("End equity", f"{summary['end_equity']:,.2f}"),
        ("Total return", _pct(summary["total_return"])),
        ("CAGR", _pct(summary["cagr"])),
        ("Volatility", _pct(summary["volatility"])),
        ("Sharpe", _num(summary["sharpe"])),
        ("Sortino", _num(summary["sortino"])),
        ("Max drawdown", _pct(summary["max_drawdown"])),
        ("Calmar", _num(summary["calmar"])),
        ("Avg exposure", _pct(summary["avg_exposure"])),
        ("Round trips", str(stats["trades"])),
        ("Win rate", _pct(stats["win_rate"])),
        ("Profit factor", _num(stats["profit_factor"])),
        ("Expectancy", _num(stats["expectancy"])),
    ]

    lines = [name, "=" * len(name)]
    if result.timestamps:
        start, end = result.timestamps[0], result.timestamps[-1]
        lines.append(f"{start:%Y-%m-%d} .. {end:%Y-%m-%d}  ({len(result.equity)} bars)")
    lines.append("")
    for label, value in rows:
        lines.append(f"{label:<16}{value:>16}")
    worst = result.worst_drawdown()
    if worst["peak"] is not None and worst["depth"] < 0:
        recovered = worst["recovered"]
        tail = f"{recovered:%Y-%m-%d}" if recovered is not None else "not recovered"
        lines.append("")
        lines.append(
            f"worst drawdown {_pct(worst['depth'])}: "
            f"{worst['peak']:%Y-%m-%d} -> {worst['trough']:%Y-%m-%d} -> {tail}"
        )

    if result.equity:
        lines += ["", "equity", sparkline(result.equity)]
    return "\n".join(lines)
