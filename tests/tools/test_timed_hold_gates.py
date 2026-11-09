"""Gates of the timed-hold families. Spec: strategy-timed-hold.md > Gates."""

import csv
import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.tools import timed_hold_gates as g

T0 = datetime(2020, 1, 6, 10, 0, tzinfo=UTC)
START, END = date(2020, 1, 1), date(2020, 12, 31)


def trade(entry, net=1.0, symbol="EURUSD", gross=None, spread=0.0, commission=0.0, minutes=60):
    return SimpleNamespace(
        symbol=symbol,
        entry_time=entry,
        exit_time=entry + timedelta(minutes=minutes),
        r_gross=net + spread + commission if gross is None else gross,
        r_net=net,
        spread_r=spread,
        commission_r=commission,
        swap_r=0.0,
        funding_r=0.0,
        conversion_r=0.0,
    )


def series(nets, symbol="EURUSD", step=8, offset=0):
    return [trade(T0 + timedelta(days=i * step + offset), n, symbol) for i, n in enumerate(nets)]


def test_stress_arithmetic():
    t = trade(T0, net=0.7, gross=1.0, spread=0.1, commission=0.05)
    r = g.variant_report([t], START, END)
    assert r["net_r"]["normal"] == pytest.approx(0.7)
    assert r["net_r"]["spread"] == pytest.approx(0.6)
    assert r["net_r"]["commission"] == pytest.approx(0.65)
    assert r["net_r"]["slippage"] == pytest.approx(0.55)
    assert r["net_r"]["all"] == pytest.approx(0.4)
    assert r["gross_r"] == pytest.approx(1.0)
    assert r["mean_net_r"] == pytest.approx(0.7)


def test_halves_split_at_utc_midpoint():
    a = trade(datetime(2020, 3, 1, tzinfo=UTC), 2.0)
    b = trade(datetime(2020, 11, 1, tzinfo=UTC), -1.0)
    r = g.variant_report([a, b], START, END)
    assert r["halves_net_r"] == [pytest.approx(2.0), pytest.approx(-1.0)]


def test_best_date_removal_uses_utc_entry_date_and_both_costs():
    trades = series([5, 4, 3, 2, 1, -2], step=1)
    trades.append(trade(trades[0].entry_time + timedelta(hours=1), 5.0))  # day 0 now 10
    r = g.variant_report(trades, START, END)
    assert r["best_dates_removed"] == sorted(
        (T0 + timedelta(days=i)).date().isoformat() for i in range(5)
    )
    assert r["net_r_without_best_dates"] == {"normal": pytest.approx(-2), "all": pytest.approx(-2)}


def test_bootstrap_is_deterministic_and_ordered_by_entry_time():
    nets = [1.0, -0.5, 2.0, 0.3, -1.0, 0.8, 0.2, 1.5, -0.2, 0.4, 0.9, -0.3]
    a = g.variant_report(series(nets), START, END)["bootstrap"]
    b = g.variant_report(list(reversed(series(nets))), START, END)["bootstrap"]
    assert a == b
    assert a["lower_2_5"] <= a["lower_5"] <= a["mean"] + 1e-9
    assert (g.SEED, g.BLOCK, g.RESAMPLES) == (2026110, 5, 10_000)


def test_difference_bootstrap_sign():
    rng = np.random.default_rng(1)
    filt = series(list(1.0 + rng.normal(0, 0.3, 80)))
    base = series(list(rng.normal(0, 0.3, 80)))
    d = g.difference_bootstrap(filt, base)
    assert d["difference"] > 0.5 and d["lower_2_5"] > 0
    null = g.difference_bootstrap(base, base)
    assert null["difference"] == pytest.approx(0)
    assert null["lower_2_5"] < 0
    assert g.difference_bootstrap(base, filt)["lower_2_5"] < 0
    assert g.difference_bootstrap(base, filt) == g.difference_bootstrap(base, filt)


