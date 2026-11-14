"""I-75 screen: weekly cross-sectional reversal on 37 Binance perps (knowledge/ideas.md › I-75).

Rule and kills pre-registered in the card (commit 68f9726) before this script ran. Signal = prior-week return
(previous Monday 00:00 bar close -> this Monday 00:00 bar close); long the floor(N/5) losers, short the floor(N/5)
winners; hold to Sunday 23:59; net = price + funding - 20 bp. Development only (Sunday exit before 2021-09-14).
Kills: net <= 0; t < 3.0; halves opposite; net <= 0 without the 2 best weeks.
`--power`: signal-free weekly sd of random legs of the same sizes (recorded in the card before the screen).
Run: .venv/Scripts/python.exe research/screens/2026-11-14_i75_crypto_reversal_screen.py [--power]
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s = _load("i73", "2026-11-13_i73_crypto_carry_xs_screen.py")
R20 = _load("i73r", "2026-11-14_i73r_replication.py").R20
SYMS = list(s.SYMBOLS) + list(R20)
END = pd.Timestamp("2021-09-14", tz="UTC")
M, D = pd.Timedelta(minutes=1), pd.Timedelta(days=1)


def weeks(symbols=SYMS):
    """Per Monday: {symbol: (prior-week return bp, held return bp, funding bp paid by a long)}."""
    fr = {sym: s.funding(sym) for sym in symbols}
    first = min(f.index[0] for f in fr.values()).normalize()
    monday = first + pd.Timedelta(days=(7 - first.weekday()) % 7)
    out = {}
    while monday + 7 * D <= END:
        rows = {}
        for sym, f in fr.items():
            if f.index[0] > monday - 30 * D:
                continue
            p0, p1 = s.close_at(sym, monday - 7 * D), s.close_at(sym, monday)
            if not p0 or not p1:
                continue
            pe = s.close_at(sym, monday + 7 * D - 2 * M)
            held = f[(f.index > monday + M) & (f.index <= monday + 7 * D - M)]
            rows[sym] = (
                (p1 / p0 - 1) * 1e4,
                (pe / p1 - 1) * 1e4 if pe else np.nan,
                held.sum() * 1e4,
            )
        if len(rows) >= 10:
            out[monday] = rows
        monday += 7 * D
    return out


def book(ws):
    rec = []
    for monday, rows in ws.items():
        ranked = sorted(rows, key=lambda k: rows[k][0])  # stable: universe order on ties
        n = len(rows) // 5
        p, f = s.leg_parts(rows, ranked[:n], ranked[-n:])
        rec.append((monday, p, f, p + f - s.COST_BP, n))
    return pd.DataFrame(rec, columns=["monday", "price", "fund", "net", "n"]).set_index("monday")


def power(ws):
    rng = np.random.default_rng(75)
    sds = []
    for _ in range(200):
        net = []
        for rows in ws.values():
            pick, n = list(rng.permutation(sorted(rows))), len(rows) // 5
            p, f = s.leg_parts(rows, pick[:n], pick[n : 2 * n])
            net.append(p + f - s.COST_BP)
        sds.append(np.nanstd(net, ddof=1))
    sd = float(np.median(sds))
    se = sd / np.sqrt(len(ws))
    print(f"weeks {len(ws)}, eligible {min(map(len, ws.values()))}-{max(map(len, ws.values()))}")
    print(
        f"random-leg weekly sd {sd:.0f} bp -> standard error {se:.0f} bp; t 3 needs {3 * se:.0f} bp a week"
    )


if __name__ == "__main__":
    ws = weeks()
    if "--power" in sys.argv:
        power(ws)
        sys.exit()
    d = book(ws)
    empty = int(d.net.isna().sum())
    d = d.dropna()
    half, drop2 = len(d) // 2, d.net.drop(d.net.nlargest(2).index)
    print(
        f"weeks {len(d)} ({d.index[0].date()} .. {d.index[-1].date()}), skipped (empty leg) {empty}, per leg {d.n.min()}-{d.n.max()}"
    )
    print(
        f"net {d.net.mean():+.1f} bp/week  t {s.tstat(d.net):+.2f}  price {d.price.mean():+.1f}  funding {d.fund.mean():+.1f}"
        f"  win {np.mean(d.net > 0):.2f}  sd {d.net.std():.0f}  worst {d.net.min():+.0f}"
    )
    print(
        f"halves {d.net.iloc[:half].mean():+.1f} / {d.net.iloc[half:].mean():+.1f}  without 2 best {drop2.mean():+.1f}"
    )
    kills = {
        "net <= 0": d.net.mean() <= 0,
        "t < 3.0": s.tstat(d.net) < 3.0,
        "halves opposite": np.sign(d.net.iloc[:half].mean()) != np.sign(d.net.iloc[half:].mean()),
        "without 2 best <= 0": drop2.mean() <= 0,
    }
    print(
        "kills:",
        {k: bool(v) for k, v in kills.items()},
        "->",
        "KILLED" if any(kills.values()) else "PASSES the screen",
    )
    print(d.groupby(d.index.year).net.agg(["mean", "count"]).round(1).to_string())
    d17 = book(weeks(list(s.SYMBOLS))).dropna()
    i73 = s.screen(s.weeks(), quiet=True).net
    both = pd.concat([d.net, i73], axis=1, join="inner")
    print(
        f"diagnostics: 17-symbol universe net {d17.net.mean():+.1f} t {s.tstat(d17.net):+.2f}; "
        f"correlation with I-73 development weeks {both.corr().iloc[0, 1]:+.2f} (n {len(both)})"
    )
