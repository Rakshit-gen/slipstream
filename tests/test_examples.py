import sys
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES))


def test_generate_produces_loadable_bars(tmp_path):
    from generate import generate

    path = tmp_path / "synth.csv"
    path.write_text("\n".join(generate(60, seed=1)))

    from slipstream.csv_data import load_csv

    bars = load_csv(path)
    assert len(bars) == 60
    assert all(bar.low <= bar.close <= bar.high for bar in bars)


def test_walkthrough_runs_clean(capsys):
    import walkthrough

    assert walkthrough.main() == 0
    assert "buy & hold" in capsys.readouterr().out
