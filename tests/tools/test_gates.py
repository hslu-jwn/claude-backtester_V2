"""Generic gates equivalence and pipeline controls on synthetic trades only."""

import csv
import json
from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.tools import gates as g
from backtester.tools import us_close_de_open_gates as legacy

START, END = date(2015, 1, 2), date(2020, 6, 14)
CONFIG = {
    "symbol": "GER40", "min_trades": 200, "halves": "2017-10-08",
    "primary": {"family": "S", "min_ref_return_pct": .1, "stop_atr": .5,
                "exit_time": "09:30"},
    "integrity_max_gap": 5,
    "control": {"family": "C", "match": ["stop_atr", "exit_time"]},
    "breadth": {"symbol": "UK100", "primary": {
        "family": "S", "min_ref_return_pct": .1, "stop_atr": .5, "exit_time": "08:30"}},
}


def trade(i, value=2., direction="long", symbol="GER40"):
    dt = datetime(2016, 1, 1, 8, tzinfo=UTC) + timedelta(days=i)
    return SimpleNamespace(entry_time=dt, exit_time=dt + timedelta(minutes=30),
                           direction=direction, symbol=symbol, r_net=value,
                           r_gross=value, spread_r=0., commission_r=0., swap_r=0.,
                           funding_r=0., conversion_r=0.)


def settings(family="S", **extra):
    return {"family": family, "stop_atr": "0.5", "exit_time": "09:30",
            **({"min_ref_return_pct": "0.1"} if family == "S" else {}), **extra}


def fixtures(n=200):
    variants = {"s": {"settings": settings(), "trades": [trade(i * 7) for i in range(n)]}}
    for d in ("long", "short"):
        variants[d] = {"settings": settings("C", direction=d),
                       "trades": [trade(i * 7 + 1, 0., d) for i in range(220)]}
    breadth = {"uk": {"settings": settings(exit_time="08:30"),
                      "trades": [trade(1, symbol="UK100")]}}
    return variants, breadth


def test_strategy14_equivalence():
    variants, breadth = fixtures()
    failures = {k: [] for k in variants}
    expected = legacy.evaluate(variants, breadth, START, END, failures)
    actual = g.evaluate(variants, breadth, START, END, failures, CONFIG)
    for key in variants:
        assert actual[key]["verdict"] == expected[key]["verdict"]
        assert actual[key]["report"]["net_r"] == expected[key]["report"]["net_r"]
        assert actual[key]["report"]["bootstrap"] == expected[key]["report"]["bootstrap"]
        if key == "s":
            for field in ("gates", "control_difference", "breadth"):
                assert actual[key][field] == expected[key][field]
            assert actual[key]["report"]["halves_net_r"] == expected[key]["report"]["halves_net_r"]


def test_optional_nulls_midpoint_and_breadth():
    ts = [trade(0), trade(3)]
    # [Jan 1, Jan 5) midpoint is Jan 3 00:00 UTC; split uses entry time.
    ts[0].exit_time = ts[1].exit_time
    vs = {"s": {"settings": settings(), "trades": ts}}
    cfg = {"min_trades": 2, "halves": "midpoint", "breadth": {"min_positive": 1}}
    row = g.evaluate(vs, {}, date(2016, 1, 1), date(2016, 1, 4), None, cfg)["s"]
    assert row["report"]["halves_net_r"] == [2., 2.]
    assert row["gates"]["breadth"] is True
    assert row["gates"]["effect_not_drift"] is None
    assert row["gates"]["no_data_integrity_failure"] is None
    assert not row["advances"]
    cfg = {"min_trades": 2}
    row = g.evaluate(vs, {}, START, END, None, cfg)["s"]
    for gate in ("positive_both_halves", "breadth", "effect_not_drift", "no_data_integrity_failure"):
        assert row["gates"][gate] is None


def test_minimum_nonprimary_skip_and_numeric_matching():
    vs, breadth = fixtures(199)
    row = g.evaluate(vs, breadth, START, END, None, CONFIG)["s"]
    assert row["verdict"] == "not_enough_evidence"
    assert row["skipped_integrity"] and row["gates"]["no_data_integrity_failure"] is False
    vs, breadth = fixtures()
    vs["s"]["settings"]["min_ref_return_pct"] = "0.10"
    vs["long"]["settings"]["stop_atr"] = "0.50"
    result = g.evaluate(vs, breadth, START, END, {k: [] for k in vs}, CONFIG)
    assert result["s"]["verdict"] == "advances"
    vs["s"]["settings"]["min_ref_return_pct"] = ".2"
    row = g.evaluate(vs, breadth, START, END, {k: [] for k in vs}, CONFIG)["s"]
    assert all(row["gates"].values()) and row["verdict"] == "rejected"


