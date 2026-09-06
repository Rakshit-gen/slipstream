import pytest

from slipstream.csv_data import load_csv, load_csv_feed

GOOD = """Date,Open,High,Low,Close,Volume
2024-01-02,100,102,99,101,15000
2024-01-03,101,103,100,102.5,16000
2024-01-04,102.5,104,101,103,17000
"""


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_loads_ohlcv_rows(tmp_path):
    bars = load_csv(write(tmp_path, "aapl.csv", GOOD))
    assert len(bars) == 3
    assert bars[0].close == 101
    assert bars[1].volume == 16000
    assert [b.timestamp.day for b in bars] == [2, 3, 4]


def test_rows_are_sorted_even_if_the_file_is_not(tmp_path):
    shuffled = "date,open,high,low,close\n2024-01-04,1,1,1,1\n2024-01-02,1,1,1,1\n"
    bars = load_csv(write(tmp_path, "x.csv", shuffled))
    assert [b.timestamp.day for b in bars] == [2, 4]


def test_volume_is_optional(tmp_path):
    text = "date,open,high,low,close\n2024-01-02,10,10,10,10\n"
    assert load_csv(write(tmp_path, "x.csv", text))[0].volume == 0.0


def test_adj_close_is_accepted_as_close(tmp_path):
    text = "Date,Open,High,Low,Adj Close\n2024-01-02,10,11,9,10.5\n"
    assert load_csv(write(tmp_path, "x.csv", text))[0].close == 10.5


def test_missing_a_price_column_is_an_error(tmp_path):
    text = "date,open,high,close\n2024-01-02,10,11,10.5\n"
    with pytest.raises(ValueError, match="missing columns"):
        load_csv(write(tmp_path, "x.csv", text))


def test_a_bad_row_names_its_line_number(tmp_path):
    text = "date,open,high,low,close\n2024-01-02,10,11,9,10\n2024-01-03,x,11,9,10\n"
    with pytest.raises(ValueError, match="line 3"):
        load_csv(write(tmp_path, "x.csv", text))


def test_us_style_dates(tmp_path):
    text = "date,open,high,low,close\n01/02/2024,10,10,10,10\n"
    assert load_csv(write(tmp_path, "x.csv", text))[0].timestamp.month == 1


def test_load_feed_keys_by_symbol(tmp_path):
    feed = load_csv_feed(
        {
            "AAPL": write(tmp_path, "a.csv", GOOD),
            "MSFT": write(tmp_path, "m.csv", GOOD),
        }
    )
    assert set(feed.symbols) == {"AAPL", "MSFT"}
    assert len(list(feed)) == 3
