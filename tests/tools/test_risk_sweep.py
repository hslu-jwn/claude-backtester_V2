"""Adaptive-risk variant sweep: grid, evaluation on fixed day orders, selection on the
development period only, universal pick, flat top, trade cache key.
Spec: risk-management.md > Prop-firm field > Adaptive risk (ROADMAP 5.7 part 2)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.risk.adaptive import AdaptiveRisk
from backtester.tools import risk_sweep
from backtester.tools.risk_sweep import (
    SweepConfig,
    Variant,
    cache_name,
    evaluate,
    flat_top,
    mean_ranks,
    pick_best,
    rank_scores,
    universal_pick,
    variants,
)


def row(label, passp, days=10.0, **kw):
    return {"label": label, "pass_probability": passp, "average_days_to_pass": days, **kw}


def test_grid_size_and_baselines():
    cfg = SweepConfig()
    vs = variants(cfg)
    # 5 base risks x (4 floors x 5 budgets - the "both off" cell) adaptive + 5 fixed baselines
    assert len(vs) == 5 * 19 + 5
    assert len({v.label for v in vs}) == len(vs)
    fixed = [v for v in vs if v.is_fixed]
    assert sorted(v.base for v in fixed) == sorted(cfg.base_risks)
    assert all(v.adaptive() is None for v in fixed)


def test_off_cells_map_to_neutral_adaptive_settings():
    cfg = SweepConfig()
    v = Variant(0.01, None, 0.03)  # floor off: no scaling, only the budget
    assert v.adaptive() == AdaptiveRisk(floor=1.0, daily_budget=0.03)
    w = Variant(0.01, 0.25, None)  # budget off: only the scaling
    assert w.adaptive() == AdaptiveRisk(floor=0.25, daily_budget=cfg.no_budget)


def test_pick_best_prefers_fewer_days_within_one_pp():
    rows = [row("a", 0.80, 20), row("b", 0.795, 12), row("c", 0.70, 5)]
    assert pick_best(rows, 0.01)["label"] == "b"  # c is 10 pp worse, b within 1 pp of a
    assert pick_best(rows, 0.0)["label"] == "a"  # exact ties only


def test_pick_best_no_pass_days_is_worst_and_ties_are_deterministic():
    rows = [row("z", 0.0, None), row("y", 0.0, None)]
    assert pick_best(rows, 0.01)["label"] == "y"
    rows = [row("a", 0.5, None), row("b", 0.5, 30)]
    assert pick_best(rows, 0.01)["label"] == "b"


def test_rank_scores_average_ties():
    ranks = rank_scores([row("a", 0.9), row("b", 0.5), row("c", 0.5), row("d", 0.1)])
    assert ranks == {"a": 1.0, "b": 2.5, "c": 2.5, "d": 4.0}


def test_universal_pick_best_mean_rank():
    per = {
        "s1": [row("x", 0.9), row("y", 0.8), row("z", 0.1)],
        "s2": [row("x", 0.2), row("y", 0.7), row("z", 0.1)],
    }
    assert mean_ranks(per) == {"x": 1.5, "y": 1.5, "z": 3.0}
    # tie in mean rank: higher mean pass probability wins (x: 0.55, y: 0.75)
    assert universal_pick(per)["label"] == "y"


def test_universal_pick_ignores_strategies_listed_out():
    per = {
        "s1": [row("x", 0.9), row("y", 0.1)],
        "s2": [row("x", 0.0), row("y", 0.02)],
    }
    assert universal_pick(per)["label"] in {"x", "y"}
    assert universal_pick({"s1": per["s1"]})["label"] == "x"


def test_flat_top_counts_variants_near_the_best():
    rows = [row("a", 0.80), row("b", 0.795), row("c", 0.78), row("d", 0.70)]
    assert flat_top(rows, (0.01, 0.02)) == {0.01: 2, 0.02: 3}


def test_cache_name_changes_with_every_input():
    a = cache_name(
        "gap_fade", ["NAS100", "US500"], date(2018, 1, 1), date(2021, 9, 13), "hd", {"x": 1}
    )
    assert a == cache_name(
        "gap_fade", ["US500", "NAS100"], date(2018, 1, 1), date(2021, 9, 13), "hd", {"x": 1}
    )
    for other in (
        cache_name("gap_fade", ["NAS100"], date(2018, 1, 1), date(2021, 9, 13), "hd", {"x": 1}),
        cache_name(
            "gap_fade", ["NAS100", "US500"], date(2018, 1, 2), date(2021, 9, 13), "hd", {"x": 1}
        ),
        cache_name(
            "gap_fade", ["NAS100", "US500"], date(2018, 1, 1), date(2021, 9, 12), "hd", {"x": 1}
        ),
        cache_name(
            "gap_fade", ["NAS100", "US500"], date(2018, 1, 1), date(2021, 9, 13), "mt5", {"x": 1}
        ),
        cache_name(
            "gap_fade", ["NAS100", "US500"], date(2018, 1, 1), date(2021, 9, 13), "hd", {"x": 2}
        ),
        cache_name(
            "no_wick", ["NAS100", "US500"], date(2018, 1, 1), date(2021, 9, 13), "hd", {"x": 1}
        ),
    ):
        assert other != a


def trades(rs):
    t0 = datetime(2020, 1, 6, 10, tzinfo=UTC)
    return [
        SimpleNamespace(
            entry_time=t0 + timedelta(days=i), exit_time=t0 + timedelta(days=i, hours=1), r_net=r
        )
        for i, r in enumerate(rs)
    ]


def test_evaluate_fixed_matches_ftmo_by_risk_and_is_reproducible():
    cfg = SweepConfig(base_risks=(0.01,), floors=(0.25, None), budgets=(None, 0.03), runs=20)
    ts = trades([1.0, -1.0, 2.0, -1.0, 1.0, 1.0, -1.0, 2.0] * 6)
    vs = variants(cfg)
    a = evaluate(ts, date(2020, 1, 6), date(2020, 4, 30), cfg, vs, workers=1)
    b = evaluate(ts, date(2020, 1, 6), date(2020, 4, 30), cfg, vs, workers=1)
    assert a == b
    assert {r["label"] for r in a} == {v.label for v in vs}
    for r in a:
        assert 0.0 <= r["pass_probability"] <= 1.0
        assert r["attempts"] >= 0
    fixed = next(r for r in a if r["label"] == Variant(0.01, None, None).label)
    assert fixed["skipped_trades"] == 0


def test_evaluate_budget_skips_trades():
    cfg = SweepConfig(base_risks=(0.01,), floors=(0.5,), budgets=(0.0105, None), runs=10)
    t0 = datetime(2020, 1, 6, 10, tzinfo=UTC)
    ts = [  # three trades open at once on each day: the 1.05 % budget fits only one
        SimpleNamespace(
            entry_time=t0 + timedelta(days=d), exit_time=t0 + timedelta(days=d, hours=1), r_net=1.0
        )
        for d in range(60)
        if (t0 + timedelta(days=d)).weekday() < 5
        for _ in range(3)
    ]
    out = evaluate(ts, date(2020, 1, 6), date(2020, 4, 30), cfg, variants(cfg), workers=1)
    tight = next(r for r in out if r["budget"] == 0.0105)
    open_ = next(r for r in out if r["budget"] is None and not r["fixed"])
    assert tight["skipped_trades"] > 0
    assert open_["skipped_trades"] == 0


def test_config_validation():
    with pytest.raises(ValueError):
        SweepConfig(runs=0)
    with pytest.raises(ValueError):
        SweepConfig(base_risks=())
    with pytest.raises(ValueError):
        SweepConfig(dev_start=date(2022, 1, 1))


def fake_backtest_factory(seen):
    def fake(symbols, start, end, settings, sources=None, workers=None, **kw):
        seen.append((tuple(symbols), start, end, sources))
        t0 = datetime(start.year, start.month, start.day, 10, tzinfo=UTC)
        trs = [
            SimpleNamespace(
                symbol=symbols[0],
                entry_time=t0 + timedelta(days=i),
                exit_time=t0 + timedelta(days=i, hours=1),
                r_gross=1.0 if i % 3 else -1.0,
                r_net=0.9 if i % 3 else -1.1,
            )
            for i in range(40)
        ]
        return SimpleNamespace(trades=trs)

    return fake


def test_trades_for_caches_and_dev_reads_histdata_only(tmp_path):
    cfg = SweepConfig(runs=5)
    plan = risk_sweep.plans()["ny_index_sweep"]
    seen: list = []
    fake = fake_backtest_factory(seen)
    a = risk_sweep.trades_for(plan, "dev", cfg, tmp_path, backtest=fake, log=lambda *_: None)
    b = risk_sweep.trades_for(plan, "dev", cfg, tmp_path, backtest=fake, log=lambda *_: None)
    assert len(seen) == 1 and a == b and len(a) == 40
    _, start, end, sources = seen[0]
    assert (start, end) == (cfg.dev_start, date(2021, 9, 13))
    assert sources.preferred_dirs == {} and "histdata" in str(sources.cache_dir("NAS100"))
    risk_sweep.trades_for(plan, "test", cfg, tmp_path, backtest=fake, log=lambda *_: None)
    assert seen[1][1:3] == (cfg.cutoff, cfg.test_end) and "mt5" in str(
        seen[1][3].cache_dir("NAS100")
    )


def test_strategy6_plan_is_the_forward_test_candidate():
    from backtester.live.bot import FORWARD_SYMBOLS, forward_strategy_config

    plan = risk_sweep.plans()["opening_range"]
    assert plan.config == forward_strategy_config()
    assert set(plan.test_symbols) == set(FORWARD_SYMBOLS)
    assert plan.dev_source == "mt5" and set(plan.dev_symbols) <= {"US30", "US2000"}


def test_sweep_plays_the_test_period_only_for_the_picks(tmp_path):
    cfg = SweepConfig(
        base_risks=(0.005, 0.01), floors=(0.25, None), budgets=(None, 0.03), runs=5, workers=1
    )
    seen: list = []
    orig = risk_sweep.run_variant
    risk_sweep.run_variant = fake_backtest_factory(seen)
    try:
        res = risk_sweep.sweep(
            cfg, ["ny_index_sweep", "gap_fade"], tmp_path, "dev", log=lambda *_: None
        )
    finally:
        risk_sweep.run_variant = orig
    assert all(s[2] == cfg.dev_end for s in seen)  # no test-period run in the dev phase
    assert all("picks" not in s for s in res["strategies"].values())
    assert res["universal"]["label"]


def test_full_sweep_writes_report_and_test_picks(tmp_path):
    cfg = SweepConfig(
        base_risks=(0.005, 0.01), floors=(0.25, None), budgets=(None, 0.03), runs=5, workers=1
    )
    seen: list = []
    orig = risk_sweep.run_variant
    risk_sweep.run_variant = fake_backtest_factory(seen)
    try:
        res = risk_sweep.sweep(
            cfg, ["ny_index_sweep", "gap_fade"], tmp_path, "all", log=lambda *_: None
        )
    finally:
        risk_sweep.run_variant = orig
    for s in res["strategies"].values():
        assert {"best", "universal"} <= set(s["picks"])
        best = s["picks"]["best"]
        assert best["test_fixed"]["fixed"] and best["test_fixed"]["base"] == best["test"]["base"]
    risk_sweep.write_outputs(res, tmp_path / "out")
    assert (tmp_path / "out" / "summary.json").exists()
    assert "Universal variant" in (tmp_path / "out" / "report.md").read_text(encoding="utf8")
    assert (
        (tmp_path / "out" / "variants.csv").read_text(encoding="utf8").startswith("strategy,period")
    )
