"""Shelf forward logs (M3; docs/research-runner.md › Verdicts and shelf; rules set by the user 2026-11-17).

Every row runs its frozen screen rule unchanged on periods from its forward start and appends them to
research/forward/shelf_<row>.csv (append-only, `backtester.tools.forward_log`). Before any forward period counts, a
canary reruns the same function on the development period and must reproduce the row's registered headline.
Crypto rows (weekly, Monday entry): I-100 wide funding carry, I-84 spot-minus-perp flow, I-98 spot-hedged carry.
Data: perps from `binance_wide.ROOTS` (update: `binance_wide.update`), spot from data/cache/binance_wide_spot (dev)
and data/cache/binance_wide_spot_fwd (`binance_wide.update_spot`, months after 2026-09).
Run: .venv/Scripts/python.exe research/screens/2026-11-17_shelf_forward.py canary | update | log | status
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.tools import forward_log


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


i78 = _load("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
i100 = _load("i100", "research/screens/2026-11-17_i100_wide_carry_screen.py")
wave1 = _load("wave1", "research/screens/2026-11-15_wave1_xs_crypto_screen.py")
i98 = _load("i98", "research/screens/2026-11-15_i98_basis_carry_screen.py")

FORWARD = Path("research/forward")
SPOT_DEV = Path("data/cache/binance_wide_spot/klines_1d")
SPOT_FWD = Path("data/cache/binance_wide_spot_fwd")
CRYPTO_START = pd.Timestamp("2026-11-23")  # first Monday after the shelf was set up (2026-11-17)
DEV = (pd.Timestamp("2020-01-01"), pd.Timestamp("2023-12-31"))
COLS = ("period", "n", "gross_bp", "net_bp")
D84 = None  # development direction of I-84, set by the canary from the registered result


def spot_frames(roots):
    out = {}
    for root in roots:
        for p in Path(root).glob("*.csv"):
            d = pd.read_csv(p, usecols=["open_time", "open", "close", "volume", "taker_buy_volume"])
            d.index = pd.to_datetime(d.open_time, unit="ms").dt.normalize()
            out[p.stem] = pd.concat([out.get(p.stem), d]) if p.stem in out else d
    return {s: d[~d.index.duplicated()].sort_index() for s, d in out.items()}


def crypto_data(end, roots):
    i78.END = end
    k, fund = i78.load(roots)
    return k, fund


def rows_i100(k, fund, start):
    i100.START = start
    out = []
    for m, (w, _) in sorted(i100.weeks_table(k, fund).items()):
        g, _, n = i100.carry(w)
        out.append({"period": f"{m:%Y-%m-%d}", "n": n, "gross_bp": g, "net_bp": g - i100.COST_BP})
    return out


def rows_i84(k, fund, spot, start, d):
    out = []
    for m, w in sorted(wave1.weekly(k, fund, spot).items()):
        if m < start or w.spot_flow.notna().sum() < i78.MIN_ELIG:
            continue
        g = wave1.legs_gross(w, "spot_minus_perp")
        if np.isfinite(g):
            out.append(
                {
                    "period": f"{m:%Y-%m-%d}",
                    "n": int(w.spot_minus_perp.notna().sum() // 5),
                    "gross_bp": d * g,
                    "net_bp": d * g - wave1.COST,
                }
            )
    return out


def rows_i98(k, fund, spot, start):
    """I-98's frozen loop (screen 2026-11-15, commit 2ec4526); the held set starts empty at `start`."""
    out, held = [], set()
    for m in i78.mondays(k):
        if m < start:
            continue
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        cand = []
        for s in w.sym:
            d = spot.get(s)
            if (
                d is None
                or m not in d.index
                or len(d[(d.index < m) & (d.index >= m - pd.Timedelta(days=7))]) < 7
            ):
                continue
            f = fund.get(s)
            if f is None:
                continue
            past = f[(f.index > m - pd.Timedelta(days=7)) & (f.index <= m)].sum()
            if past > 0:
                cand.append((past, s))
        pick = [s for _, s in sorted(cand, key=lambda x: (-x[0], x[1]))[: i98.N]]
        new = set(pick)
        turnover = len(new - held) + len(held - new)
        if not pick:
            out.append(
                {
                    "period": f"{m:%Y-%m-%d}",
                    "n": 0,
                    "gross_bp": 0.0,
                    "net_bp": -turnover * i98.COST / max(len(held), 1),
                }
            )
            held = new
            continue
        wi = w.set_index("sym")
        basis, carry = [], []
        for s in pick:
            hs = spot[s][(spot[s].index >= m) & (spot[s].index <= m + pd.Timedelta(days=6))]
            basis.append((hs.close.iloc[-1] / hs.open.iloc[0] - 1) * 1e4 - wi.loc[s, "ret"])
            carry.append(wi.loc[s, "fund"])
        gross = np.mean(basis) + np.mean(carry)
        out.append(
            {
                "period": f"{m:%Y-%m-%d}",
                "n": len(pick),
                "gross_bp": gross,
                "net_bp": gross - turnover * i98.COST / len(new),
            }
        )
        held = new
    return out


