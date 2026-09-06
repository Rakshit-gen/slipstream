"""Turning a flat list of fills into round-trip trades.

A trade is a matched entry and exit for some quantity of one symbol. Fills
are matched FIFO: the oldest open lot is closed first. A fill that reduces a
position emits one trade per lot it eats into; a fill that adds to or opens
a position becomes a new lot.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from .types import Fill


@dataclass(frozen=True)
class Trade:
    symbol: str
    quantity: float  # signed: positive for a long round trip, negative for a short
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    pnl: float  # net of the commission attributed to both legs
    commission: float

    @property
    def return_pct(self) -> float:
        cost = abs(self.quantity) * self.entry_price
        return self.pnl / cost if cost else 0.0

    @property
    def duration(self) -> timedelta:
        return self.exit_time - self.entry_time


@dataclass
class _Lot:
    quantity: float  # signed
    price: float
    time: datetime
    commission_per_share: float


def extract_trades(fills: list[Fill]) -> list[Trade]:
    trades: list[Trade] = []
    open_lots: dict[str, deque[_Lot]] = defaultdict(deque)

    for fill in sorted(fills, key=lambda f: f.timestamp):
        lots = open_lots[fill.symbol]
        remaining = fill.quantity
        commission_per_share = fill.commission / abs(fill.quantity)

        while remaining != 0 and lots and lots[0].quantity * remaining < 0:
            lot = lots[0]
            matched = min(abs(remaining), abs(lot.quantity))
            direction = 1 if lot.quantity > 0 else -1
            gross = (fill.price - lot.price) * matched * direction
            legs = (lot.commission_per_share + commission_per_share) * matched
            trades.append(
                Trade(
                    symbol=fill.symbol,
                    quantity=matched * direction,
                    entry_time=lot.time,
                    exit_time=fill.timestamp,
                    entry_price=lot.price,
                    exit_price=fill.price,
                    pnl=gross - legs,
                    commission=legs,
                )
            )
            lot.quantity -= matched * direction
            remaining += matched * direction
            if lot.quantity == 0:
                lots.popleft()

        if remaining != 0:
            lots.append(_Lot(remaining, fill.price, fill.timestamp, commission_per_share))

    return trades


def trade_stats(trades: list[Trade]) -> dict[str, float]:
    if not trades:
        return {
            "trades": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
        }
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    return {
        "trades": len(trades),
        "win_rate": len(wins) / len(trades),
        "avg_win": gross_win / len(wins) if wins else 0.0,
        "avg_loss": sum(losses) / len(losses) if losses else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss else math.inf,
        "expectancy": sum(t.pnl for t in trades) / len(trades),
    }
