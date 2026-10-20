"""Large-move momentum study: trailing robust sd (no lookahead), events, signed forward
returns, shuffled-time null, top-1 % removal, spread units, findings reuse.
Spec: ROADMAP.md > 11.13; ideas.md I-61. Synthetic series, fixed seeds."""

from __future__ import annotations

import numpy as np
import pytest

from backtester.analytics import large_move as lm
from backtester.analytics.large_move import LargeMoveConfig
from backtester.analytics.stationarity import StationarityConfig

CFG = LargeMoveConfig(window=100, ks=(3.0,), hs=(1, 2), n_null=400, min_events=10)
SCFG = StationarityConfig()
BAR = 3600
JUMPS = tuple(range(150, 2950, 40))  # 70 injected events


def secs_hourly(n, start=0):
    return start + np.arange(n, dtype=np.int64) * BAR


def series(n, seed=1, sigma=0.001, jumps=(), follow=0.0):
    """Log prices: gaussian walk; at each bar in `jumps` a move of 8 sigma (sign alternates)
    and the next bar continues (follow > 0) or reverses (follow < 0) by |follow| x the move."""
    r = np.random.default_rng(seed).normal(0, sigma, n)
    for j, b in enumerate(jumps):
        sign = 1 if j % 2 == 0 else -1
        r[b] = sign * 8 * sigma
        r[b + 1] = sign * follow * 8 * sigma
    return np.cumsum(r)  # y[b] - y[b-1] = r[b]


def cell(rows, k=3.0, h=1, period="whole"):
    return next(r for r in rows if r["k"] == k and r["h"] == h and r["period"] == period)


def rows_of(y, secs=None, cfg=CFG, split=None, spread=1e-4):
    secs = secs_hourly(len(y)) if secs is None else secs
    split = len(y) // 2 if split is None else split
    return lm.cell_rows(y, secs, BAR, split, spread, cfg, SCFG, seed_key="t")


def test_trailing_sd_uses_only_past_bars():
    y = series(600, seed=3)
    ret = lm.bar_returns(y)
    full = lm.trailing_robust_sd(ret, 100)
    for n in (150, 300, 450):
        part = lm.trailing_robust_sd(ret[:n], 100)
        assert np.array_equal(part, full[:n], equal_nan=True)


def test_trailing_sd_excludes_the_current_bar_and_warms_up():
    ret = np.full(300, np.nan)
    ret[1:] = np.random.default_rng(5).normal(0, 0.001, 299)
    sd = lm.trailing_robust_sd(ret, 100)
    assert np.isnan(sd[:101]).all()  # needs 100 past returns (indices 1..100)
    assert np.isfinite(sd[101])
    spiked = ret.copy()
    spiked[200] = 1.0  # a huge current return must not move its own sd
    assert lm.trailing_robust_sd(spiked, 100)[200] == sd[200]


def test_trailing_sd_value_is_1_4826_mad_of_the_past_window():
    ret = np.full(200, np.nan)
    ret[1:] = np.random.default_rng(6).normal(0, 0.002, 199)
    sd = lm.trailing_robust_sd(ret, 100)
    past = ret[50:150]
    mad = 1.4826 * np.median(np.abs(past - np.median(past)))
    assert sd[150] == pytest.approx(mad)


def test_no_lookahead_appending_future_bars_never_changes_events():
    y = series(1500, seed=4, jumps=JUMPS[:20], follow=0.35)
    secs = secs_hourly(1500)
    ev_full = lm.event_mask(y, secs, BAR, 3.0, CFG, SCFG)
    assert ev_full.sum() > 10
    for n in (400, 800, 1200):
        assert np.array_equal(lm.event_mask(y[:n], secs[:n], BAR, 3.0, CFG, SCFG), ev_full[:n])


