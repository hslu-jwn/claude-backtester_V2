"""I-101 FINRA short-volume ratio, weekly cross-sectional sort (Fable card 3; rule fixed in knowledge/ideas.md, 5ebefb7).

Development only (2015-10-01 .. 2021-09-13); universe docs/share-universe.md (card 2 output
data/cache/alpaca_meta/universe.csv); prices Alpaca daily closes (data/cache/alpaca_1d).
Steps: finra (download every trading day's files, one request at a time), power (signal-free random deciles),
run (both cells, kills, reported diagnostics).
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i101_short_volume_screen.py finra | power | run
"""

import itertools
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FINRA = Path("data/cache/finra/daily")
D1 = Path("data/cache/alpaca_1d")
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
START, END, BREAK = (
    pd.Timestamp("2015-10-01"),
    pd.Timestamp("2021-09-13"),
    pd.Timestamp("2018-08-01"),
)
COST, WIN, BASE, MIN_WIN, MIN_BASE = 13.0, 5, 60, 4, 40


def get(url):
    r = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}", url], capture_output=True, timeout=120, check=True
    )
    body, _, code = r.stdout.rpartition(b"\n")
    return body if code == b"200" else None if code in (b"403", b"404") else RuntimeError(code)


def finra():
    """Every weekday in the development window; a day with no file at all is a market holiday."""
    FINRA.mkdir(parents=True, exist_ok=True)
    missing = []
    for day in pd.bdate_range(START, END):
        ds = day.strftime("%Y%m%d")
        feeds = ["CNMS"] if day >= BREAK else ["FNSQ", "FNYX"]
        got = []
        for f in feeds:
            path = FINRA / f"{f}shvol{ds}.txt"
            if not path.exists():
                body = get(f"https://cdn.finra.org/equity/regsho/daily/{f}shvol{ds}.txt")
                if isinstance(body, Exception):
                    raise body
                if body:
                    path.write_bytes(body)
            got.append(path.exists())
        if any(got) and not all(got):
            missing.append(ds)
        if day.day == 1 or day == END:
            print(f"finra up to {ds}", flush=True)
    print(f"days with only part of the facility files: {missing or 'none'}")


def short_volume():
    """Daily table day x symbol: ShortVolume, TotalVolume (facilities summed)."""
    rows = []
    for p in sorted(FINRA.glob("*shvol*.txt")):
        day = pd.Timestamp(p.stem[-8:])
        if not (START <= day <= END) or (p.stem[:4] == "CNMS") != (day >= BREAK):
            continue
        d = pd.read_csv(
            p, sep="|", usecols=["Symbol", "ShortVolume", "TotalVolume"], dtype={"Symbol": str}
        )
        d = d[d.Symbol.str.fullmatch(r"[A-Z]+(/[A-Z])?", na=False)]
        d["day"] = day
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    d["symbol"] = d.Symbol.str.replace("/", ".", regex=False)
    g = d.groupby(["day", "symbol"])[["ShortVolume", "TotalVolume"]].sum()
    return g.ShortVolume.unstack(), g.TotalVolume.unstack()


def closes(symbols):
    out = {}
    for s in symbols:
        p = D1 / f"{s}.csv"
        if p.exists() and p.stat().st_size > 60:
            d = pd.read_csv(p, usecols=["ts", "close"])
            day = (
                pd.to_datetime(d.ts, utc=True)
                .dt.tz_convert("America/New_York")
                .dt.tz_localize(None)
                .dt.normalize()
            )
            out[s] = pd.Series(d.close.to_numpy(float), index=day)
    return pd.DataFrame(out)


