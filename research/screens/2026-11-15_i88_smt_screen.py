"""I-88 screen: SMT divergence at the session extreme, NAS100 vs US500 (knowledge/ideas.md › I-88; rules fixed in
commit d94946c before any data).

New York time, development only (before 2021-09-14). Per symbol and day: minute matrix from 09:30 (offset 0) to
15:55. Checkpoints at bar closes 10:00, 10:15, ..., 15:00 (bar opening one minute earlier). Session high so far =
max M1 high in [09:30, t - 15 min). Bearish event: A's close at t > A's high so far, while B's highs in [t - 15, t)
stay below B's high so far; bullish mirrored. Trade A against the new extreme (ICT direction) from its close at t to
its 15:55 close; first event per day per direction. Cost = engine spread at entry + 2 x slippage, bp.
Kills: |t| < 3.0 in own direction; net <= 0; halves not both > 0; doubled costs <= 0; without the 2 best days <= 0.
`--power`: signal-free line (event count, sd of A's checkpoint -> 15:55 return).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i88_smt_screen.py [--power]
"""
import sys
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
START, END = date(2015, 1, 1), date(2021, 9, 13)
OPEN_MIN, EXIT_OFF = 9 * 60 + 30, (15 * 60 + 54) - (9 * 60 + 30)  # offset of the bar closing 15:55
CHECKS = [(h * 60 + m) - OPEN_MIN - 1 for h in range(10, 16) for m in (0, 15, 30, 45) if h * 60 + m <= 15 * 60]
cfg = CostConfig()


def matrices(sym):
    d = load_m1(sym, DEFAULT_SOURCES, START, END)
    t = pd.to_datetime(d.open_s, unit="s", utc=True).tz_convert(NY)
    off = t.hour * 60 + t.minute - OPEN_MIN
    keep = (off >= 0) & (off <= EXIT_OFF)
    df = pd.DataFrame({"day": t.date[keep], "off": off[keep], "high": d.high[keep], "low": d.low[keep],
                       "close": d.close[keep]})
    return {c: df.pivot_table(index="day", columns="off", values=c, aggfunc="first").reindex(columns=range(EXIT_OFF + 1))
            for c in ("high", "low", "close")}


def events(mats, a, others, confirm=False):
    """Rows (day, checkpoint offset, leg, side): A breaks its session extreme; every other leg fails (or, for the
    control, confirms)."""
    days = sorted(set(mats[a]["close"].index).intersection(*[set(mats[o]["close"].index) for o in others]))
    out = []
    for side in ("bear", "bull"):
        ext, cmp = ("high", np.greater) if side == "bear" else ("low", np.less)
        agg = np.nanmax if side == "bear" else np.nanmin
        for day in days:
            for c in CHECKS:
                start = c + 1 - 15  # first bar of the last 15 minutes
                so_far_a = agg(mats[a][ext].loc[day].to_numpy()[:start])
                ca = mats[a]["close"].loc[day, c]
                if np.isnan(ca) or np.isnan(so_far_a) or not cmp(ca, so_far_a):
                    continue
                fails = []
                for o in others:
                    so_far_o = agg(mats[o][ext].loc[day].to_numpy()[:start])
                    recent = agg(mats[o][ext].loc[day].to_numpy()[start:c + 1])
                    fails.append(not cmp(recent, so_far_o) if not (np.isnan(so_far_o) or np.isnan(recent)) else None)
                if None in fails:
                    continue
                if (not confirm and all(fails)) or (confirm and not any(fails)):
                    out.append((day, c, a, side))
                    break  # first event per day per direction
    return out


def first_per_day(evs):
    """At most one event per day and direction across legs: the earliest checkpoint (ties: leg name)."""
    best = {}
    for e in sorted(evs, key=lambda e: (e[0], e[3], e[1], e[2])):
        best.setdefault((e[0], e[3]), e)
    return list(best.values())


