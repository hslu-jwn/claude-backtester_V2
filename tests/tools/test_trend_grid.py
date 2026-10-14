"""Strategy 4 grid tool: the variants (signal x timeframe + the spec's parameter sweep), the
rows it writes and a smoke run with a stubbed backtest. Spec: strategy-trend-following.md ›
Evaluation (ROADMAP 10.3)."""

from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction, Timeframe
from backtester.strategy.trend_following.config import Signal
from backtester.tools import trend_grid
from backtester.tools.trend_grid import (
    avg_holding_hours,
    half_rows,
    summary_row,
    variant_name,
    variants,
    year_rows,
)

ALL_TF = [Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4, Timeframe.D1]
ALL_SIGNALS = [Signal.BREAKOUT, Signal.SMA, Signal.KAMA]
NEW_SIGNALS = [Signal.MOMENTUM, Signal.DUNNIGAN]


def trade(
    symbol="XAUUSD", year=2021, r_gross=1.0, r_net=0.9, hours=48, direction=Direction.BULLISH
):
    entry = datetime(year, 3, 1, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol,
        direction=direction,
        entry_time=entry,
        exit_time=entry + timedelta(hours=hours),
        r_gross=r_gross,
        r_net=r_net,
        planned_r=None,
    )


def test_default_grid_is_signal_x_timeframe_with_the_spec_parameter_sweep():
    configs = variants(ALL_SIGNALS, ALL_TF, sweep=True)
    names = [variant_name(c) for c in configs]
    assert len(names) == len(set(names)) == 5 * (3 + 4 + 4 + 3)  # per timeframe: 14 sets
    h4 = [c for c in configs if c.timeframe is Timeframe.H4]
    assert sorted(c.breakout_period for c in h4 if c.signal is Signal.BREAKOUT) == [20, 55, 100]
    plain = [c for c in h4 if c.signal is Signal.SMA and c.sma_band_atr == 0]
    assert sorted(c.sma_period for c in plain) == [20, 50, 100, 200]
    banded = {(c.sma_period, c.sma_band_atr) for c in h4 if c.sma_band_atr > 0}
    assert banded == {(50, 0.5), (50, 1.0), (200, 0.5), (200, 1.0)}
    assert sorted(c.kama_filter for c in h4 if c.signal is Signal.KAMA) == [0.0, 0.1, 0.5]


def test_without_sweep_it_is_signal_x_timeframe_at_the_spec_defaults():
    configs = variants(ALL_SIGNALS, ALL_TF, sweep=False)
    assert len(configs) == 15
    one = next(c for c in configs if c.signal is Signal.SMA and c.timeframe is Timeframe.D1)
    assert one.sma_period == 50 and one.stop_atr_mult == 3.0


def test_limits_to_signals_and_timeframes_and_custom_values():
    configs = variants(
        [Signal.BREAKOUT], [Timeframe.H4], sweep=True, breakout=(10, 30), sma=(), kama_filters=()
    )
    assert [variant_name(c) for c in configs] == ["H4 breakout 10", "H4 breakout 30"]


def test_names_show_signal_and_its_parameter():
    configs = variants(ALL_SIGNALS, [Timeframe.H4], sweep=False)
    assert [variant_name(c) for c in configs] == ["H4 breakout 20", "H4 sma 50", "H4 kama 0.1"]


def test_average_holding_time_in_hours():
    assert avg_holding_hours([trade(hours=24), trade(hours=72)]) == 48.0
    assert avg_holding_hours([]) is None


def test_summary_row_has_the_reported_columns():
    trades = [trade(r_gross=2.0, r_net=1.8), trade(r_gross=-1.0, r_net=-1.1, hours=24)]
    row = summary_row("H4 breakout 20", "ALL", trades)
    assert row["trades"] == 2 and row["win_rate"] == 0.5
    assert row["avg_r_gross"] == pytest.approx(0.5) and row["avg_r_net"] == pytest.approx(0.35)
    assert row["sum_r_gross"] == pytest.approx(1.0) and row["sum_r_net"] == pytest.approx(0.7)
    assert row["profit_factor"] == pytest.approx(1.8 / 1.1)
    assert row["max_dd_r_net"] == pytest.approx(1.1)
    assert row["avg_hold_hours"] == 36.0


