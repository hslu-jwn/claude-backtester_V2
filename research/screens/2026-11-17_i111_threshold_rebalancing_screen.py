"""I-111 threshold rebalancing on US500 (rule fixed in knowledge/ideas.md, 496b4eb). Development only.

Signal: Harvey, Mazzoleni & Melone (NBER w33554) eq. 2 from US500 cash closes and FRED DGS10 par-bond returns.
Steps: power (signal-free permutation), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i111_threshold_rebalancing_screen.py power | run
"""

import importlib.util
import sys
from datetime import UTC, date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).parent / "2026-11-17_i109_treasury_month_end_screen.py"
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)

NY = ZoneInfo("America/New_York")
CFG = CostConfig()
BANDS = np.round(np.arange(0, 2.51, 0.1), 1) / 100
TARGET, SCALE = 0.60, 0.015
CACHE = Path("data/cache/i111_closes.pkl")


def cash_closes():
    """US500 last M1 close <= 16:00 New York per weekday (as I-70): Series day -> (close, close time)."""
    if CACHE.exists():
        return pd.read_pickle(CACHE)
    out = {}
    for src, a, b in (
        (SymbolSources.single("data/cache/histdata_presample", ["US500"]), date(2010, 1, 1), date(2014, 12, 31)),
        (DEFAULT_SOURCES, date(2015, 1, 1), date(2021, 9, 13)),
    ):
        d = load_m1("US500", src, a, b)
        for open_s, c in zip(d.open_s.tolist(), d.close.tolist(), strict=True):
            t = datetime.fromtimestamp(open_s + 60, UTC).astimezone(NY)
            if time(9, 30) < t.time() <= time(16, 0) and t.weekday() < 5:
                out[pd.Timestamp(t.date())] = (c, open_s + 60)
    s = pd.DataFrame(out, index=["close", "ts"]).T.sort_index()
    s.to_pickle(CACHE)
    return s


def table():
    c = cash_closes()
    bond = i109.returns("DGS10", "2009-12-01", "2021-09-13") / 1e4
    d = c.join(bond.rename("rb"), how="inner")
    d["rs"] = d.close.pct_change()
    return d.dropna()


def signal(rs, rb):
    """Mean over bands of the 60/40 equity-weight deviation (pre-reset on a reset day)."""
    w = np.full(len(BANDS), TARGET)
    out = np.empty(len(rs))
    for i, (a, b) in enumerate(zip(rs, rb, strict=True)):
        w = w * (1 + a) / (w * (1 + a) + (1 - w) * (1 + b))
        dev = w - TARGET
        out[i] = dev.mean()
        w = np.where(np.abs(dev) > BANDS, TARGET, w)
    return out


def pnl(d, s, cost_mult=1.0):
    """Daily gross / net bp of p = clip(-S / 1.5 %, -1, 1) held close -> next close."""
    p = np.clip(-s / SCALE, -1, 1)
    nxt = d.rs.shift(-1).to_numpy() * 1e4
    triple = CFG.for_symbol("US500").swap_triple_weekday
    net = np.full(len(d), np.nan)
    gross = p * nxt
    px, ts = d.close.to_numpy(float), d.ts.to_numpy(float)
    prev = 0.0
    for i in range(len(d) - 1):
        fill = (CFG.spread("US500", price=px[i]) / 2 + CFG.slippage("US500", px[i])) / px[i] * 1e4
        nights = rollover_nights(
            datetime.fromtimestamp(ts[i], UTC), datetime.fromtimestamp(ts[i + 1], UTC), triple
        )
        side = Direction.BULLISH if p[i] >= 0 else Direction.BEARISH
        swap = CFG.swap_r_nights("US500", side, px[i], nights, px[i]) * 1e4  # negative = cost
        net[i] = gross[i] - cost_mult * (abs(p[i] - prev) * fill - abs(p[i]) * swap)
        prev = p[i]
    return pd.Series(gross, index=d.index)[:-1], pd.Series(net, index=d.index)[:-1], p


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power():
    d = table()
    s = signal(d.rs.to_numpy(), d.rb.to_numpy())
    rng = np.random.default_rng(1)
    means = [pnl(d, rng.permutation(s))[0].mean() for _ in range(200)]
    g = pnl(d, rng.permutation(s))[0]
    se = np.std(means, ddof=1)
    print(
        f"days {len(d)} ({d.index[0].date()} .. {d.index[-1].date()}); S sd {s.std() * 100:.2f} %, mean |p| "
        f"{np.abs(np.clip(-s / SCALE, -1, 1)).mean():.2f}; permuted gross sd/day {g.std():.0f} bp, se of the mean "
        f"{se:.2f} bp: t 3 needs {3 * se:.2f} bp/day net"
    )


def run():
    d = table()
    s = signal(d.rs.to_numpy(), d.rb.to_numpy())
    g, n, p = pnl(d, s)
    _, n2, _ = pnl(d, s, 2.0)
    t = tstat(n)
    h1, h2 = n[n.index.year <= 2015].mean(), n[n.index.year >= 2016].mean()
    nb = n.drop(n.nlargest(2).index).mean()
    kills = {
        "net <= 0": n.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2.mean() <= 0,
        "without 2 best <= 0": nb <= 0,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"days {len(n)}: gross {g.mean():+.2f} bp/day (t {tstat(g):.2f}), net {n.mean():+.2f}, t {t:.2f}; halves "
        f"{h1:+.2f} / {h2:+.2f}; doubled {n2.mean():+.2f}; without 2 best {nb:+.2f} -> "
        f"{'KILLED ' + str(hit) if hit else 'PASSED (development)'}"
    )
    paired = pd.Series(p[:-1] * (d.rs - d.rb).shift(-1).to_numpy()[:-1] * 1e4, index=n.index)
    covid = n.drop(n.loc["2020-02-20":"2020-04-30"].index)
    print(
        f"reported: paired leg gross {paired.mean():+.2f} (t {tstat(paired):.2f}); net without 2020-02-20..04-30 "
        f"{covid.mean():+.2f} (t {tstat(covid):.2f}); mean |p| {np.abs(p).mean():.2f}; by year "
        f"{n.groupby(n.index.year).mean().round(2).to_dict()}"
    )


if __name__ == "__main__":
    {"power": power, "run": run}[sys.argv[1]]()
