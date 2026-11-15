"""Research CLI, append-only forward log, no lookahead and cached golden checks."""

import csv
from datetime import date

import numpy as np
import pandas as pd
import pytest

from backtester.data import binance_wide
from backtester.tools import crypto_flow as tool

MONDAY = pd.Timestamp("2026-01-05", tz="UTC")


def fixture_book():
    index = pd.date_range(MONDAY - pd.Timedelta(days=60), periods=67, freq="D")
    k = {
        f"S{i:02}": pd.DataFrame(
            {
                "open": 100.0,
                "close": 100.0 + i,
                "volume": 100.0,
                "quote_volume": 5e6,
                "taker_buy_volume": float(i),
            },
            index=index,
        )
        for i in range(25)
    }
    f = {"S00": pd.Series([0.0], index=[MONDAY + pd.Timedelta(days=7)])}
    return k, f


def test_weeks_boundaries_completion_and_future_invariance():
    k, f = fixture_book()
    trades, legs = tool.compute_weeks(k, f, date(2026, 1, 1), date(2026, 1, 11))
    assert len(trades) == 1 and len(legs) == 10
    assert trades[0]["n_eligible"] == 25
    assert trades[0]["net_bp"] == pytest.approx(1980)
    assert tool.compute_weeks(k, f, date(2026, 1, 6), date(2026, 1, 11)) == ([], [])
    assert tool.compute_weeks(k, f, date(2026, 1, 1), date(2026, 1, 10)) == ([], [])
    assert tool.compute_weeks(k, f, date(2026, 1, 1)) == (trades, legs)
    lagging = {"S00": pd.Series([0.0], index=[MONDAY + pd.Timedelta(days=5)])}
    assert tool.compute_weeks(k, lagging, date(2026, 1, 1)) == ([], [])
    assert tool.compute_weeks(k, {}, date(2026, 1, 1)) == ([], [])
    for sym in k:
        k[sym].loc[MONDAY + pd.Timedelta(days=8)] = 99999
    f["S00"].loc[MONDAY + pd.Timedelta(days=8)] = 99999
    assert tool.compute_weeks(k, f, date(2026, 1, 1), date(2026, 1, 11)) == (trades, legs)
    # Current/future price changes cannot change the book's member choices/signals.
    for d in k.values():
        d.loc[d.index >= MONDAY, :] = 99999
    _, changed_legs = tool.compute_weeks(k, f, date(2026, 1, 1), date(2026, 1, 11))
    assert [(r["symbol"], r["signal"]) for r in changed_legs] == [
        (r["symbol"], r["signal"]) for r in legs
    ]


def test_never_emit_future_week():
    k, f = fixture_book()
    delta = pd.Timedelta(days=7 * 5200)
    for d in k.values():
        d.index += delta
    f = {"S00": pd.Series([0.0], index=[MONDAY + delta + pd.Timedelta(days=7)])}
    assert tool.compute_weeks(k, f, end=date(2130, 1, 1)) == ([], [])


