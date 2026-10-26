"""Portfolio tool: config file, components, combined report with a stubbed backtest.
Spec: risk-management.md > Portfolio tool (ROADMAP 12.9)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.trial_log import append, count_only, read_all
from backtester.engine.costs import CostConfig
from backtester.tools import portfolio as tool

START, END = date(2021, 1, 4), date(2021, 4, 30)


def trade(symbol, day, r_net):
    entry = datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, entry_time=entry, exit_time=entry + timedelta(hours=2),
        entry=100.0, initial_stop=99.0, exit_reason="signal", swap_r=0.0,
        r_gross=r_net + 0.05, r_net=r_net, spread_r=0.04, commission_r=0.01, funding_r=0.0,
        mae_r=-0.5, mfe_r=1.0,
    )  # fmt: skip


def weekdays(n=60):
    d, out = START, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


@pytest.fixture
def stub(monkeypatch):
    calls = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        calls.append({"symbols": list(symbols), "strategy": settings.strategy,
                      "workers": kwargs.get("workers"), "settings": settings})  # fmt: skip
        other = (
            getattr(settings.strategy, "mode", None) == "follow"
            or getattr(settings.strategy, "side", None) == "fade"
        )
        sign = -1.0 if other else 1.0
        trades = tuple(
            trade(s, d, sign * (1.0 if i % 3 else -0.8))
            for s in symbols for i, d in enumerate(weekdays())
        )  # fmt: skip
        return SimpleNamespace(trades=trades, runs={s: SimpleNamespace() for s in symbols})

    monkeypatch.setattr(tool, "run_backtests", fake_run)
    return calls


CONFIG = {
    "components": [
        {"name": "fade", "strategy": "gap_fade", "symbols": ["NAS100", "US500"],
         "families": ["gap_fade"]},
        {"name": "orb", "strategy": "opening_range", "symbols": ["US30"],
         "set": {"entry_mode": "band", "band_atr": 0.25, "target_r": 0, "min_rel_volume": 1.5},
         "families": ["opening_range", "screen_opening_range"]},
    ]
}  # fmt: skip


def write_config(tmp_path, config=None):
    p = tmp_path / "components.json"
    p.write_text(json.dumps(config or CONFIG), encoding="utf-8")
    return p


def argv(tmp_path, *extra, config=None):
    return [
        str(write_config(tmp_path, config)), "--start", START.isoformat(), "--end", END.isoformat(),
        "--runs", "30", "--out", str(tmp_path / "out"), "--trials", str(tmp_path / "t.jsonl"),
        "--cache-dir", str(tmp_path), *extra,
    ]  # fmt: skip


def load_summary(tmp_path):
    return json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))


# ----- config --------------------------------------------------------------------------------


def test_load_components_applies_the_settings(tmp_path):
    comps = tool.load_components(write_config(tmp_path))
    assert [c.name for c in comps] == ["fade", "orb"]
    orb = comps[1]
    assert orb.symbols == ["US30"] and orb.strategy == "opening_range"
    assert orb.config.band_atr == 0.25 and orb.config.min_rel_volume == 1.5
    assert orb.config.entry_mode.value == "band" and orb.families == [
        "opening_range",
        "screen_opening_range",
    ]


@pytest.mark.parametrize(
    "bad",
    [
        {"components": []},
        {"components": [{"name": "a", "strategy": "nope", "symbols": ["X"]}]},
        {"components": [{"name": "a", "strategy": "gap_fade", "symbols": []}]},
        {"components": [{"name": "a", "strategy": "gap_fade", "symbols": ["X"]},
                        {"name": "a", "strategy": "gap_fade", "symbols": ["Y"]}]},
        {"components": [{"name": "a", "strategy": "gap_fade", "symbols": ["X"], "set": {"zzz": 1}}]},
    ],
)  # fmt: skip
def test_bad_config_stops_with_a_message(tmp_path, bad):
    with pytest.raises(SystemExit):
        tool.load_components(write_config(tmp_path, bad))


def test_families_default_to_the_strategy_name(tmp_path):
    cfg = {"components": [{"name": "a", "strategy": "gap_fade", "symbols": ["NAS100"]}]}
    assert tool.load_components(write_config(tmp_path, cfg))[0].families == ["gap_fade"]


# ----- run -----------------------------------------------------------------------------------


def test_run_writes_report_and_summary(tmp_path, stub):
    append(count_only("gap_fade", "gap_fade", 36, "fill"), tmp_path / "t.jsonl")
    append(count_only("opening_range", "opening_range", 41, "fill"), tmp_path / "t.jsonl")
    assert tool.main(argv(tmp_path)) == 0
    s = load_summary(tmp_path)
    html = (tmp_path / "out" / "report.html").read_text(encoding="utf-8")
    assert [c["key"] for c in s["verdict"]["checks"]] == [
        "t_stat", "random_entries", "halves", "cost_stress", "without_best", "random_fills",
        "deflated_sharpe",
    ]  # fmt: skip
    p = s["portfolio"]
    assert [c["name"] for c in p["components"]] == ["fade", "orb"]
    assert p["weights"] == [0.5, 0.5] and p["apply_idm"] is False
    assert p["idm"] >= 1.0 and p["idm_applied"] == 1.0
    assert len(p["correlation"]) == 2 and p["correlation"][0][0] == 1.0
    assert s["deflated"]["n_trials"] == 36 + 41 and p["trial_families"] == {
        "gap_fade": 36,
        "opening_range": 41,
    }
    for text in ("Correlation", "IDM", "Deflated Sharpe", "FTMO 2-Step", "fade", "orb"):
        assert text in html
    assert "NaN" not in json.dumps(s)


def test_each_component_runs_once_with_workers_one_and_gap_fade_gets_a_follow_run(tmp_path, stub):
    tool.main(argv(tmp_path))
    strategies = [type(c["strategy"]).__name__ for c in stub]
    assert strategies.count("OpeningRangeConfig") == 1
    assert strategies.count("GapFadeConfig") == 2  # fade + the kind B follow run
    assert all(c["workers"] == 1 for c in stub)
    assert [c["symbols"] for c in stub if type(c["strategy"]).__name__ == "OpeningRangeConfig"] == [
        ["US30"]
    ]


def test_kind_b_randomises_only_the_components_that_have_it(tmp_path, stub):
    tool.main(argv(tmp_path))
    s = load_summary(tmp_path)
    assert s["random_entries"]["available"] is True
    assert len(s["random_entries"]["run_net_r"]) == 30
    assert s["portfolio"]["kind_b_components"] == ["fade"]


def test_kind_b_is_not_available_when_no_component_has_it(tmp_path, stub):
    cfg = {"components": [CONFIG["components"][1]]}
    tool.main(argv(tmp_path, config=cfg))
    s = load_summary(tmp_path)
    assert s["random_entries"]["available"] is False
    assert "random_entries" in s["verdict"]["not_available"]


def test_kind_c_is_combined_with_the_weights(tmp_path, stub):
    tool.main(argv(tmp_path))
    s = load_summary(tmp_path)
    # every stub trade has a stop distance of 1 and the default slippage is non-negative, so
    # random fills can only lower the weighted net R
    assert s["random_fills"]["p50"] <= s["random_fills"]["base_net_r"]
    assert s["random_fills"]["base_net_r"] == pytest.approx(s["robustness"]["net_r"])


def test_combined_net_r_is_the_weighted_sum_of_the_components(tmp_path, stub):
    tool.main(argv(tmp_path))
    s = load_summary(tmp_path)
    comps = s["portfolio"]["components"]
    assert s["robustness"]["net_r"] == pytest.approx(sum(c["net_r"] * c["weight"] for c in comps))
    assert s["meta"]["trades"] == sum(c["trades"] for c in comps)


def test_apply_idm_flag_scales_the_account_result(tmp_path, stub):
    tool.main(argv(tmp_path))
    off = load_summary(tmp_path)
    tool.main(argv(tmp_path, "--apply-idm"))
    on = load_summary(tmp_path)
    assert on["portfolio"]["apply_idm"] is True
    assert on["robustness"]["net_r"] == pytest.approx(
        off["robustness"]["net_r"] * on["portfolio"]["idm"]
    )


def test_own_trial_line_is_logged_but_not_counted_in_n(tmp_path, stub):
    append(count_only("gap_fade", "gap_fade", 36, "fill"), tmp_path / "t.jsonl")
    tool.main(argv(tmp_path, "--family", "portfolio_first"))
    lines = read_all(tmp_path / "t.jsonl")
    own = [r for r in lines if r.family == "portfolio_first"]
    assert len(own) == 1 and own[0].strategy == "portfolio" and own[0].trades == 120 + 60
    assert len(lines) == 2  # the components are not logged again
    s = load_summary(tmp_path)
    assert s["deflated"]["n_trials"] == 36 and s["deflated"]["family"] == "portfolio_first"


def test_extra_trial_logs_are_read_only_and_counted(tmp_path, stub):
    extra = tmp_path / "other.jsonl"
    append(count_only("gap_fade", "gap_fade", 36, "fill"), extra)
    before = extra.read_text(encoding="utf-8")
    tool.main(argv(tmp_path, "--trials-extra", str(extra)))
    assert load_summary(tmp_path)["deflated"]["n_trials"] == 36
    assert extra.read_text(encoding="utf-8") == before


def test_spread_table_is_given_to_the_costs(tmp_path, stub):
    sample = tmp_path / "spreads.json"
    sample.write_text(json.dumps({"stat": "median", "note": "t",
                                  "values": {"NAS100": {"2021": {"0": 0.5}}}}), encoding="utf-8")  # fmt: skip
    tool.main(argv(tmp_path, "--spread-table", str(sample)))
    assert all(c["settings"].engine.costs.spread_table is not None for c in stub)
    tool.main(argv(tmp_path))
    assert (
        stub[-1]["settings"].engine.costs.spread_table == CostConfig().spread_table
    )  # no option: the default table


def test_same_seed_same_numbers(tmp_path, stub):
    tool.main(argv(tmp_path))
    a = load_summary(tmp_path)
    tool.main(argv(tmp_path))
    b = load_summary(tmp_path)
    for key in ("verdict", "monte_carlo", "random_entries", "random_fills", "robustness"):
        assert a[key] == b[key]
