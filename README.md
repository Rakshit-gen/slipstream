# slipstream

An event-driven backtester for bar-based trading strategies. Feeds price
bars through a strategy one timestamp at a time, simulates the fills with
commission and slippage, and reports what the equity curve did.

No dependencies, standard library only. Python 3.10+.

Status: early. See `tests/` for what actually works.

## License

MIT