def summary(rows):
    x = np.array([r["net_bp"] for r in rows])
    return len(x), x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def canary():
    """The forward functions on development data must reproduce each row's registered headline."""
    k, fund = crypto_data(DEV[1], (i78.ROOT,))
    spot = spot_frames([SPOT_DEV])
    n, mu, t = summary(rows_i100(k, fund, pd.Timestamp("2020-05-04")))
    print(f"I-100 dev: {n} weeks, net {mu:+.1f}, t {t:.2f} (registered 153, +107.1, 2.45)")
    assert n == 153 and abs(mu - 107.1) < 0.05 and abs(t - 2.45) < 0.005
    g = summary(rows_i84(k, fund, spot, DEV[0], 1.0))
    d = 1.0 if g[1] + wave1.COST > 0 else -1.0
    n, mu, t = summary(rows_i84(k, fund, spot, DEV[0], d))
    print(
        f"I-84 dev: {n} weeks, direction {d:+.0f}, net {mu:+.1f}, t {t:.2f} (registered +70.5, 1.76)"
    )
    assert abs(mu - 70.5) < 0.05 and abs(t - 1.76) < 0.005
    n, mu, t = summary(rows_i98(k, fund, spot, DEV[0]))
    print(f"I-98 dev: {n} weeks, net {mu:+.1f}, t {t:.2f} (registered +12.0, 1.84)")
    assert abs(mu - 12.0) < 0.05 and abs(t - 1.84) < 0.005
    print("CANARY OK")
    return d


def update():
    """Monthly: complete months of perps (all symbols) and spot (forward root) from Binance's archives."""
    month = (pd.Timestamp.now(tz="UTC").normalize().replace(day=1) - pd.Timedelta(days=1)).strftime(
        "%Y-%m"
    )
    binance_wide.update(binance_wide.ROOTS[-1], month)
    binance_wide.update_spot(SPOT_FWD, binance_wide.symbols(), month, start_after="2026-09")


def log():
    d84 = canary()
    end = max(binance_wide.read_klines("BTCUSDT").index).tz_localize(None).normalize()
    k, fund = crypto_data(end, binance_wide.ROOTS)
    spot = spot_frames([SPOT_DEV, SPOT_FWD / "klines_1d"])
    for name, rows in (
        ("i100", rows_i100(k, fund, CRYPTO_START)),
        ("i84", rows_i84(k, fund, spot, CRYPTO_START, d84)),
        ("i98", rows_i98(k, fund, spot, CRYPTO_START)),
    ):
        n = forward_log.append(FORWARD / f"shelf_{name}.csv", rows, COLS)
        print(f"{name}: {len(rows)} forward weeks computed, {n} appended")


def status():
    fb = _load("fb", "research/screens/2026-11-15_fb254_forward_boundaries.py")
    c = 2.071
    for p in sorted(FORWARD.glob("shelf_*.csv")):
        x = pd.read_csv(p).net_bp.to_numpy(float)
        k = min(len(x) // fb.LOOK, fb.K)
        if k == 0:
            print(f"{p.stem}: {len(x)} periods, first look at {fb.LOOK}")
            continue
        y = x[: k * fb.LOOK]
        z = y.mean() / (y.std(ddof=1) / np.sqrt(len(y)))
        state = (
            "CONFIRMED"
            if z >= c / np.sqrt(k / fb.K)
            else "KILL (z <= -2)"
            if z <= fb.KILL_Z
            else "continue"
        )
        print(f"{p.stem}: look {k} ({len(y)} periods) mean {y.mean():+.1f}, z {z:.2f} -> {state}")


if __name__ == "__main__":
    {"canary": canary, "update": update, "log": log, "status": status}[sys.argv[1]]()
