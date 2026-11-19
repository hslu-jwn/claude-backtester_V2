"""Cached-only H1-H4 screen. Spec: docs/strategy-share_book_factors.md.

CLI: power | run | test H1 (explicit cell, development gates, one-time marker).
The brief's entry-date boundaries take precedence over calendar-month shorthand.
"""

import argparse
import importlib.util
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


def self_check():
    """Hand-built critical cases, written before the implementation; run at import."""
    f = pd.DataFrame({"sig": range(10), "ret": np.arange(10) * 100.0})
    # Lowest quintile = 50 bp, highest = 850 bp: low-minus-high = -800 bp.
    assert spread(f, "H1") == -800.0
    assert spread(f, "H2") == 900.0
    assert spread(f, "H1", cap=500) == -450.0
    assert np.isnan(spread(f.iloc[:1], "H1"))
    dates = pd.bdate_range("2020-01-01", periods=20)
    market = pd.Series(np.arange(20) / 1000, index=dates)
    stocks = pd.DataFrame({"exact": 0.01 + 2 * market, "short": np.nan})
    stocks.loc[dates[:14], "short"] = market.iloc[:14]
    residual = residual_sd(stocks, market)
    assert residual["exact"] < 1e-14
    assert pd.isna(residual["short"])
    px = pd.DataFrame({"A": [100., np.nan, 120.], "B": [np.nan, 20., 30.]},
                      index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]))
    r = holding_returns(px, pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-03"))
    assert r["A"] == 0 and pd.isna(r["B"])
    # A future exit price must not leak into an earlier missing exit bar.
    assert holding_returns(px.iloc[:2], px.index[0], px.index[1]).equals(r)
    history = pd.DataFrame({"A": [100.] * 251 + [102.], "B": [100.] * 251 + [102.01]})
    assert tax_selection(history).to_dict() == {"A": True, "B": False}
    assert not tax_selection(history.iloc[:0]).any()


spec = importlib.util.spec_from_file_location(
    "i101", Path(__file__).with_name("2026-11-17_i101_short_volume_screen.py")
)
i101 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i101)
closes, tstat = i101.closes, i101.tstat


@dataclass(frozen=True)
class Config:
    start: str = "2016-05-01"
    split: str = "2021-09-14"
    min_common: int = 15
    min_momentum: int = 200
    low_days: int = 252
    low_buffer: float = 0.02
    draws: int = 200
    seed: int = 1
    threshold: float = 3.3
    max_false_positive: float = 0.05
    cap: float = 5000.0
    costs: tuple = (15.0, 15.0, 12.0, 4.0)


CFG = Config()
CELLS = ("H1", "H2", "H3", "H4")


def ordered(f):
    return f.rename_axis("sym").reset_index().sort_values(["sig", "sym"], kind="mergesort")


def buckets(f, cell, cap=None):
    f = ordered(f)
    count = 5 if cell == "H1" else 10
    if len(f) < count:
        return np.full(count, np.nan)
    r = f.ret.clip(-cap, cap) if cap is not None else f.ret
    return np.array([r.iloc[ix].mean() for ix in np.array_split(np.arange(len(f)), count)])


def spread(f, cell, cap=None):
    if cell in ("H1", "H2"):
        b = buckets(f, cell, cap)
        return b[0] - b[-1] if cell == "H1" else b[-1] - b[0]
    r = f.ret.clip(-cap, cap) if cap is not None else f.ret
    if cell == "H3":
        return r[f.selected].mean() - r.mean()
    return r.loc["IWM"] - r.loc["IWB"]


def residual_sd(returns, market):
    """Spec H1: OLS with intercept, pairwise common returns; residual sample sd."""
    y = returns.where(market.notna(), axis=0)
    x = pd.DataFrame(np.broadcast_to(market.to_numpy()[:, None], y.shape),
                     index=y.index, columns=y.columns).where(y.notna())
    dx, dy = x - x.mean(), y - y.mean()
    ssx = dx.pow(2).sum()
    beta = (dx * dy).sum() / ssx.where(ssx > 0)
    residual = dy - dx * beta
    return residual.std(ddof=1).where(y.count() >= CFG.min_common)


def holding_returns(c, entry, exit_day):
    """Spec A4 / I-101 A2: exact entry close; last observed close up to exit."""
    return (c.loc[:exit_day].ffill().iloc[-1] / c.loc[entry] - 1) * 1e4


def tax_selection(history):
    if history.empty:
        return pd.Series(False, index=history.columns)
    low = history.tail(CFG.low_days).min()
    return history.iloc[-1].le(low * (1 + CFG.low_buffer))