def weeks():
    """Per week: entry day, exit day, frame of names (symbol, signal, ret in bp)."""
    sv, tv = short_volume()
    days = sv.index  # trading days with FINRA files
    u = pd.read_csv(UNIVERSE)
    c = closes(sorted(u.symbol.unique()))
    daily_svr = (sv / tv.where(tv > 0)).reindex(days)
    wk = (
        pd.Series(days, index=days).groupby(days.to_period("W-SUN")).min()
    )  # first trading day of each week
    entries = list(wk.to_numpy())
    out = []
    for e, x in itertools.pairwise(entries):
        i = days.get_loc(e)
        if i < WIN + BASE:
            continue
        win, base = days[i - WIN : i], days[i - WIN - BASE : i - WIN]
        if (win[0] < BREAK <= win[-1]) or (base[0] < BREAK <= win[-1]):
            continue
        if x > END or pd.Timestamp(e) < pd.Timestamp("2016-01-01"):
            continue
        members = u[u.month == pd.Timestamp(e).strftime("%Y-%m")].symbol
        members = [m for m in members if m in daily_svr.columns and m in c.columns]
        w = daily_svr.loc[win, members]
        b = daily_svr.loc[base, members]
        ok = (w.notna().sum() >= MIN_WIN) & (b.notna().sum() >= MIN_BASE)
        swin = sv.loc[win, members].sum() / tv.loc[win, members].sum()
        sig = (swin - b.mean())[ok]
        px = c[sig.index]
        p0 = px.loc[:e].iloc[-1] if e in px.index else None
        if p0 is None:
            continue
        p1 = px.loc[:x].ffill().iloc[-1]  # A2: no exit bar -> last close
        ret = ((p1 / p0 - 1) * 1e4).where(px.loc[e].notna())
        f = pd.DataFrame({"sig": sig, "ret": ret}).dropna()
        if len(f) >= 100:
            out.append((pd.Timestamp(e), f))
    return out


def spread(f, cap=None):
    f = f.reset_index(names="sym").sort_values(["sig", "sym"], kind="mergesort")
    n = len(f) // 10
    r = f.ret.clip(-cap, cap) if cap else f.ret
    return r.iloc[:n].mean() - r.iloc[-n:].mean()  # cell A: long low SVR, short high


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power(ws):
    rng = np.random.default_rng(1)
    sds = []
    for _ in range(200):
        sp = []
        for _, f in ws:
            r = rng.permutation(f.ret.to_numpy())
            n = len(r) // 10
            sp.append(r[:n].mean() - r[-n:].mean())
        sds.append(np.std(sp, ddof=1))
    sd = float(np.mean(sds))
    se = sd / np.sqrt(len(ws))
    names = [len(f) for _, f in ws]
    print(
        f"weeks {len(ws)} ({ws[0][0].date()} .. {ws[-1][0].date()}), names per week min {min(names)} median "
        f"{int(np.median(names))}; POWER: random-decile weekly sd {sd:.0f} bp, se {se:.1f}; |t| 3.3 needs "
        f"{3.3 * se:.0f} bp a week net (+ {COST:.0f} cost)"
    )


def run(ws):
    idx = [e for e, _ in ws]
    g = pd.Series([spread(f) for _, f in ws], index=idx)
    gc = pd.Series([spread(f, 5000) for _, f in ws], index=idx)
    print(
        f"weeks {len(g)}; gross cell A (long low SVR) {g.mean():+.1f} bp/week, gross t {tstat(g):.2f}"
    )
    for cell, d in (("A long low SVR / short high", 1), ("B long high SVR / short low", -1)):
        net = d * g - COST
        t = tstat(net)
        h1, h2 = net[net.index.year <= 2018].mean(), net[net.index.year >= 2019].mean()
        n2 = (d * g - 2 * COST).mean()
        nb = net.drop(net.nlargest(2).index).mean()
        kills = {
            "t < 3.3": t < 3.3,
            "net <= 0": net.mean() <= 0,
            "halves": not (h1 > 0 and h2 > 0),
            "doubled cost <= 0": n2 <= 0,
            "without 2 best <= 0": nb <= 0,
        }
        hit = [k for k, v in kills.items() if v]
        print(
            f"\ncell {cell}: net {net.mean():+.1f} bp/week, t {t:.2f}, sd {net.std(ddof=1):.0f}, positive "
            f"{100 * (net > 0).mean():.0f} %; halves {h1:+.1f} / {h2:+.1f}; doubled cost {n2:+.1f}; without 2 best "
            f"{nb:+.1f}"
        )
        print("  kills hit:", hit or "none", "->", "KILLED" if hit else "PASSED (development)")
        print(
            f"  reported: capped +-50 % net {(d * gc - COST).mean():+.1f}; smallest half / mean "
            f"{min(h1, h2) / net.mean():.2f}; years {net.groupby(net.index.year).mean().round(1).to_dict()}"
        )
    dec = []
    for _, f in ws:
        f = f.reset_index(names="sym").sort_values(["sig", "sym"], kind="mergesort")
        dec.append([f.ret.iloc[i].mean() for i in np.array_split(np.arange(len(f)), 10)])
    print(
        "\ndecile mean next-week return (bp, 1 = lowest SVR):",
        np.round(np.mean(dec, axis=0), 1).tolist(),
    )


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "finra":
        finra()
    else:
        ws = weeks()
        power(ws) if step == "power" else run(ws)
