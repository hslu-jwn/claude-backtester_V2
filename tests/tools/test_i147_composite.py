"""I-147 flow + carry composite forward logger (knowledge/ideas.md > I-147). Hand-built fixtures, tmp_path only."""

import importlib.util
from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

_spec = importlib.util.spec_from_file_location(
    "i147", "research/screens/2026-11-27_i147_composite_forward.py"
)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

MON = pd.Timestamp("2026-11-30")
FIRST = pd.Timestamp("2026-09-20")


def bars(rng, first=FIRST, last="2026-12-21", base=10.0):
    idx = pd.date_range(first, last, freq="D")
    close = base * np.exp(np.cumsum(rng.normal(0, 0.02, len(idx))))
    vol = rng.uniform(1.0e6, 2.0e6, len(idx))
    return pd.DataFrame(
        {
            "open": np.r_[base, close[:-1]],
            "close": close,
            "volume": vol,
            "quote_volume": vol * close,
            "taker_buy_volume": vol * rng.uniform(0.3, 0.7, len(idx)),
        },
        index=idx,
    )


def funding(rng, first=FIRST, last="2026-12-22"):
    idx = pd.date_range(first, last, freq="8h")
    return pd.Series(rng.normal(1e-4, 1e-4, len(idx)), index=idx)


def make(n=45, last="2026-12-21"):
    """Always draw the full series, then cut at `last`: later days never change earlier bars."""
    rng = np.random.default_rng(0)
    names = [f"S{i:02d}USDT" for i in range(n)]
    k = {s: bars(rng) for s in names}
    fund = {s: funding(rng) for s in names}
    spot = {s: bars(rng) for s in names[::2]}
    end = pd.Timestamp(last)
    cut = lambda d: (
        d[d.index <= end + pd.Timedelta(hours=16)]
        if isinstance(d, pd.Series)
        else d[d.index <= end]
    )
    return (
        {s: cut(d) for s, d in k.items()},
        {s: cut(d) for s, d in fund.items()},
        {s: cut(d) for s, d in spot.items()},
    )


def test_rank_normal_is_phi_inverse_of_mid_ranks_and_keeps_nan():
    z = m.rank_normal(pd.Series([3.0, 1.0, np.nan, 2.0, 4.0], index=list("abcde")))
    inv = NormalDist().inv_cdf
    assert z["b"] == pytest.approx(inv(0.125)) and z["d"] == pytest.approx(inv(0.375))
    assert z["a"] == pytest.approx(inv(0.625)) and z["e"] == pytest.approx(inv(0.875))
    assert "c" not in z.index  # missing values are dropped; a reindex gives NaN
    assert m.rank_normal(pd.Series([1.0, 1.0, 1.0, 1.0])).tolist() == pytest.approx(
        [0.0] * 4
    )  # ties share a rank


def frame(n=10, f3=True):
    r = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "f1": r,
            "f2": r[::-1].copy() * 0.5 + (r % 3),
            "f3": r * 2 if f3 else np.nan,
            "c": -(r**2),
        },
        index=[f"S{i}" for i in range(n)],
    )


def test_flow_part_is_restandardised_to_unit_sd_and_missing_f3_is_handled():
    for with_f3 in (True, False):
        f = frame(f3=with_f3)
        z = pd.DataFrame({k: m.rank_normal(f[k]) for k in ("f1", "f2", "f3")})
        F = z.mean(axis=1, skipna=True)
        expected = 0.5 * F / F.std(ddof=0) + 0.5 * m.rank_normal(f["c"])
        s = m.score(f)
        assert s.tolist() == pytest.approx(expected.tolist())
        assert s.notna().all()


def test_degenerate_flow_raises():
    f = frame()
    f["f1"] = f["f2"] = f["f3"] = 5.0  # all tied: ranks equal, z = 0, no dispersion
    with pytest.raises(ValueError):
        m.score(f)