def load():
    u = pd.read_csv("data/cache/alpaca_meta/universe.csv")
    c = closes(sorted(set(u.symbol) | {"SPY", "IWM", "IWB"})).sort_index()
    for symbol in ("SPY", "IWM", "IWB"):
        if symbol not in c or c[symbol].dropna().empty:
            raise ValueError(f"Missing cached closes: {symbol}; no downloads permitted")
    c = c.where(np.isfinite(c) & (c > 0))
    days = c.SPY.dropna().index
    return u, c.reindex(days), days


def samples(u, c, days, cells=CELLS, test=False):
    """Spec Common frame / H1-H4: form strictly before entry; realize afterward."""
    out = {cell: [] for cell in cells}
    months = pd.Series(days, index=days).groupby(days.to_period("M"))
    first, last = months.min(), months.max()
    current = pd.Timestamp.now(tz="UTC").tz_localize(None).to_period("M")
    last_complete = min(current - 1, days[-1].to_period("M") - 1)
    daily = c.pct_change(fill_method=None)

    def eligible(e):
        return (e >= pd.Timestamp(CFG.split) and e.to_period("M") <= last_complete
                if test else pd.Timestamp(CFG.start) <= e < pd.Timestamp(CFG.split))

    def members(e):
        return [s for s in u.loc[u.month == e.strftime("%Y-%m"), "symbol"]
                if s in c.columns]

    def add(cell, e, x, f):
        f = f.dropna(subset=["ret"])
        if cell in ("H1", "H2"):
            f = f.dropna(subset=["sig"])
        g = spread(f, cell)
        if cell == "H3" and not np.isfinite(g):
            print(f"H3 {e.date()}: empty basket, no trade (spec A6)")
            return
        if not np.isfinite(g):
            raise ValueError(f"{cell} {e.date()}: insufficient names or empty basket")
        market = holding_returns(c[["SPY"]], e, x).iloc[0]
        out[cell].append((e, f, market))

    for m, e in first.items():
        if not eligible(e) or m + 1 not in first.index:
            continue
        x = first.loc[m + 1]
        syms = members(e)
        for cell in set(cells) & {"H1", "H2"}:
            if cell == "H1":
                previous = daily.loc[daily.index.to_period("M") == m - 1, syms]
                signal = residual_sd(previous, daily.SPY.reindex(previous.index))
            else:
                if m - 13 not in last.index or m - 2 not in last.index:
                    continue
                a, b = last.loc[m - 13], last.loc[m - 2]
                history = c.loc[a:b, syms]
                signal = (c.loc[b, syms] / c.loc[a, syms] - 1).where(
                    history.count() >= CFG.min_momentum)
            add(cell, e, x, pd.DataFrame({"sig": signal,
                                        "ret": holding_returns(c[syms], e, x)}))

    for year in sorted(set(days.year)):
        december = days[(days.year == year) & (days.month == 12)]
        if len(december) < 11:
            continue
        if "H3" in cells:
            events = december[december.day >= 15]
            exits = days[(days.year == year + 1) & (days.month == 2) & (days.day >= 15)]
            if len(events) and len(exits) and eligible(events[0]):
                e, x = events[0], exits[0]
                syms = members(e)
                # A5: excludes entry close; window is the previous 252 SPY trade dates.
                selected = tax_selection(c.loc[c.index < e, syms].tail(CFG.low_days))
                add("H3", e, x, pd.DataFrame({"selected": selected,
                                             "ret": holding_returns(c[syms], e, x)}))
        if "H4" in cells and eligible(december[10]):
            if pd.Period(year=year, month=12, freq="M") > last_complete:
                continue
            e, x = december[10], december[-1]
            # Both ETFs must have the registered entry close; no synthetic entry fills.
            add("H4", e, x, pd.DataFrame({"ret": holding_returns(c[["IWM", "IWB"]], e, x)}))
    return out


def safe_t(x):
    x = np.asarray(x, float)
    if len(x) < 2 or not np.isfinite(x).all():
        return np.nan
    if x.std(ddof=1) == 0:
        return np.copysign(np.inf, x.mean()) if x.mean() else 0.0
    return float(tstat(x))


