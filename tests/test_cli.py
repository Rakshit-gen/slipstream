import json

import pytest

from slipstream.cli import _commission, _load_strategy, _slippage, main
from slipstream.costs import FixedBps, NoCommission, PercentOfValue

PRICES = """date,open,high,low,close,volume
2024-01-02,100,101,99,100,10000
2024-01-03,100,106,100,105,10000
2024-01-04,105,111,105,110,10000
2024-01-05,110,116,110,115,10000
"""

STRATEGY_FILE = """
from slipstream.strategies import BuyAndHold

class MyStrat(BuyAndHold):
    pass
"""


def test_commission_and_slippage_specs():
    assert isinstance(_commission("none"), NoCommission)
    assert isinstance(_commission("pct:0.001"), PercentOfValue)
    assert _commission("pct:0.001").rate == 0.001
    assert isinstance(_slippage("bps:10"), FixedBps)
    with pytest.raises(ValueError):
        _commission("bogus:1")


def test_load_strategy_finds_a_single_subclass(tmp_path):
    path = tmp_path / "strat.py"
    path.write_text(STRATEGY_FILE)
    from slipstream.strategy import Strategy

    assert isinstance(_load_strategy(path), Strategy)


def test_load_strategy_errors_when_ambiguous(tmp_path):
    path = tmp_path / "strat.py"
    path.write_text(STRATEGY_FILE + "\nclass Other(BuyAndHold):\n    pass\n")
    with pytest.raises(ValueError, match="exactly one"):
        _load_strategy(path)


def test_run_prints_a_report(tmp_path, capsys):
    (tmp_path / "aapl.csv").write_text(PRICES)
    (tmp_path / "strat.py").write_text(STRATEGY_FILE)
    code = main(
        [
            "run",
            str(tmp_path / "strat.py"),
            "--data",
            f"AAPL={tmp_path / 'aapl.csv'}",
            "--cash",
            "10000",
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["end_equity"] > 10_000  # bought into a rising series


def test_run_reports_a_missing_file(capsys):
    code = main(["run", "nope.py", "--data", "AAPL=missing.csv"])
    assert code == 2
    assert "slipstream:" in capsys.readouterr().err
