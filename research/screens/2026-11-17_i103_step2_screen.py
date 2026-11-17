"""I-103 step 2 (Fable card 7): follow the day's direction from 15:30 to the close on name-days whose leveraged-fund
rebalance flow is >= 5 % of the 15:30-16:00 dollar volume. Rule and kills fixed in knowledge/ideas.md (1b78850,
step 2 assumptions b263bef); events from step 1 (`flows()`). Development 2022-07 .. 2024-12-31 only.
Steps: fetch (15:27-15:31 minute bars on the event dates for the universe), power (signal-free), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i103_step2_screen.py fetch | power | run
"""

import importlib.util
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data import alpaca

spec = importlib.util.spec_from_file_location(
    "s1", "research/screens/2026-11-17_i103_step1_flow_audit.py"
)
s1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s1)

CACHE = Path("data/cache/alpaca_late2")
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
NY = ZoneInfo("America/New_York")
COST, RATIO = 2.5, 0.05


def events():
    a, _, _ = s1.flows()
    return a[a.ratio >= RATIO].reset_index(drop=True)


def fetch():
    ev = events()
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(sorted).to_dict()
    fetch_ = alpaca.http_fetch(*alpaca.keys())
    CACHE.mkdir(parents=True, exist_ok=True)
    for d in sorted(ev.day.unique()):
        d = pd.Timestamp(d)
        path = CACHE / f"{d:%Y-%m-%d}.csv"
        if path.exists():
            continue
        syms = sorted(set(members.get(f"{d:%Y-%m}", [])) | set(ev[ev.day == d].underlying))
        t0 = d.replace(hour=15, minute=27).tz_localize(NY).tz_convert("UTC")
        cut = t0 + pd.Timedelta(minutes=3)
        rows = []
        for k in range(0, len(syms), 500):
            params = {
                "symbols": ",".join(syms[k : k + 500]),
                "timeframe": "1Min",
                "limit": 10000,
                "adjustment": "split",
                "feed": "sip",
                "start": f"{t0:%Y-%m-%dT%H:%M:00Z}",
                "end": f"{cut + pd.Timedelta(minutes=2):%Y-%m-%dT%H:%M:00Z}",
            }
            while True:
                page = fetch_(params)
                for s, bars in (page.get("bars") or {}).items():
                    rows += [(s, b["t"], b["o"], b["c"]) for b in bars]
                if not page.get("next_page_token"):
                    break
                params = {**params, "page_token": page["next_page_token"]}
        b = pd.DataFrame(rows, columns=["symbol", "ts", "open", "close"])
        after = pd.to_datetime(b.ts, utc=True) >= cut
        out = pd.DataFrame(
            {
                "p1530": b[~after].groupby("symbol").close.last(),
                "o1530": b[after].groupby("symbol").open.first(),
            }
        ).rename_axis("symbol")
        out.to_csv(path)
    print(f"fetched {len(list(CACHE.glob('*.csv')))} event dates")


def frame():
    """Events with entry o1530, exit daily close, signed 15:30 -> close return (bp) and the control."""
    ev = events()
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(list).to_dict()
    unders = set(pd.read_csv(s1.NPORT / "funds.csv").underlying)
    rows, ctrl = [], []
    for d, g in ev.groupby("day"):
        late = pd.read_csv(CACHE / f"{pd.Timestamp(d):%Y-%m-%d}.csv", index_col="symbol")
        for _, e in g.iterrows():
            px = s1.daily(e.underlying)
            if (
                e.underlying in late.index
                and d in px.index
                and np.isfinite(late.loc[e.underlying, "o1530"])
            ):
                ret = (px.loc[d, "close"] / late.loc[e.underlying, "o1530"] - 1) * 1e4
                rows.append((d, e.underlying, e.ratio, np.sign(e.r), ret))
        # control: other universe names (no leveraged funds) whose 09:30 -> 15:30 move is within 0.8-1.25 x an event's
        moves = []
        for s in members.get(pd.Timestamp(d).strftime("%Y-%m"), []):
            if s in unders or s not in late.index:
                continue
            px = s1.daily(s)
            if px is None or d not in px.index or not np.isfinite(late.loc[s, "o1530"]):
                continue
            r = late.loc[s, "p1530"] / px.loc[d, "open"] - 1
            moves.append((s, r, (px.loc[d, "close"] / late.loc[s, "o1530"] - 1) * 1e4))
        for _, e in g.iterrows():
            m = (
                [np.sign(r) * x for s, r, x in moves if 0.8 <= abs(r) / abs(e.r) <= 1.25]
                if e.r
                else []
            )
            if m:
                ctrl.append((d, float(np.mean(m))))
    f = pd.DataFrame(rows, columns=["day", "underlying", "ratio", "sign", "ret"])
    f["signed"] = f.sign * f.ret
    return f, pd.DataFrame(ctrl, columns=["day", "signed"])


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power(f):
    by = f.groupby("day").ret.mean()  # unsigned direction: dispersion only
    sd = by.std(ddof=1)
    se = sd / np.sqrt(len(by))
    print(
        f"events {len(f)} on {len(by)} dates; per-date sd of the 15:30 -> close return {sd:.0f} bp, se {se:.1f}; "
        f"t 3 needs {3 * se:.1f} bp net ({3 * se + COST:.1f} gross)"
    )


def run(f, c):
    f["net"] = f.signed - COST
    by = f.groupby("day").net.mean()
    t = tstat(by)
    mid = by.index[len(by) // 2]
    h1, h2 = by[by.index < mid].mean(), by[by.index >= mid].mean()
    n2 = (f.groupby("day").signed.mean() - 2 * COST).mean()
    nb = by.drop(by.nlargest(2).index).mean()
    hi, lo = f[f.ratio >= 0.10].net.mean(), f[f.ratio < 0.10].net.mean()
    kills = {
        "net <= 0": by.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2 <= 0,
        "without 2 best <= 0": nb <= 0,
        "dose (>=10 % not above 5-10 %)": hi <= lo,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"events {len(f)} on {len(by)} dates: gross {f.signed.mean():+.1f} bp, net per date {by.mean():+.1f}, t {t:.2f}, "
        f"sd {by.std(ddof=1):.0f}; halves (median date {mid.date()}) {h1:+.1f} / {h2:+.1f}; doubled cost {n2:+.1f}; "
        f"without 2 best {nb:+.1f}; dose >= 10 % {hi:+.1f} vs 5-10 % {lo:+.1f}"
    )
    print("kills hit:", hit or "none", "->", "KILLED" if hit else "PASSED (development)")
    print(
        f"reported: control (same-size movers without leveraged funds) {c.signed.mean():+.1f} bp on {len(c)} events; "
        f"by underlying {f.groupby('underlying').signed.agg(['count', 'mean']).round(1).to_dict('index')}"
    )


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "fetch":
        fetch()
    else:
        f, c = frame()
        power(f) if step == "power" else run(f, c)
