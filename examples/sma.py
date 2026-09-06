"""A 20/50 moving-average crossover, ready for `slipstream run`.

    python examples/generate.py AAPL 750 > aapl.csv
    slipstream run examples/sma.py --data AAPL=aapl.csv --slippage bps:2
"""

from slipstream.strategies import SMACrossover

strategy = SMACrossover("AAPL", fast=20, slow=50, fraction=0.95)