def test_target_clip_mean_removed_long_one_short_one():
    s = pd.Series([6.0, 1.0, 0.5, 0.0, -0.5, -1.0, -3.0, 0.2])
    w = m.target_weights(s)
    clipped = s.clip(-2, 2)
    expected_sign = np.sign(clipped - clipped.mean())
    assert (np.sign(w) == expected_sign).all()
    assert w[w > 0].sum() == pytest.approx(1.0) and w[w < 0].sum() == pytest.approx(-1.0)
    # the 6.0 and 2.0 would differ without the clip: with it the outlier is only the cap
    capped = pd.Series([2.0, 1.0, 0.5, 0.0, -0.5, -1.0, -2.0, 0.2])
    assert m.target_weights(capped).tolist() == pytest.approx(w.tolist())


def test_buffer_keeps_old_weight_below_threshold_and_trades_above():
    cur = pd.Series({"A": 0.10, "B": 0.10, "C": -0.20, "Z": 0.05})
    tgt = pd.Series({"A": 0.1049, "B": 0.1051, "C": -0.30, "D": 0.004})
    held, traded = m.apply_buffer(tgt, cur)
    assert held["A"] == 0.10  # diff 0.0049 < 0.005: keep
    assert held["B"] == 0.1051  # diff 0.0051: trade
    assert held["C"] == -0.30
    assert "Z" not in held.index  # left the universe: closed
    assert "D" not in held.index  # new name, |0.004 - 0| < 0.005: stays at 0
    assert traded == pytest.approx(abs(0.1051 - 0.10) + abs(-0.30 + 0.20) + 0.05)


def test_cost_only_on_traded_notional():
    k, fund, spot = make()
    row1, held = m.build_week(MON, k, fund, spot, pd.Series(dtype=float), [])
    assert not row1["skipped"]
    assert row1["traded"] == pytest.approx(held.abs().sum()) and row1["traded"] == pytest.approx(
        2.0, abs=0.1
    )
    assert row1["cost_bp"] == pytest.approx(row1["traded"] * 10)
    # same book held again with the buffer wide open is not possible; hold it by passing it as target-equal "previous"
    row2, _ = m.build_week(MON, k, fund, spot, held, [])
    assert row2["traded"] == pytest.approx(0.0, abs=1e-12) and row2["cost_bp"] == pytest.approx(
        0.0, abs=1e-9
    )
    assert row2["net10_bp"] == pytest.approx(row2["gross_bp"] + row2["funding_bp"])
    assert row1["net20_bp"] == pytest.approx(
        row1["gross_bp"] + row1["funding_bp"] - row1["traded"] * 20
    )
    assert row1["net5_bp"] == pytest.approx(
        row1["gross_bp"] + row1["funding_bp"] - row1["traded"] * 5
    )


def test_fewer_than_40_names_is_skipped_and_closes_the_old_book():
    k, fund, spot = make(n=39)
    prev = pd.Series({"S00USDT": 0.5, "S01USDT": -0.5})
    row, held = m.build_week(MON, k, fund, spot, prev, [])
    assert row["skipped"] == 1 and row["names"] == 39 and len(held) == 0
    assert row["gross_bp"] == 0 and row["traded"] == pytest.approx(1.0)
    assert row["net10_bp"] == pytest.approx(-10.0)
    k, fund, spot = make(n=40)
    assert m.build_week(MON, k, fund, spot, pd.Series(dtype=float), [])[0]["skipped"] == 0


def test_universe_is_top_100_by_median_quote_volume():
    k, fund, spot = make(n=105)
    f, cover, _ = m.week_features(k, fund, spot, MON)
    assert len(f) == 100
    top = sorted(k, key=lambda s: -k[s][k[s].index < MON].quote_volume.iloc[-30:].median())[:100]
    assert set(f.index) == set(top)
    assert cover == pytest.approx(f.f3.notna().mean()) and 0 < cover < 1