def test_continuation_gives_positive_signed_forward_return():
    c = cell(rows_of(series(3000, seed=1, jumps=JUMPS, follow=0.35)), h=1)
    assert c["n"] >= 60
    assert c["mean_sd"] == pytest.approx(2.4, abs=0.8)  # 0.35 x 8 sd, diluted by chance events
    assert c["p"] < 0.001


def test_reversal_gives_negative_signed_forward_return():
    c = cell(rows_of(series(3000, seed=1, jumps=JUMPS, follow=-0.35)), h=1)
    assert c["mean_sd"] == pytest.approx(-2.4, abs=0.8)
    assert c["p"] < 0.001


def test_random_walk_has_no_effect_and_is_not_a_finding():
    rows = rows_of(series(8000, seed=11))
    c = cell(rows, h=1)
    assert c["n"] >= 10
    assert abs(c["mean_sd"]) < 1.0
    assert c["p"] > 0.01
    for r in rows:
        r["symbol"], r["timeframe"] = "EURUSD", "H1"
    assert not any(r["finding"] for r in lm.annotate(rows, [], SCFG))


def test_events_after_a_gap_are_excluded():
    y = series(3000, seed=1, jumps=JUMPS, follow=0.35)
    secs = secs_hourly(3000)
    b = JUMPS[10]
    assert lm.event_mask(y, secs, BAR, 3.0, CFG, SCFG)[b]
    secs[b:] += 10 * BAR  # a gap of 10 bars right before the injected move
    ev = lm.event_mask(y, secs, BAR, 3.0, CFG, SCFG)
    assert not ev[b]
    assert ev[JUMPS[11]]  # the next move is untouched


def test_return_over_exactly_gap_bars_is_not_a_gap():
    y = series(3000, seed=1, jumps=JUMPS, follow=0.35)
    secs = secs_hourly(3000)
    b = JUMPS[10]
    secs[b:] += 2 * BAR  # 3 bars apart: the limit is "more than 3 bars"
    assert lm.event_mask(y, secs, BAR, 3.0, CFG, SCFG)[b]


def test_forward_return_and_sd_units():
    y = np.array([0.0, 0.0, -0.01, -0.03, -0.02])
    fwd = lm.forward_log_return(y, 1)
    assert fwd[2] == pytest.approx(-0.02)
    assert np.isnan(fwd[4])
    assert lm.forward_log_return(y, 2)[2] == pytest.approx(-0.01)
    # a down move (sign -1) followed by a further drop is continuation: positive
    assert lm.signed(-1, fwd[2]) == pytest.approx(0.02)


def test_null_keeps_count_and_hour_of_day():
    y = series(3000, seed=1, jumps=JUMPS, follow=0.35)
    ctx = lm.prepare(y, secs_hourly(3000), BAR, CFG, SCFG)
    ev = lm.events_for(ctx, 3.0, 1)
    draws = lm.null_indices(ctx, ev, CFG, "x")
    assert draws.shape == (CFG.n_null, int(ev.sum()))
    expected = np.sort(ctx["hour"][ev])
    for run in draws[:5]:
        assert np.array_equal(np.sort(ctx["hour"][run]), expected)


def test_null_is_seeded_and_reproducible():
    y = series(3000, seed=1, jumps=JUMPS, follow=0.35)
    a, b = rows_of(y), rows_of(y)
    assert cell(a)["null_mean"] == cell(b)["null_mean"]
    assert cell(a)["null_sd"] > 0


def test_top_share_removal_drops_the_best_events_in_the_direction_of_the_mean():
    v = np.array([1.0] * 98 + [50.0, 40.0])
    out = lm.trim_top(v, 1.0, 0.01)  # ceil(0.01 x 100) = 1
    assert len(out) == 99 and 50.0 not in out and 40.0 in out
    neg = np.array([-1.0] * 99 + [-60.0])
    assert -60.0 not in lm.trim_top(neg, -1.0, 0.01)
    assert len(lm.trim_top(np.array([1.0, 2.0, 3.0]), 1.0, 0.01)) == 2  # at least one