def trades(mats, evs, leg_override=None):
    rows = []
    for day, c, a, side in evs:
        leg = leg_override(a) if leg_override else a
        e, x = mats[leg]["close"].loc[day, c], mats[leg]["close"].loc[day, EXIT_OFF]
        if np.isnan(e) or np.isnan(x):
            continue
        direction = -1 if side == "bear" else 1  # ICT: against the new extreme
        et = datetime.combine(day, time(9, 30), NY) + timedelta(minutes=c + 1)
        cost = (cfg.spread(leg, fill_spread_time(et.astimezone(UTC)), e) + 2 * cfg.slippage(leg, e)) / e * 1e4
        rows.append({"day": day, "leg": leg, "side": side, "c": c, "gross": direction * (x / e - 1) * 1e4, "cost": cost})
    return pd.DataFrame(rows)


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def summary(name, t, gate=True):
    if t.empty:
        print(f"{name}: no trades")
        return
    g = t.groupby("day").gross.mean()
    c = t.groupby("day").cost.mean()
    d = 1.0 if g.mean() > 0 else -1.0
    net, net2 = d * g - c, d * g - 2 * c
    half = net.index < date(2018, 5, 1)
    tt = tstat(net)
    msg = (f"{name}: {len(t)} trades / {len(net)} days, direction {'ICT (fade)' if d > 0 else 'continuation'}; net "
           f"{net.mean():+.2f} bp, t {tt:.2f}; gross {d * g.mean():+.2f}, cost {c.mean():.2f}; halves {net[half].mean():+.2f} / "
           f"{net[~half].mean():+.2f}; 2x cost {net2.mean():+.2f}; without 2 best {net.drop(net.nlargest(2).index).mean():+.2f}")
    print(msg)
    if gate:
        kills = {"|t| < 3": not abs(tt) >= 3.0, "net <= 0": net.mean() <= 0,
                 "halves": not (net[half].mean() > 0 and net[~half].mean() > 0), "2x cost <= 0": net2.mean() <= 0,
                 "without 2 best <= 0": net.drop(net.nlargest(2).index).mean() <= 0}
        print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")


def main(argv):
    pair = ("NAS100", "US500")
    mats = {s: matrices(s) for s in pair}
    evs = first_per_day(events(mats, "NAS100", ["US500"]) + events(mats, "US500", ["NAS100"]))
    if "--power" in argv:
        r = []
        for day, c, a, _ in evs:
            e, x = mats[a]["close"].loc[day, c], mats[a]["close"].loc[day, EXIT_OFF]
            r.append((x / e - 1) * 1e4)
        r = pd.Series(r).dropna()
        n_days = len({e[0] for e in evs})
        print(f"POWER: {len(evs)} events on {n_days} days; sd of A's checkpoint -> 15:55 return {r.std():.0f} bp -> "
              f"se ~{r.std() / np.sqrt(n_days):.1f} bp, t 3 needs ~{3 * r.std() / np.sqrt(n_days):.1f} bp net")
        return 0
    t = trades(mats, evs)
    summary("I-88 SMT NAS100 / US500 (primary)", t)
    print("\nDiagnostics (no gate):")
    ctrl = first_per_day(events(mats, "NAS100", ["US500"], confirm=True) + events(mats, "US500", ["NAS100"], confirm=True))
    summary("  control: both legs make the new extreme (trade A)", trades(mats, ctrl), gate=False)
    other = {"NAS100": "US500", "US500": "NAS100"}
    summary("  trade the non-confirming leg B instead", trades(mats, evs, lambda a: other[a]), gate=False)
    for side in ("bear", "bull"):
        summary(f"  {side}ish events only", t[t.side == side], gate=False)
    for lo, hi, name in ((0, 120, "10:00-11:59"), (120, 240, "12:00-13:59"), (240, 400, "14:00-15:00")):
        summary(f"  events {name}", t[(t.c >= lo) & (t.c < hi)], gate=False)
    tri = ("NAS100", "US500", "US30")
    mats["US30"] = matrices("US30")
    tev = []
    for a in tri:
        tev += events(mats, a, [o for o in tri if o != a])
    summary("  US triad (US30 from 2019-02): A breaks, both others fail", trades(mats, first_per_day(tev)), gate=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