def test_funding_signal_uses_only_settlements_in_monday_minus_7d_to_monday():
    k, fund, spot = make(n=45)
    s = "S00USDT"
    fr = fund[s].copy()
    lo, hi = MON - pd.Timedelta(days=7), MON
    fr[:] = 0.0
    fr[lo] = 9.0  # excluded: not after Monday - 7 d
    fr[lo + pd.Timedelta(hours=8)] = 0.001  # included
    fr[hi] = 0.002  # included: the Monday 00:00 settlement
    fr[hi + pd.Timedelta(hours=8)] = 7.0  # excluded: after the Monday
    fund[s] = fr
    f, _, _ = m.week_features(k, fund, spot, MON)
    assert f.loc[s, "c"] == pytest.approx(-0.003)


def test_names_without_7_days_of_funding_history_are_out():
    k, fund, spot = make(n=45)
    fund["S03USDT"] = fund["S03USDT"][fund["S03USDT"].index > MON - pd.Timedelta(days=6)]
    f, _, _ = m.week_features(k, fund, spot, MON)
    assert "S03USDT" not in f.index and len(f) == 44


def test_signals_ignore_bars_from_the_monday_on():
    k, fund, spot = make()
    a, _, _ = m.week_features(k, fund, spot, MON)
    k2 = {s: d.copy() for s, d in k.items()}
    for d in k2.values():
        d.loc[d.index >= MON, ["close", "volume", "taker_buy_volume", "quote_volume"]] *= 3
    b, _, _ = m.week_features(k2, fund, spot, MON)
    assert a.drop(columns=[]).equals(b)


def test_appending_future_days_never_changes_a_logged_row():
    k, fund, spot = make(last="2026-12-14")
    row, held = m.build_week(MON, k, fund, spot, pd.Series(dtype=float), [])
    k2, fund2, spot2 = make(last="2026-12-21")
    row2, held2 = m.build_week(MON, k2, fund2, spot2, pd.Series(dtype=float), [])
    assert row == row2 and held.equals(held2)


def run(out, last, start=MON):
    k, fund, spot = make(last=last)
    return m.forward(k, fund, spot, out, start)


def test_forward_says_no_complete_week_and_writes_nothing(tmp_path, capsys):
    run(tmp_path, "2026-12-06")  # next Monday 12-07 is not in the data
    assert "no complete forward week" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_forward_logs_weeks_append_only_and_refuses_changed_out_of_order_data(tmp_path):
    run(tmp_path, "2026-12-07")  # one complete week (11-30)
    first = (tmp_path / "i147.csv").read_text()
    run(tmp_path, "2026-12-07")  # rerun: identical, nothing appended
    assert (tmp_path / "i147.csv").read_text() == first
    run(tmp_path, "2026-12-14")  # a second week appended
    d = pd.read_csv(tmp_path / "i147.csv")
    assert (
        d.period.tolist() == ["2026-11-30", "2026-12-07"]
        and (tmp_path / "i147_weights.csv").exists()
    )
    assert (tmp_path / "i147.csv").read_text().startswith(first)
    k, fund, spot = make(last="2026-12-14")  # changed data under a logged week
    for d in k.values():
        d.loc[MON, "open"] *= 1.1
    with pytest.raises(ValueError, match="changed"):
        m.forward(k, fund, spot, tmp_path)
    # a week before the last logged one
    with pytest.raises(ValueError, match="before the last"):
        k, fund, spot = make(last="2026-12-21")
        row, _ = m.build_week(pd.Timestamp("2026-11-23"), k, fund, spot, pd.Series(dtype=float), [])
        m.forward_log.append(tmp_path / "i147.csv", [row], m.COLS)
    # duplicate period in one append
    with pytest.raises(ValueError, match="duplicate"):
        m.forward_log.append(tmp_path / "x.csv", [row, row], m.COLS)
