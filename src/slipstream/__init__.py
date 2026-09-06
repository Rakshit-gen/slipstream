"""An event-driven backtester for bar-based trading strategies."""

from .broker import Broker
from .costs import (
    FixedBps,
    NoCommission,
    NoSlippage,
    PercentOfValue,
    PerShare,
    PerTrade,
    VolumeShare,
)
from .csv_data import load_csv, load_csv_feed
from .engine import Engine
from .feed import BarFeed
from .portfolio import Portfolio
from .report import format_report
from .result import BacktestResult
from .strategy import Context, Strategy
from .types import Bar, Fill, Order, OrderType, Side

__version__ = "0.1.0"

__all__ = [
    "Bar",
    "BacktestResult",
    "BarFeed",
    "Broker",
    "Context",
    "Engine",
    "Fill",
    "FixedBps",
    "NoCommission",
    "NoSlippage",
    "Order",
    "OrderType",
    "PerShare",
    "PerTrade",
    "PercentOfValue",
    "Portfolio",
    "Side",
    "Strategy",
    "VolumeShare",
    "format_report",
    "load_csv",
    "load_csv_feed",
]