def power(data):
    """Spec Gates: shuffle signal labels within each month, 200 draws, gross null t."""
    rng = np.random.default_rng(CFG.seed)
    passed = {}
    for cell in ("H1", "H2"):
        ws = data[cell]
        if not ws:
            raise ValueError(f"No development observations for {cell}")
        random_spreads = []
        # Sorting shuffled labels is equivalent to permuting returns into fixed rank buckets.
        count = 5 if cell == "H1" else 10
        for _ in range(CFG.draws):
            draw = []
            for _, f, _ in ws:
                r = rng.permutation(f.ret.to_numpy())
                b = [r[ix].mean() for ix in np.array_split(np.arange(len(r)), count)]
                draw.append(b[0] - b[-1] if cell == "H1" else b[-1] - b[0])
            random_spreads.append(draw)
        sd = np.mean(np.std(random_spreads, axis=1, ddof=1))
        rate = np.mean([abs(safe_t(draw)) >= CFG.threshold for draw in random_spreads])
        passed[cell] = bool(rate <= CFG.max_false_positive)
        names = [len(f) for _, f, _ in ws]
        se = sd / np.sqrt(len(ws))
        print(f"{cell}: months {len(ws)} ({ws[0][0].date()} .. {ws[-1][0].date()}), "
              f"names min {min(names)} median {int(np.median(names))}; POWER: "
              f"shuffled-label draws {CFG.draws}, sd {sd:.1f} bp, se {se:.1f}; "
              f"|t| 3.3 needs {CFG.threshold * se:.1f} bp/month net (+ 15 cost); "
              f"share |t| >= 3.3 {rate:.1%} (<= 5%): "
              f"{'PASSED' if passed[cell] else 'KILLED'}", flush=True)
    return passed


def run(data, controls, test=False):
    passed = {}
    for cell, ws in data.items():
        if not ws:
            raise ValueError(f"No observations for {cell}")
        cost = CFG.costs[CELLS.index(cell)]
        idx = pd.DatetimeIndex([e for e, _, _ in ws])
        g = pd.Series([spread(f, cell) for _, f, _ in ws], index=idx)
        capped = np.mean([spread(f, cell, CFG.cap) for _, f, _ in ws]) - cost
        net = g - cost
        t = safe_t(net)
        cut = 2018 if cell in ("H1", "H2") else 2017
        if test:
            h1, h2 = [s.mean() for s in np.array_split(net.to_numpy(), 2)]
        else:
            h1, h2 = net[idx.year <= cut].mean(), net[idx.year > cut].mean()
        doubled = (g - 2 * cost).mean()
        nb = net.drop(net.nlargest(2).index).mean()
        kills = {
            "|t| < 3.3": not abs(t) >= CFG.threshold,
            "net <= 0 / wrong sign": not net.mean() > 0,
            "halves": not (h1 > 0 and h2 > 0),
            "doubled cost <= 0": not doubled > 0,
            "without 2 best <= 0": not nb > 0,
        }
        if cell in ("H1", "H2"):
            kills["shuffled-label control"] = not controls[cell]
        hit = [k for k, v in kills.items() if v]
        passed[cell] = not hit
        market = np.array([m for _, _, m in ws])
        beta = np.cov(g, market, ddof=1)[0, 1] / np.var(market, ddof=1)
        print(f"\ncell {cell}: n {len(g)}; gross {g.mean():+.1f} bp/period; "
              f"net {net.mean():+.1f}, t {t:.2f}, sd {net.std(ddof=1):.1f}, "
              f"positive {100 * (net > 0).mean():.0f} %; halves {h1:+.1f} / {h2:+.1f}; "
              f"doubled cost {doubled:+.1f}; without 2 best {nb:+.1f}")
        print("  kills hit:", hit or "none", "->",
              "KILLED" if hit else f"PASSED ({'test' if test else 'development'})")
        print(f"  reported: capped +-50 % net {capped:+.1f}; beta to SPY {beta:.3f}; "
              f"years {net.groupby(idx.year).mean().round(1).to_dict()}")
        if cell in ("H1", "H2"):
            means = np.mean([buckets(f, cell) for _, f, _ in ws], axis=0)
            print(f"  {'quintile' if cell == 'H1' else 'decile'} gross means "
                  f"(bp, 1 = lowest signal): {np.round(means, 1).tolist()}")
        elif cell == "H3":
            print("  selected basket sizes:", [int(f.selected.sum()) for _, f, _ in ws])
    return passed


self_check()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("power", "run", "test"))
    parser.add_argument("cell", nargs="?", choices=CELLS)
    args = parser.parse_args()
    if (args.step == "test") != (args.cell is not None):
        parser.error("test requires one explicit cell (e.g. test H1); power/run take no cell")
    u, c, days = load()
    dev = samples(u, c, days, cells=("H1", "H2") if args.step == "power" else CELLS)
    controls = power(dev)
    if args.step == "power":
        return
    passed = run(dev, controls)
    if args.step == "test":
        if not passed[args.cell]:
            parser.error(f"{args.cell} failed development gates; test refused")
        marker = Path("results") / f"2026-11-19_share_book_factors_{args.cell}_test.txt"
        marker.parent.mkdir(exist_ok=True)
        # Exclusive creation prevents accidental repeats, including after an interrupted test.
        with marker.open("x", encoding="utf-8") as stream:
            stream.write(f"One-time test consumed: {args.cell}\n")
        result = samples(u, c, days, cells=(args.cell,), test=True)
        run(result, controls, test=True)


if __name__ == "__main__":
    main()