def test_pooled_breadth_counts_symbols_before_selection():
    vs = {"s": {"settings": settings(), "trades": [
        trade(0, symbol=s) for s in ("GER40", "UK100", "EURUSD", "US500")]}}
    cfg = {"symbol": "GER40", "min_trades": 1, "breadth": {"min_positive": 4}}
    row = g.evaluate(vs, {}, START, END, None, cfg)["s"]
    assert row["report"]["trades"] == 1 and row["gates"]["breadth"] is True


def test_empty_and_missing_controls():
    vs = {"s": {"settings": settings(), "trades": []}}
    row = g.evaluate(vs, {}, START, END, None, CONFIG, controls=2)["s"]
    assert row["verdict"] == "not_enough_evidence"
    assert row["controls"] is None and row["notes"]


def test_pipeline_controls():
    signal = [trade(i, 4., "long" if i % 2 else "short") for i in range(100)]
    longs = [trade(i, 1., "long") for i in range(1000)]
    shorts = [trade(i, -1., "short") for i in range(1000)]
    result = g.pipeline_controls(signal, longs, shorts, 10, START, END)
    assert result["negative"]["all_three"] <= .05
    assert result["positive"]["all_three"] >= .8
    assert result["edge"] == pytest.approx(2.8 * (2000 / 1999) ** .5 / 10)
    assert result == g.pipeline_controls(signal, longs, shorts, 10, START, END)


def test_cli_and_missing_table(tmp_path):
    grid = tmp_path / "grid.toml"
    grid.write_text('strategy = "opening_range"\nsymbols = ["GER40"]\n')
    (tmp_path / "research.json").write_text(json.dumps({"grid_file": str(grid)}))
    with pytest.raises(ValueError, match=r"\[gates\]"):
        g.main([str(tmp_path), "--skip-integrity"])
    grid.write_text(grid.read_text() + '\n[gates]\nmin_trades = 200\nintegrity_max_gap = 5\n')
    d = tmp_path / "variants" / "v1"
    d.mkdir(parents=True)
    (d / "settings.json").write_text(json.dumps({"run": {
        "start": str(START), "end": str(END), "symbols": ["GER40"], "cache_dirs": {}}}))
    with (d / "trades.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "symbol", "direction", "entry_time", "entry_candle", "entry",
                         "initial_stop", "exit_time", "exit_price", "exit_reason", "r_gross",
                         "r_net", "spread_r", "commission_r"])
        writer.writerow([1, "GER40", "long", "2019-03-12T08:00:00+00:00",
                         "2019-03-12T08:00:00+00:00", 1, .9, "2019-03-12T08:30:00+00:00",
                         1.1, "time", 1, 1, 0, 0])
    with (tmp_path / "variants.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["variant_id", "family"])
        writer.writerow(["v1", "S"])
    assert g.main([str(tmp_path), "--skip-integrity", "--controls", "2"]) == 0
    result = json.loads((tmp_path / "gates.json").read_text())
    row = next(iter(result["variants"].values()))
    assert row["verdict"] == "not_enough_evidence"
    assert row["gates"]["no_data_integrity_failure"] is False


def test_falsification_and_failed_optional_gate():
    vs, _ = fixtures()
    cfg = {"min_trades": 200, "primary": CONFIG["primary"]}
    row = g.evaluate(vs, {}, START, END, None, cfg)["s"]
    assert row["verdict"] == "advances"
    cfg["breadth"] = {"min_positive": 4}
    assert g.evaluate(vs, {}, START, END, None, cfg)["s"]["verdict"] == "rejected"
    bad = deepcopy(vs)
    for t in bad["s"]["trades"]:
        t.r_net = -1
    assert g.evaluate(bad, {}, START, END, None, cfg)["s"]["verdict"] == "falsified"


def test_numeric_control_family_and_minimum_precedence():
    vs, breadth = fixtures(199)
    cfg = deepcopy(CONFIG)
    cfg["control"]["family"] = 3
    for d in ("long", "short"):
        vs[d]["settings"]["family"] = "3.0"
    for t in vs["s"]["trades"]:
        t.r_net = -1.
    rows = g.evaluate(vs, breadth, START, END, None, cfg)
    assert rows["long"]["verdict"] == rows["short"]["verdict"] == "control"
    assert rows["s"]["verdict"] == "not_enough_evidence"


def test_pipeline_invalid_date_pools_and_no_mutation():
    signal = [trade(0), trade(1)]
    with pytest.raises(ValueError, match="shared control entry dates"):
        g.pipeline_controls(signal, [trade(2)], [trade(3)], 1, START, END)
    with pytest.raises(ValueError, match="duplicate control entry dates"):
        g.pipeline_controls(signal, [trade(2), trade(2)], [trade(2)], 1, START, END)
    original = trade(2)
    shifted = g._shift(original, 3.)
    assert original.r_net == 2. and shifted.r_net == 5.