def test_forward_append_only(tmp_path):
    trades, _ = tool.compute_weeks(*fixture_book(), date(2026, 1, 1), date(2026, 1, 11))
    row = trades[0]
    path = tmp_path / "forward.csv"
    tool.append_forward(path, [row])
    original = path.read_bytes()
    tool.append_forward(path, [dict(row, net_bp=row["net_bp"] + 1e-10)])
    assert path.read_bytes() == original
    new = dict(
        row,
        entry_time=MONDAY + pd.Timedelta(days=7),
        exit_time=MONDAY + pd.Timedelta(days=14, minutes=-1),
    )
    tool.append_forward(path, [row, new])
    assert path.read_bytes().startswith(original)
    existing = path.read_bytes()
    with pytest.raises(ValueError, match="2026-01-05"):
        tool.append_forward(path, [dict(row, r_net=99), new])
    assert path.read_bytes() == existing
    with pytest.raises(ValueError, match="duplicate"):
        tool.append_forward(path, [new, new])
    with pytest.raises(ValueError, match="out-of-order"):
        tool.append_forward(path, [dict(row, entry_time=MONDAY - pd.Timedelta(days=7))])
    path.write_text("bad,columns\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        tool.append_forward(path, [row])


def test_cli_csv_and_forward(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tool, "load", fixture_book)
    monkeypatch.setattr(tool.binance_wide, "update", lambda *a, **kw: pytest.fail("network update"))
    tool.main(["--start", "2026-01-01", "--end", "2026-01-11", "--out", str(tmp_path)])
    with (tmp_path / "trades.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert tuple(rows[0]) == tool.TRADE_COLUMNS
    assert rows[0]["entry_time"] == "2026-01-05T00:00:00+00:00"
    assert rows[0]["exit_time"] == "2026-01-11T23:59:00+00:00"
    assert "mean net 1980.0000 bp" in capsys.readouterr().out
    forward = tmp_path / "forward.csv"
    monkeypatch.setattr(tool, "FORWARD_PATH", forward)
    tool.main(["--forward", "--out", str(tmp_path)])
    assert not forward.exists()  # no complete forward weeks on 2026-11-14
    with pytest.raises(SystemExit):
        tool.main(["--forward", "--start", "2026-01-01"])


@pytest.mark.parametrize(
    "start,end,count,mean,t",
    [
        (date(2020, 1, 1), date(2023, 12, 31), 186, 145.0, 3.24),
        (date(2024, 1, 1), date(2026, 10, 25), 147, 147.2, 3.76),
    ],
)
def test_golden(start, end, count, mean, t):
    if not all(root.is_dir() for root in binance_wide.ROOTS):
        pytest.skip("crypto flow golden requires data/cache/binance_wide and binance_wide_test")
    trades, _ = tool.compute_weeks(*tool.load(), start, end)
    net = np.array([row["net_bp"] for row in trades])
    actual_t = net.mean() / net.std(ddof=1) * np.sqrt(len(net))
    print(f"golden {start}..{end}: n={len(net)} mean={net.mean():.8f} t={actual_t:.8f}")
    assert len(net) == count
    if start.year == 2020:
        assert trades[0]["entry_time"] == pd.Timestamp("2020-05-25", tz="UTC")
    assert abs(net.mean() - mean) < 0.05
    assert abs(actual_t - t) < 0.005


def test_liquid_forward_uses_own_log(tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "load", fixture_book)
    seen = {}
    real = tool.compute_weeks

    def spy(*args, **kwargs):
        seen["config"] = args[4] if len(args) > 4 else kwargs.get("config")
        return real(*args, **kwargs)

    monkeypatch.setattr(tool, "compute_weeks", spy)
    monkeypatch.setattr(tool, "FORWARD_PATH", tmp_path / "full.csv")
    monkeypatch.setattr(tool, "LIQUID_FORWARD_PATH", tmp_path / "top100.csv")
    monkeypatch.setattr(tool, "append_forward", lambda path, rows: seen.setdefault("path", path))
    tool.main(["--forward", "--liquid", "--out", str(tmp_path)])
    assert seen["config"].top_volume == 100
    assert seen["path"] == tmp_path / "top100.csv"


@pytest.mark.parametrize(
    "start,end,count,mean,t",
    [
        (date(2020, 1, 1), date(2023, 12, 31), 186, 171.0, 3.64),
        (date(2024, 1, 1), date(2026, 10, 31), 147, 166.3, 3.06),
    ],
)
def test_golden_liquid(start, end, count, mean, t):
    """FB-017 diagnostic numbers (research/screens/2026-11-15_fb017_liquid_s20.py)."""
    if not all(root.is_dir() for root in binance_wide.ROOTS):
        pytest.skip("crypto flow golden requires data/cache/binance_wide and binance_wide_test")
    trades, _ = tool.compute_weeks(*tool.load(), start, end, tool.LIQUID)
    net = np.array([row["net_bp"] for row in trades])
    assert len(net) == count
    assert abs(net.mean() - mean) < 0.05
    assert abs(net.mean() / net.std(ddof=1) * np.sqrt(len(net)) - t) < 0.005
