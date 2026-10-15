"""Building the spread table from MT5's per-bar spreads. Spec: ROADMAP.md › 6.7."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from backtester.engine.spread_table import SpreadTable
from backtester.tools.spread_table import SpreadCollector, run


def frame(start, spreads):
    """One M1 bar per entry of `spreads`, from `start` (UTC)."""
    ts = [start + timedelta(minutes=i) for i in range(len(spreads))]
    return pd.DataFrame({"ts": pd.DatetimeIndex(ts, tz="UTC"), "spread": spreads})


SUMMER = datetime(2026, 7, 1, 13, 30, tzinfo=UTC)  # 09:30 New York (hour 9)


def test_median_and_p90_per_symbol_year_and_new_york_hour():
    c = SpreadCollector(min_bars=5)
    c.add("XAUUSD", frame(SUMMER, [0.2] * 20 + [0.4] * 10))  # 13:30..13:59 UTC: hour 9 only
    median, _ = c.build("median")
    p90, _ = c.build("p90")
    assert median.values["XAUUSD"][2026][9] == pytest.approx(0.2)
    assert p90.values["XAUUSD"][2026][9] == pytest.approx(0.4)
    assert median.stat == "median" and p90.stat == "p90"


def test_zero_spread_bars_are_not_information():
    c = SpreadCollector(min_bars=5)
    c.add("XAUUSD", frame(SUMMER, [0.0] * 10 + [0.3] * 10))
    table, rows = c.build("median")
    assert table.values["XAUUSD"][2026][9] == pytest.approx(0.3)
    assert rows[0]["bars"] == 20
    assert rows[0]["zero_share"] == pytest.approx(0.5)


def test_cells_with_too_few_bars_are_left_out():
    c = SpreadCollector(min_bars=10)
    c.add("XAUUSD", frame(SUMMER, [0.2] * 5))
    table, _ = c.build("median")
    assert "XAUUSD" not in table.values or not table.values["XAUUSD"]


def test_year_and_hour_come_from_new_york_time_and_chunks_add_up():
    c = SpreadCollector(min_bars=5)
    new_year_eve = datetime(2026, 1, 1, 4, 30, tzinfo=UTC)  # 2025-12-31 23:30 New York
    c.add("US500", frame(new_year_eve, [0.5] * 6))
    c.add("US500", frame(new_year_eve + timedelta(minutes=6), [0.7] * 6))  # a second chunk
    table, _ = c.build("median")
    assert 2025 in table.values["US500"] and 23 in table.values["US500"][2025]
    # 12 bars in hour 23 (23:30..23:41 New York): median of six 0.5 and six 0.7
    assert table.values["US500"][2025][23] == pytest.approx(0.6)


def test_rollover_hour_shows_the_wide_spread():
    c = SpreadCollector(min_bars=5)
    rollover = datetime(2026, 7, 1, 21, 0, tzinfo=UTC)  # 17:00 New York
    c.add("GBPUSD", frame(rollover, [0.0006] * 10))
    c.add("GBPUSD", frame(SUMMER, [0.00003] * 10))
    table, _ = c.build("median")
    assert table.values["GBPUSD"][2026][17] == pytest.approx(0.0006)
    assert table.values["GBPUSD"][2026][9] == pytest.approx(0.00003)


def test_rejects_a_bad_statistic():
    with pytest.raises(ValueError):
        SpreadCollector().build("mean")


# --- the command ------------------------------------------------------------------------------


def fake_frames(symbol, name):
    yield frame(SUMMER, [0.3] * 40 if symbol == "XAUUSD" else [0.5] * 40)


def test_run_writes_both_tables_and_a_coverage_file(tmp_path, capsys):
    code = run(["XAUUSD", "US500"], {"US500": "US500.cash"}, fake_frames, tmp_path, min_bars=10)
    assert code == 0
    for stat in ("median", "p90"):
        table = SpreadTable.from_dict(
            json.loads((tmp_path / f"ftmo_spread_{stat}.json").read_text())
        )
        assert table.stat == stat
        assert table.values["XAUUSD"][2026][9] == pytest.approx(0.3)
        assert table.values["US500"][2026][9] == pytest.approx(0.5)
        assert "US500.cash" in table.note
    assert "XAUUSD" in capsys.readouterr().out
    assert (tmp_path / "coverage.csv").is_file()


def test_run_skips_a_symbol_that_fails_and_says_so(tmp_path, capsys):
    def frames(symbol, name):
        if symbol == "US500":
            raise RuntimeError("no bars")
        yield from fake_frames(symbol, name)

    assert run(["XAUUSD", "US500"], {}, frames, tmp_path, min_bars=10) == 0
    out = capsys.readouterr().out
    assert "US500" in out and "skipped" in out
    table = SpreadTable.from_dict(json.loads((tmp_path / "ftmo_spread_median.json").read_text()))
    assert set(table.values) == {"XAUUSD"}
