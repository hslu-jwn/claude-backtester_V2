"""I-102 overnight -> 10:00 reversal on the wide US share universe at real-share cost (Fable card 4; rule fixed in
knowledge/ideas.md, 4de0afc).

Development only: trading days 2016-01-04 .. 2021-09-13. Universe docs/share-universe.md (universe.csv of card 2).
Prices: previous close and exit = Alpaca daily close (data/cache/alpaca_1d); the 10:00 price = close of the last
1-min bar before 10:00 ET and the entry = open of the first 1-min bar from 10:00, both from one narrow multi-symbol
request per trading day and 500 names (09:57-10:03 ET; data/cache/alpaca_ten/<day>.csv; share-universe A7); the
09:30 open of the diagnostic = Alpaca's daily open. SPY from the same sources.
Steps: ten (download the 10:00 prices), extract (one compact table, cached), power, run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i102_open_reversal_screen.py ten | extract | power | run
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import alpaca

D1 = Path("data/cache/alpaca_1d")
TEN = Path("data/cache/alpaca_ten")
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
TABLE = Path("data/cache/alpaca_meta/i102_prices.pkl")
START, END = pd.Timestamp("2016-01-04"), pd.Timestamp("2021-09-13")
COST, MIN_NAMES = 7.0, 500


def ten():
    """Per trading day: c_before (close of the last 1-min bar before 10:00 ET), o_after (open of the first from 10:00)."""
    from zoneinfo import ZoneInfo

    fetch = alpaca.http_fetch(*alpaca.keys())
    alpaca.download_batch(["SPY"], "1Day", "2015-07-01", fetch, D1)
    days = pd.read_csv(D1 / "SPY.csv", usecols=["ts"]).ts.pipe(ny).dt.normalize()
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(sorted).to_dict()
    TEN.mkdir(parents=True, exist_ok=True)
    for d in days[(days >= pd.Timestamp("2016-04-01")) & (days <= END)]:
        path = TEN / f"{d:%Y-%m-%d}.csv"
        if path.exists():
            continue
        t0 = (
            d.replace(hour=9, minute=57).tz_localize(ZoneInfo("America/New_York")).tz_convert("UTC")
        )
        t1 = t0 + pd.Timedelta(minutes=6)
        syms = members.get(f"{d:%Y-%m}", []) + ["SPY"]
        rows = []
        for k in range(0, len(syms), 500):
            params = {
                "symbols": ",".join(syms[k : k + 500]),
                "timeframe": "1Min",
                "limit": 10000,
                "start": f"{t0:%Y-%m-%dT%H:%M:00Z}",
                "end": f"{t1:%Y-%m-%dT%H:%M:00Z}",
                "adjustment": "split",
                "feed": "sip",
            }
            while True:
                page = fetch(params)
                for sym, bars in (page.get("bars") or {}).items():
                    rows += [(sym, b["t"], b["o"], b["c"]) for b in bars]
                if not page.get("next_page_token"):
                    break
                params = {**params, "page_token": page["next_page_token"]}
        b = pd.DataFrame(rows, columns=["symbol", "ts", "open", "close"])
        ten_utc = t0 + pd.Timedelta(minutes=3)
        b["after"] = pd.to_datetime(b.ts, utc=True) >= ten_utc
        before = b[~b.after].groupby("symbol").close.last()
        after = b[b.after].groupby("symbol").open.first()
        out = pd.DataFrame({"c_before": before, "o_after": after}).rename_axis("symbol")
        out.to_csv(path.with_suffix(".part"))
        path.with_suffix(".part").replace(path)
        if d.day == 1 or d == END:
            print(f"ten {d.date()}: {len(out)} symbols", flush=True)


def ny(ts):
    return pd.to_datetime(ts, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None)


def extract():
    """day x symbol tables: prev_close, close, o0930 (daily open), c0930 (10:00 price), o1000 (entry)."""
    syms = sorted(set(pd.read_csv(UNIVERSE).symbol) | {"SPY"})
    cols = {"close": {}, "o0930": {}}
    for s in syms:
        p1 = D1 / f"{s}.csv"
        if not p1.exists() or p1.stat().st_size < 60:
            continue
        d = pd.read_csv(p1, usecols=["ts", "open", "close"])
        d.index = ny(d.ts).dt.normalize()
        d = d[~d.index.duplicated()]
        cols["close"][s], cols["o0930"][s] = d.close, d.open
    out = {k: pd.DataFrame(v).sort_index() for k, v in cols.items()}
    days = out["close"]["SPY"].dropna().index
    out = {k: v.reindex(days) for k, v in out.items()}
    out["prev_close"] = out["close"].shift(
        1
    )  # previous market session's close (NaN if the name did not trade)
    ten = {
        pd.Timestamp(p.stem): pd.read_csv(p, index_col="symbol") for p in sorted(TEN.glob("*.csv"))
    }
    for k, col in (("c0930", "c_before"), ("o1000", "o_after")):
        out[k] = pd.DataFrame({d: f[col] for d, f in ten.items()}).T.reindex(
            index=days, columns=out["close"].columns
        )
    pd.to_pickle(out, TABLE)
    print(
        f"extracted {len(out['close'].columns)} symbols x {len(days)} days ({len(ten)} days with 10:00 prices)"
    )


def day_frames(entry="o1000", signal="c0930"):
    t = pd.read_pickle(TABLE)
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(list).to_dict()
    days = [d for d in t["close"].index if START <= d <= END]
    out = []
    for d in days:
        m = [s for s in members.get(d.strftime("%Y-%m"), []) if s in t["close"].columns]
        pc, sg, en, cl = (t[k].loc[d, m] for k in ("prev_close", signal, entry, "close"))
        spy_r = t[signal].loc[d, "SPY"] / t["prev_close"].loc[d, "SPY"] - 1
        f = pd.DataFrame({"s": sg / pc - 1 - spy_r, "r": (cl / en - 1) * 1e4}).dropna()
        if len(f) >= MIN_NAMES and np.isfinite(spy_r):
            out.append((d, f))
    return out


def spread(f):
    f = f.reset_index(names="sym").sort_values(["s", "sym"], kind="mergesort")
    n = len(f) // 10
    return f.r.iloc[:n].mean() - f.r.iloc[-n:].mean()  # long the lowest s, short the highest


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power(ws):
    rng = np.random.default_rng(1)
    sds = []
    for _ in range(100):
        sp = []
        for _, f in ws:
            r = rng.permutation(f.r.to_numpy())
            n = len(r) // 10
            sp.append(r[:n].mean() - r[-n:].mean())
        sds.append(np.std(sp, ddof=1))
    sd = float(np.mean(sds))
    se = sd / np.sqrt(len(ws))
    names = [len(f) for _, f in ws]
    print(
        f"days {len(ws)} ({ws[0][0].date()} .. {ws[-1][0].date()}), names per day min {min(names)} median "
        f"{int(np.median(names))}; POWER: random-decile daily sd {sd:.0f} bp, se {se:.2f}; t 3 needs {3 * se:.1f} bp "
        f"a day net (+ {COST:.0f} cost)"
    )


def run(ws):
    idx = [d for d, _ in ws]
    g = pd.Series([spread(f) for _, f in ws], index=idx)
    net = g - COST
    t = tstat(net)
    h1, h2 = net[net.index.year <= 2018].mean(), net[net.index.year >= 2019].mean()
    n2 = (g - 2 * COST).mean()
    nb = net.drop(net.nlargest(2).index).mean()
    kills = {
        "net <= 0": net.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2 <= 0,
        "without 2 best <= 0": nb <= 0,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"days {len(g)}: gross {g.mean():+.2f} bp/day (gross t {tstat(g):.2f}), cost {COST:.0f}, net {net.mean():+.2f}, "
        f"t {t:.2f}, sd {net.std(ddof=1):.0f}; halves {h1:+.2f} / {h2:+.2f}; doubled cost {n2:+.2f}; "
        f"without 2 best {nb:+.2f}"
    )
    print("kills hit:", hit or "none", "->", "KILLED" if hit else "PASSED (development)")
    print(
        f"reported: smallest half / mean {min(h1, h2) / net.mean():.2f}; gross by year "
        f"{g.groupby(g.index.year).mean().round(2).to_dict()}"
    )
    dec = []
    for _, f in ws:
        f = f.reset_index(names="sym").sort_values(["s", "sym"], kind="mergesort")
        dec.append([f.r.iloc[i].mean() for i in np.array_split(np.arange(len(f)), 10)])
    print(
        "deciles of s, mean 10:00 -> close (bp, 1 = lowest):",
        np.round(np.mean(dec, axis=0), 1).tolist(),
    )
    go = day_frames(entry="o0930", signal="o0930")
    go_g = pd.Series([spread(f) for _, f in go], index=[d for d, _ in go])
    print(
        f"open timing (I-96: sort on 09:30 open, open -> close): gross {go_g.mean():+.2f}, gross t {tstat(go_g):.2f}, "
        f"by year {go_g.groupby(go_g.index.year).mean().round(2).to_dict()}"
    )


if __name__ == "__main__":
    step = sys.argv[1]
    if step in ("ten", "extract"):
        {"ten": ten, "extract": extract}[step]()
    else:
        ws = day_frames()
        power(ws) if step == "power" else run(ws)