def _variants(good=True):
    n = 40
    win = [1.0, 0.8] * (n // 2) if good else [-1.0, -0.8] * (n // 2)
    return {
        "a": {
            "settings": {"day_filter": "fomc"},
            "trades": series(win, "EURUSD") + series(win, "GBPUSD"),
        },
        "b": {
            "settings": {"day_filter": "all"},
            # the all baseline holds the filter days too; the gate compares with the other days
            "trades": series(win, "EURUSD")
            + series([0.5, -0.6] * (n // 2), "EURUSD", offset=4)
            + series(win, "GBPUSD"),
        },
    }


def test_gates_all_true():
    out = g.evaluate(_variants(), START, END, None, "EURUSD", 10, 1)
    assert all(out["a"]["gates"].values()) and out["a"]["advances"]
    assert out["a"]["skipped_integrity"] is True
    # filter mean 0.9 minus the non-filter days' mean -0.05 (filter dates left out)
    assert out["a"]["baseline_difference"]["difference"] == pytest.approx(0.95)
    # day_filter all: the gate is the bootstrap of its own mean (0.425 per trade here)
    assert out["b"]["gates"]["effect_not_drift"] is True
    assert out["b"]["symbols"]["EURUSD"]["mean_net_r"] == pytest.approx(0.425)


def test_gates_fail_cases():
    bad = g.evaluate(_variants(False), START, END, None, "EURUSD", 10, 1)["a"]
    assert not bad["advances"]
    assert not bad["gates"]["positive_normal_and_doubled"]
    assert not bad["gates"]["breadth"]
    out = g.evaluate(_variants(), START, END, None, "EURUSD", 100, 2)["a"]["gates"]
    assert not out["min_trades"] and not out["breadth"]
    r = g.evaluate({"a": _variants()["a"]}, START, END, None, "EURUSD", 10, 1)["a"]
    assert r["gates"]["effect_not_drift"] is False and "no baseline" in r["notes"][0]
    fails = {"a": {"EURUSD": [trade(T0)]}, "b": {}}
    r = g.evaluate(_variants(), START, END, fails, "EURUSD", 10, 1)["a"]
    assert r["gates"]["no_data_integrity_failure"] is False and not r["advances"]
    assert r["skipped_integrity"] is False


COLS = [
    *("id", "symbol", "direction", "entry_time", "entry_candle", "entry", "initial_stop"),
    *("exit_time", "exit_price", "exit_reason", "r_gross", "r_net", "spread_r", "commission_r"),
]


def _write_variant(folder, vid, per_symbol, offset=0):
    d = folder / "variants" / vid
    d.mkdir(parents=True)
    run = {
        "start": "2020-01-01",
        "end": "2020-12-31",
        "symbols": list(per_symbol),
        "cache_dirs": {},
    }
    (d / "settings.json").write_text(json.dumps({"run": run}), encoding="utf-8")
    with (d / "trades.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        i = 0
        for sym, nets in per_symbol.items():
            for k, n in enumerate(nets):
                e = T0 + timedelta(days=k + offset)
                x = e + timedelta(hours=1)
                row = [i, sym, "long", e.isoformat(), e.isoformat(), 1, 0.9, x.isoformat()]
                w.writerow([*row, 1.1, "time", n, n, 0, 0])
                i += 1


def test_grid_families_stay_separate_variants(tmp_path):
    win = [1.0, 0.8] * 20
    _write_variant(tmp_path, "v1", {"EURUSD": win})
    _write_variant(tmp_path, "v2", {"EURUSD": [-1.0] * 40})
    with (tmp_path / "variants.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "family", "set.direction"])
        w.writerows([["v1", "h07", "long"], ["v2", "h13", "long"]])
    argv = [str(tmp_path), "--primary-symbol", "EURUSD", "--min-trades", "10", "--min-breadth", "0"]
    assert g.main([*argv, "--skip-integrity"]) == 0
    res = json.loads((tmp_path / "gates.json").read_text(encoding="utf-8"))["variants"]
    assert set(res) == {"family=h07|direction=long", "family=h13|direction=long"}


def test_end_to_end_skip_integrity(tmp_path, capsys):
    win = [1.0, 0.8] * 20
    _write_variant(tmp_path, "v1", {"EURUSD": win, "GBPUSD": win})
    _write_variant(tmp_path, "v2", {"EURUSD": [0.0, 0.1] * 20, "GBPUSD": win}, offset=60)
    with (tmp_path / "variants.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant_id", "set.day_filter", "set.hold"])
        w.writerows([["v1", "fomc", "60"], ["v2", "all", "60"]])
    argv = [str(tmp_path), "--primary-symbol", "EURUSD", "--min-trades", "10"]
    assert g.main([*argv, "--min-breadth", "1", "--skip-integrity"]) == 0
    res = json.loads((tmp_path / "gates.json").read_text(encoding="utf-8"))
    v = res["variants"]["day_filter=fomc|hold=60"]
    assert v["gates"]["no_data_integrity_failure"] and v["skipped_integrity"] is True
    assert set(v["symbols"]) == {"EURUSD", "GBPUSD"} and v["pooled"]["trades"] == 80
    assert v["baseline_difference"]["difference"] > 0.5
    assert len(capsys.readouterr().out.strip().splitlines()) == 2
