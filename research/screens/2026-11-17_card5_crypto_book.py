"""Card 5: one pre-registered crypto book, forward only (Fable sweep 2026-11-16; spec docs/strategy-crypto_flow.md ›
Crypto book). No data look: the book is defined on development quantities fixed earlier (each stream's R = its
development weekly sd, rounded) and judged only on the forward logs.

Book week = 0.5 x Strategy 20 top-100 r_net (net_bp / 600) + 0.5 x Strategy 19 r_net (net_bp / 1000), paired by the
Monday of entry; a week enters the book only when both logs have it. FB-254 boundary (8 looks every 13 weeks, OBF c,
early kill z <= -2) on the book's weekly R.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_card5_crypto_book.py [--check]
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "fb254", "research/screens/2026-11-15_fb254_forward_boundaries.py"
)
fb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fb)

FORWARD = Path("research/forward")
STREAMS = {"crypto_flow_top100.csv": 600.0, "crypto_carry.csv": 1000.0}  # R per stream (its spec)
PLAN = {  # fair bp a week, sd bp a week (FB-254 table), weekly correlation (card 0 / spec, test weeks)
    "crypto_flow_top100.csv": (74.0, 658.0),
    "crypto_carry.csv": (63.0, 624.0),
}
CORR = 0.09


def book(frames):
    """Paired book weeks: frames = {file: DataFrame with entry_time, net_bp}."""
    parts = []
    for name, d in frames.items():
        monday = pd.to_datetime(d.entry_time, utc=True).dt.normalize()
        parts.append(pd.Series(d.net_bp.to_numpy(float) / STREAMS[name], index=monday, name=name))
    both = pd.concat(parts, axis=1, join="inner").sort_index()
    return both.mean(axis=1)


def plan():
    (m1, s1), (m2, s2) = (PLAN[f] for f in STREAMS)
    r1, r2 = STREAMS.values()
    mu = 0.5 * (m1 / r1 + m2 / r2)
    sd = 0.5 * np.sqrt((s1 / r1) ** 2 + (s2 / r2) ** 2 + 2 * CORR * (s1 / r1) * (s2 / r2))
    return mu, sd


def self_check():
    a = pd.DataFrame(
        {"entry_time": ["2026-11-16T00:00:00Z", "2026-11-23T00:00:00Z"], "net_bp": [600.0, -300.0]}
    )
    b = pd.DataFrame({"entry_time": ["2026-11-16T00:01:00Z"], "net_bp": [1000.0]})
    x = book({"crypto_flow_top100.csv": a, "crypto_carry.csv": b})
    assert len(x) == 1 and abs(x.iloc[0] - 1.0) < 1e-12, (
        x
    )  # only the paired week, 0.5 x 1 R + 0.5 x 1 R


def main(argv):
    self_check()
    c = fb.calibrate()
    mu, sd = plan()
    win, lose = fb.power(mu, sd, c)
    need = [c / np.sqrt((k + 1) / fb.K) * sd / np.sqrt((k + 1) * fb.LOOK) for k in range(fb.K)]
    print(
        f"book plan: mean {mu:+.3f} R a week, sd {sd:.3f} R (corr {CORR}); confirm needs mean >= "
        + ", ".join(f"{(k + 1) * fb.LOOK}w {n:.3f}" for k, n in enumerate(need))
        + f" R; P(confirm by 104 w) {100 * win:.0f} %, P(early kill) {100 * lose:.0f} %; "
        f"at mean 0 P(kill) {100 * fb.power(0.0, sd, c)[1]:.0f} %"
    )
    if "--check" in argv:
        missing = [f for f in STREAMS if not (FORWARD / f).exists()]
        if missing:
            print(f"check: no forward log yet ({', '.join(missing)})")
            return 0
        x = book({f: pd.read_csv(FORWARD / f) for f in STREAMS}).to_numpy()
        k = min(len(x) // fb.LOOK, fb.K)
        if k == 0:
            print(f"check: {len(x)} paired weeks, first look at {fb.LOOK}")
            return 0
        y = x[: k * fb.LOOK]
        z = y.mean() / (y.std(ddof=1) / np.sqrt(len(y)))
        state = (
            "CONFIRMED"
            if z >= c / np.sqrt(k / fb.K)
            else "KILL (z <= -2)"
            if z <= fb.KILL_Z
            else "continue"
        )
        print(f"check: look {k} ({len(y)} weeks): mean {y.mean():+.3f} R, z {z:.2f} -> {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