def test_one_crash_event_does_not_survive_the_top_removal():
    v = np.concatenate([np.random.default_rng(1).normal(0, 1, 200), [400.0]])
    assert abs(v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))) > 0.5  # looks big untrimmed
    _, t = lm.trimmed_mean_t(v, 0.01)
    assert abs(t) < 1.96


def test_spread_return_is_spread_over_reference_price():
    from backtester.engine.costs import DEFAULT_SYMBOL_COSTS

    c = DEFAULT_SYMBOL_COSTS["XAUUSD"]
    assert lm.spread_return("XAUUSD") == pytest.approx(c.spread / c.reference_price)
    assert lm.spread_return("GBPUSD") == pytest.approx(0.00003 / 1.348)


def test_mean_in_spreads_converts_return_units():
    c = cell(rows_of(series(3000, seed=1, jumps=JUMPS, follow=0.35), spread=1e-3), h=1)
    assert c["mean_spreads"] == pytest.approx(c["mean_ret"] / 1e-3)
    assert c["mean_ret"] == pytest.approx(0.0028, rel=0.25)  # 0.35 x 8 x 0.001, signed


def test_halves_split_events_at_the_split_bar():
    rows = rows_of(series(3000, seed=1, jumps=JUMPS, follow=0.35), split=1500)
    n1, n2 = cell(rows, period="first_half")["n"], cell(rows, period="second_half")["n"]
    assert n1 + n2 == cell(rows)["n"] and n1 > 20 and n2 > 20


def _sym_rows(sym, seed, jumps, follow):
    y = series(3000, seed=seed, jumps=jumps, follow=follow)
    rows = rows_of(y, split=1500)
    for r in rows:
        r["symbol"], r["timeframe"] = sym, "H1"
    return rows


def test_findings_reuse_bh_halves_and_siblings():
    rows = []
    for sym, seed, jumps in (
        ("EURUSD", 1, JUMPS),
        ("GBPUSD", 2, JUMPS),
        ("JP225", 3, JUMPS),  # no sibling symbol in the data
    ):
        rows += _sym_rows(sym, seed, jumps, 0.35)
    pad = [
        {
            "family": "large_move",
            "symbol": f"S{i}",
            "timeframe": "H1",
            "cell": "k=3.0,h=1",
            "period": "whole",
            "p_value": 0.5,
            "value": 0.0,
        }
        for i in range(30)
    ]
    cells = lm.cells_for_findings(rows) + pad
    findings, counts = lm.find_move_findings(cells, SCFG)
    got = {f["symbol"] for f in findings}
    assert {"EURUSD", "GBPUSD"} <= got
    assert "JP225" not in got
    assert counts["large_move"]["cells"] >= 34
    out = lm.annotate(rows, findings, SCFG)
    eur = cell([r for r in out if r["symbol"] == "EURUSD"], h=1)
    assert eur["finding"] is True and eur["tradeable"] is True
    oil = cell([r for r in out if r["symbol"] == "JP225"], h=1)
    assert oil["finding"] is False and "sibling" in oil["reason"]


def test_annotate_marks_a_crash_driven_cell_as_failing_the_top_removal():
    rows = _sym_rows("EURUSD", 1, JUMPS, 0.35)
    sib = _sym_rows("GBPUSD", 2, JUMPS, 0.35)
    # replace the stored events of EURUSD h=1 whole with one dominated by a single event
    for r in rows:
        if r["h"] == 1 and r["period"] == "whole":
            r["trim_t"] = 0.5  # trimmed t below the survival threshold
    findings, _ = lm.find_move_findings(lm.cells_for_findings(rows + sib), SCFG)
    out = lm.annotate(rows + sib, findings, SCFG)
    c = cell([r for r in out if r["symbol"] == "EURUSD"], h=1)
    assert c["finding"] is False and "top" in c["reason"]