def test_halves_split_at_the_end_of_2022():
    trades = [
        trade(year=2022, r_net=1.0),
        trade(year=2023, r_net=-2.0),
        trade(year=2026, r_net=0.5),
    ]
    rows = {r["half"]: r for r in half_rows("v", "ALL", trades)}
    assert rows["2020-22"]["trades"] == 1 and rows["2020-22"]["sum_r_net"] == pytest.approx(1.0)
    assert rows["2023-26"]["trades"] == 2 and rows["2023-26"]["sum_r_net"] == pytest.approx(-1.5)


def test_year_rows_per_year_and_symbol_group():
    trades = [trade(year=2021), trade(year=2021, symbol="US500"), trade(year=2022)]
    rows = year_rows("v", trades)
    got = {(r["year"], r["symbol"]): r["trades"] for r in rows}
    assert got[("2021", "ALL")] == 2 and got[("2021", "US500")] == 1 and got[("2022", "ALL")] == 1


def test_smoke_run_writes_the_three_csv_files(tmp_path, monkeypatch, capsys):
    calls = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        calls.append((tuple(symbols), settings.strategy))
        trades = (trade(year=2021, r_net=1.0), trade(year=2024, r_net=-0.5))
        runs = {s: SimpleNamespace(trades=trades) for s in symbols}
        return SimpleNamespace(trades=trades * len(symbols), runs=runs)

    monkeypatch.setattr(trend_grid, "run_backtests", fake_run)
    out = tmp_path / "grid"
    code = trend_grid.main(
        ["--symbols", "XAUUSD", "--timeframes", "H4", "--signals", "breakout", "sma",
         "--no-sweep", "--out", str(out)]
    )  # fmt: skip
    assert code == 0
    assert [c[1].signal for c in calls] == [Signal.BREAKOUT, Signal.SMA]
    for name in ("summary.csv", "by_year.csv", "split.csv"):
        with (out / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    with (out / "summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["variant"] for r in rows} == {"H4 breakout 20", "H4 sma 50"}
    assert {r["symbol"] for r in rows} == {"ALL", "XAUUSD"}
    text = capsys.readouterr().out
    assert "H4 breakout 20" in text and "swap" in text.lower()


def test_new_signals_are_swept_as_in_the_spec_with_readable_names():
    configs = variants(NEW_SIGNALS, [Timeframe.H4], sweep=True)
    assert [variant_name(c) for c in configs] == [
        "H4 momentum 5", "H4 momentum 20", "H4 momentum 63", "H4 momentum 252", "H4 dunnigan",
    ]  # fmt: skip
    sma = [c for c in variants([Signal.SMA], [Timeframe.H4]) if c.sma_band_atr > 0]
    assert [variant_name(c) for c in sma] == [
        "H4 sma 50 b0.5", "H4 sma 50 b1", "H4 sma 200 b0.5", "H4 sma 200 b1",
    ]  # fmt: skip


def test_without_sweep_the_new_signals_run_at_their_defaults():
    configs = variants([*ALL_SIGNALS, *NEW_SIGNALS], [Timeframe.H4], sweep=False)
    assert [variant_name(c) for c in configs] == [
        "H4 breakout 20", "H4 sma 50", "H4 kama 0.1", "H4 momentum 20", "H4 dunnigan",
    ]  # fmt: skip
    assert all(c.sma_band_atr == 0 for c in configs)


def test_cli_signals_filter_accepts_the_new_names(tmp_path, monkeypatch):
    calls = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        calls.append(settings.strategy)
        return SimpleNamespace(trades=(), runs={s: SimpleNamespace(trades=()) for s in symbols})

    monkeypatch.setattr(trend_grid, "run_backtests", fake_run)
    argv = ["--symbols", "XAUUSD", "--timeframes", "H1", "--signals", "momentum", "dunnigan",
            "--momentum-periods", "5", "63", "--out", str(tmp_path)]  # fmt: skip
    assert trend_grid.main(argv) == 0
    assert [(c.signal, c.momentum_period) for c in calls] == [
        (Signal.MOMENTUM, 5),
        (Signal.MOMENTUM, 63),
        (Signal.DUNNIGAN, 20),
    ]
