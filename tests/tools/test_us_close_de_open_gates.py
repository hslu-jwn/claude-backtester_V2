import csv
import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics.entry_screen import M1Data
from backtester.tools import us_close_de_open_gates as g

START, END = date(2015, 1, 2), date(2020, 6, 14)


def trade(day, value=1., direction="long", spread=0., symbol="GER40"):
    dt = datetime.fromisoformat(day).replace(tzinfo=UTC)
    return SimpleNamespace(entry_time=dt, exit_time=dt + timedelta(minutes=30),
                           direction=direction, symbol=symbol, r_net=value,
                           r_gross=value + spread, spread_r=spread, commission_r=0.,
                           swap_r=0., funding_r=0., conversion_r=0.)


def cell(family="S", threshold="0.1", stop="0.5", exit_time="09:30", direction=None):
    s = {"family": family, "stop_atr": stop, "exit_time": exit_time}
    s.update({"min_ref_return_pct": threshold} if family == "S" else {"direction": direction})
    return s


def test_primary_and_fixed_halves():
    assert g.is_primary(cell())
    assert not g.is_primary(cell(threshold="0.2"))
    a, b = trade("2017-10-07T08:00", 2), trade("2017-10-08T08:00", 3)
    assert g.report([a, b], START, END)["halves_net_r"] == [2, 3]


def test_weighted_control_dates_and_determinism():
    signal = [trade(f"2019-03-{d:02}T08:00", 2, "long" if d < 4 else "short") for d in range(1, 5)]
    longs = [trade("2019-03-01T08:00", 100), trade("2019-03-08T08:00", 1)]
    shorts = [trade("2019-03-09T08:00", -1, "short")]
    result = g.control_difference(signal, longs, shorts)
    assert result["difference"] == pytest.approx(1.5)
    assert result["control_long_trades"] == 1
    assert (result["n_long"], result["n_short"]) == (3, 1)
    assert result == g.control_difference(signal, longs, shorts)


def test_missing_controls_breadth_and_skip():
    variants = {"s": {"settings": cell(), "trades": [trade("2019-03-12T08:00")]}}
    row = g.evaluate(variants, {}, START, END, None)["s"]
    assert not row["gates"]["effect_not_drift"] and row["notes"]
    assert not row["gates"]["breadth"] and not row["gates"]["no_data_integrity_failure"]
    assert row["skipped_integrity"] and row["verdict"] == "not_enough_evidence"
    uk = {"uk": {"settings": cell(exit_time="08:30"), "trades": [trade("2019-03-12T08:00", symbol="UK100")]}}
    assert g.breadth_report(uk, START, END)["passes"]
    uk["uk"]["trades"][0].r_net = -1
    assert not g.breadth_report(uk, START, END)["passes"]
    assert not g.breadth_report({}, START, END)["passes"]


def test_removal_and_minimum_and_nonprimary():
    trades = [trade((datetime(2016, 1, 1) + timedelta(days=i * 8)).isoformat(), 1, spread=1.1) for i in range(199)]
    vs = {"s": {"settings": cell(), "trades": trades}}
    row = g.evaluate(vs, {}, START, END, {"s": []})["s"]
    assert not row["gates"]["best_date_removal_positive"]
    assert row["verdict"] == "not_enough_evidence"
    assert not g.is_primary(cell(threshold="0.2"))


def test_dst_and_gap():
    ts = [trade("2019-03-12T08:00"), trade("2019-04-02T08:00")]
    assert g.dst_split(ts)["mismatch"]["trades"] == 1
    assert g.dst_split(ts)["rest"]["trades"] == 1
    t = ts[0]
    times = np.array([int((t.entry_time + timedelta(minutes=i)).timestamp()) for i in range(30) if i not in range(5, 11)])
    data = M1Data(times, np.ones(len(times)), np.ones(len(times)), np.ones(len(times)), np.ones(len(times)))
    assert g.integrity_failures([t], data, max_gap_minutes=5) == [t]


def test_cli(tmp_path):
    d = tmp_path / "variants" / "v1"
    d.mkdir(parents=True)
    (d / "settings.json").write_text(json.dumps({"run": {"start": "2015-01-02", "end": "2020-06-14", "symbols": ["GER40"], "cache_dirs": {}}}))
    with (d / "trades.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "symbol", "direction", "entry_time", "entry_candle", "entry", "initial_stop", "exit_time", "exit_price", "exit_reason", "r_gross", "r_net", "spread_r", "commission_r"])
        w.writerow([1, "GER40", "long", "2019-03-12T08:00:00+00:00", "2019-03-12T08:00:00+00:00", 1, .9, "2019-03-12T08:30:00+00:00", 1.1, "time", 1, 1, 0, 0])
    with (tmp_path / "variants.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "family", "set.min_ref_return_pct", "set.stop_atr", "set.exit_time"])
        w.writerow(["v1", "S", "0.1", "0.5", "09:30"])
    assert g.main([str(tmp_path), "--breadth-folder", str(tmp_path / "missing"), "--skip-integrity"]) == 0
    assert json.loads((tmp_path / "gates.json").read_text())["variants"]



def test_nonprimary_never_advances_with_all_gates():
    origin = datetime(2016, 1, 1)
    signal = [trade((origin + timedelta(days=7 * i)).isoformat(), 2) for i in range(200)]
    baseline = [trade((origin + timedelta(days=7 * i + 1)).isoformat(), 0) for i in range(10)]
    variants = {
        "s": {"settings": cell(threshold="0.2"), "trades": signal},
        "l": {"settings": cell(family="C", direction="long"), "trades": baseline},
        "h": {"settings": cell(family="C", direction="short"), "trades": baseline},
    }
    uk = {"uk": {"settings": cell(exit_time="08:30"),
                 "trades": [trade("2019-03-12T08:00", symbol="UK100")]}}
    row = g.evaluate(variants, uk, START, END, {k: [] for k in variants})["s"]
    assert all(row["gates"].values())
    assert row["verdict"] == "rejected" and not row["advances"]


def test_missing_signal_days_observes_nyse_calendar_and_close_times():
    stamps = [int((datetime(2019, 3, 12, h, m, tzinfo=g.NEW_YORK)
                   - timedelta(minutes=1)).timestamp()) for h, m in ((15, 30), (16, 0))]
    data = SimpleNamespace(open_s=np.array(stamps))
    assert g.missing_signal_days(data, date(2019, 3, 12), date(2019, 3, 12)) == 0
    data.open_s = data.open_s[:1]
    assert g.missing_signal_days(data, date(2019, 3, 12), date(2019, 3, 12)) == 1
    assert g.missing_signal_days(data, date(2019, 12, 25), date(2019, 12, 25)) == 0
