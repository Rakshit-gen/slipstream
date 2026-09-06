# slipstream

An event-driven backtester for bar-based trading strategies. It feeds price
bars through a strategy one timestamp at a time, simulates the fills with
commission and slippage, and reports what the equity curve did.

No dependencies, standard library only. Python 3.10+.

## The model

One timestamp is processed in a fixed order, and that order is the whole
point -- it's what stops a strategy trading on prices it couldn't have seen:

1. **fill** orders the strategy queued on the previous bar, against this
   bar's open (moved by slippage, with commission on top);
2. **observe** -- the strategy's context is refreshed with the current bars
   and the latest closes;
3. **decide** -- `strategy.on_bar(context)` runs and places orders, which
   will fill on the *next* bar;
4. **mark** -- equity and gross exposure are recorded at this bar's closes.

Orders queued on the final bar never fill. Any position still open at the
end is booked at the last mark (at no cost) so the realised trade log lines
up with the equity curve; pass `close_at_end=False` to leave it open.

## Usage

```python
from slipstream import Engine, BarFeed, load_csv, PercentOfValue, FixedBps
from slipstream.strategies import SMACrossover

feed = BarFeed({"AAPL": load_csv("aapl.csv")})
engine = Engine(
    feed,
    SMACrossover("AAPL", fast=20, slow=50),
    starting_cash=100_000,
    commission=PercentOfValue(rate=0.0005),   # 5 bps
    slippage=FixedBps(bps=2),
)
result = engine.run()

print(result.summary())          # return, CAGR, vol, Sharpe, Sortino, drawdown, ...
print(result.trade_stats())      # win rate, profit factor, expectancy
for trade in result.trades:
    print(trade.symbol, trade.pnl, trade.duration)
```

### Writing a strategy

Subclass `Strategy` and implement `on_bar`. The context gives you prices,
positions and cash, and order helpers:

```python
from slipstream import Strategy

class Momentum(Strategy):
    def on_bar(self, context):
        bar = context.bars["AAPL"]
        if bar.close > context.prices.get("AAPL", bar.close):
            context.order_target_percent("AAPL", 1.0)   # go fully long
        else:
            context.order_target("AAPL", 0)             # flat
```

`context.order`, `order_target`, `order_target_percent`, `limit_order`,
`stop_order`, `cancel`. The `slipstream.sizing` module has helpers for
risk-based and volatility-target position sizing.

## CLI

```
slipstream run strategy.py --data AAPL=aapl.csv --cash 100000 \
    --commission pct:0.0005 --slippage bps:5
```

`strategy.py` is a plain module that defines a module-level `strategy`
object or a single `Strategy` subclass. `--commission` takes
`per-trade:F`, `per-share:C` or `pct:R`; `--slippage` takes `bps:N` or
`volume:ETA`. `--json` prints the summary instead of the tearsheet.

## What's modelled

- Market, limit and stop orders; next-bar-open fills; GTC queue with cancel.
- Commission: per-trade, per-share (with a minimum), percent of notional.
- Slippage: fixed basis points, and volume-share price impact.
- Average-cost position accounting, longs and shorts, position flips.
- Metrics: total return, CAGR, annualised volatility, Sharpe, Sortino, max
  drawdown, Calmar, average exposure; trade stats from FIFO-matched round
  trips.

## Tests

```
pip install -e '.[dev]'
pytest
```

## License

MIT
