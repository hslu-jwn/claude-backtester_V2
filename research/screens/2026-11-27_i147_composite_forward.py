"""I-147 frozen flow + carry composite on Binance USDT perps, top 100, forward only (knowledge/ideas.md > I-147).

The rule is the card's, verbatim; nothing here is tuned. Modes:
  canary   I-78's development run (f2 = f3 = c = 0, quintile bins, 20 bp): must print +145.0 bp a week, t 3.24.
  forward  every complete week from Monday 2026-11-30 -> research/forward/i147.csv (one row a week) and
           research/forward/i147_weights.csv (held weights), append-only (backtester.tools.forward_log).
No composite-sorted return is ever computed on a historical week (brief briefs/i147-composite-forward.md).
Run: .venv/Scripts/python.exe research/screens/2026-11-27_i147_composite_forward.py canary | forward
"""

import importlib.util
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.tools import forward_log

FORWARD = Path("research/forward")
SPOT_ROOTS = (Path("data/cache/binance_wide_spot"), Path("data/cache/binance_wide_spot_fwd"))
FORWARD_START = pd.Timestamp("2026-11-30")
TOP, MIN_NAMES, MIN_BARS, MIN_QVOL = 100, 40, 60, 5e6
CLIP, BUFFER = 2.0, 0.005
COSTS = {
    "cost10": 10.0,
    "net20": 20.0,
    "net5": 5.0,
}  # bp per unit of traded notional; 10 bp is the rule
COLS = (
    "period",
    "names",
    "skipped",
    "gross_bp",
    "funding_bp",
    "traded",
    "cost_bp",
    "net10_bp",
    "net20_bp",
    "net5_bp",
    "f3_coverage",
    "dispersion_bp",
    "dispersion_state",
)
WCOLS = ("period", "weights")


def _i78():
    spec = importlib.util.spec_from_file_location(
        "i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rank_normal(x: pd.Series) -> pd.Series:
    """Phi^-1((rank - 0.5) / N) over the non-missing values (average ranks for ties); missing values are dropped."""
    x = x.dropna()
    r = x.rank(method="average")
    inv = NormalDist().inv_cdf
    return pd.Series([inv((v - 0.5) / len(x)) for v in r], index=x.index)


def score(f: pd.DataFrame) -> pd.Series:
    """S = 0.5 F + 0.5 C. f has columns f1, f2, f3 (f3 may be NaN) and c, indexed by symbol."""
    z = pd.DataFrame({k: rank_normal(f[k]) for k in ("f1", "f2", "f3")}).reindex(f.index)
    F = z.mean(axis=1, skipna=True)
    sd = F.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        raise ValueError("flow score has no dispersion")
    C = rank_normal(f["c"]).reindex(f.index)
    return 0.5 * F / sd + 0.5 * C


def target_weights(s: pd.Series) -> pd.Series:
    """clip(S, -2, 2), mean removed, long sum 1 and short sum 1."""
    w = s.clip(-CLIP, CLIP)
    w = w - w.mean()
    pos, neg = w[w > 0].sum(), -w[w < 0].sum()
    if pos <= 0 or neg <= 0:
        raise ValueError("no long or no short side")
    return pd.Series(np.where(w > 0, w / pos, w / neg), index=w.index)


def apply_buffer(target: pd.Series, current: pd.Series) -> tuple[pd.Series, float]:
    """Keep the current weight if |target - current| < 0.005 (only for names still in the target).

    Returns (held weights, traded notional = sum |held - current|)."""
    idx = target.index.union(current.index)
    t, c = target.reindex(idx, fill_value=0.0), current.reindex(idx, fill_value=0.0)
    keep = (t - c).abs() < BUFFER
    keep &= idx.isin(target.index)  # a name that left the universe is closed
    held = c.where(keep, t)
    return held[held.abs() > 1e-15], float((held - c).abs().sum())


def spot_flows(spot_roots=SPOT_ROOTS) -> dict[str, pd.DataFrame]:
    out = {}
    for s in binance_wide.symbols(spot_roots):
        d = binance_wide.read_klines(s, spot_roots)
        d.index = d.index.tz_localize(None)
        out[s] = d
    return out


def week_features(k, fund, spot, monday):
    """Universe and signals for one Monday from bars strictly before it. Returns (frame, f3 coverage, dispersion)."""
    rows = []
    for s, d in k.items():
        fr = fund.get(s)
        if (
            monday not in d.index
            or fr is None
            or not len(fr)
            or fr.index[0] > monday - pd.Timedelta(days=7)
        ):
            continue  # >= 7 days of funding history
        past = d[d.index < monday]
        if len(past) < MIN_BARS or past.quote_volume.iloc[-30:].median() < MIN_QVOL:
            continue
        last7 = past[past.index >= monday - pd.Timedelta(days=7)]
        if len(last7) < 7:
            continue
        sp = spot.get(s)
        sl = (
            sp[(sp.index >= monday - pd.Timedelta(days=7)) & (sp.index < monday)]
            if sp is not None
            else None
        )
        spot_flow = (
            (2 * sl.taker_buy_volume - sl.volume).sum() / sl.volume.sum()
            if sl is not None and len(sl) == 7 and sl.volume.sum() > 0
            else np.nan
        )
        v = last7.volume.sum()
        f1 = (2 * last7.taker_buy_volume - last7.volume).sum() / v if v > 0 else np.nan
        window = fr[(fr.index > monday - pd.Timedelta(days=7)) & (fr.index <= monday)]
        rows.append(
            {
                "sym": s,
                "qv": past.quote_volume.iloc[-30:].median(),
                "f1": f1,
                "ret7": past.close.iloc[-1] / past.close.iloc[-8] - 1,
                "f3": f1 - spot_flow,
                "c": -window.sum(),
            }
        )
    f = pd.DataFrame(rows)
    if f.empty:
        return f, np.nan, np.nan
    f = f.sort_values(["qv", "sym"], ascending=[False, True], kind="mergesort").head(TOP)
    f = f.dropna(subset=["f1", "ret7"]).set_index("sym")
    ok = len(f) >= 3
    if ok:
        b = np.polyfit(f.ret7, f.f1, 1)
        f["f2"] = f.f1 - (b[0] * f.ret7 + b[1])
    else:
        f["f2"] = np.nan
    return (
        f,
        float(f.f3.notna().mean()) if len(f) else np.nan,
        float(f.ret7.std(ddof=0) * 1e4) if len(f) else np.nan,
    )


def hold_week(monday, held, k, fund):
    """(gross bp, funding bp) of the held weights, Monday open to next Monday open; funding (Mon, next Mon]."""
    nxt = monday + pd.Timedelta(days=7)
    gross = funding = 0.0
    for s, w in held.items():
        d = k[s]
        week = d[(d.index >= monday) & (d.index <= nxt)]
        exit_ = (
            week.open.iloc[-1] if week.index[-1] == nxt else week.close.iloc[-1]
        )  # delisted: last close
        gross += w * (exit_ / week.open.iloc[0] - 1) * 1e4
        fr = fund.get(s)
        paid = fr[(fr.index > monday) & (fr.index <= nxt)].sum() if fr is not None else 0.0
        funding -= w * paid * 1e4
    return gross, funding


def build_week(monday, k, fund, spot, previous, past_dispersion):
    """One log row and the held weights. A week with < 40 names is skipped (flat, the old book is closed)."""
    f, cover, disp = week_features(k, fund, spot, monday)
    names = len(f)
    base = {
        "period": f"{monday:%Y-%m-%d}",
        "names": names,
        "f3_coverage": cover,
        "dispersion_bp": disp,
    }
    state = (
        "na" if not past_dispersion else ("high" if disp > np.median(past_dispersion) else "low")
    )
    skipped = names < MIN_NAMES
    if not skipped:
        try:
            held, traded = apply_buffer(target_weights(score(f)), previous)
        except ValueError:
            skipped = True
    if skipped:
        held, traded = previous[:0], float(previous.abs().sum())
        gross = funding = 0.0
    else:
        gross, funding = hold_week(monday, held, k, fund)
    row = {
        **base,
        "skipped": int(skipped),
        "gross_bp": gross,
        "funding_bp": funding,
        "traded": traded,
        "cost_bp": traded * COSTS["cost10"],
        "dispersion_state": state,
    }
    for key, c in (("net10_bp", 10.0), ("net20_bp", 20.0), ("net5_bp", 5.0)):
        row[key] = gross + funding - traded * c
    return row, held


def complete_mondays(k, fund, start=FORWARD_START):
    """Mondays from `start` whose next Monday bar and settlement are already in the data."""
    last = min(
        max(d.index[-1] for d in k.values()), max(f.index.max() for f in fund.values() if len(f))
    )
    out, m = [], start
    while m + pd.Timedelta(days=7) <= last:
        out.append(m)
        m += pd.Timedelta(days=7)
    return out


def forward(k, fund, spot, out_dir=FORWARD, start=FORWARD_START):
    mondays = complete_mondays(k, fund, start)
    if not mondays:
        print("no complete forward week")
        return 0
    rows, wrows, held, disp = [], [], pd.Series(dtype=float), []
    for m in mondays:
        row, held = build_week(m, k, fund, spot, held, disp)
        if np.isfinite(row["dispersion_bp"]):
            disp.append(row["dispersion_bp"])
        rows.append(row)
        wrows.append(
            {"period": row["period"], "weights": ";".join(f"{s}:{w!r}" for s, w in held.items())}
        )
    n = forward_log.append(out_dir / "i147.csv", rows, COLS)
    forward_log.append(out_dir / "i147_weights.csv", wrows, WCOLS)
    print(f"{len(rows)} forward weeks computed, {n} appended")
    return 0


def canary():
    """I-78's development run (flow only, quintile bins, 20 bp) through this script's rank-normal score."""
    i78 = _i78()
    k, fund = i78.load()
    net = []
    for m in i78.mondays(k):
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        w["flow"] = (
            w.set_index("sym").flow.pipe(rank_normal).reindex(w.sym).to_numpy()
        )  # S = z(f1); f2 = f3 = c = 0
        net.append(i78.spread(w, "flow")[0] - i78.COST_BP)
    mean, t = np.mean(net), i78.tstat(net)
    print(
        f"CANARY I-78: {len(net)} weeks, net {mean:+.1f} bp a week, t {t:.2f} (must be 186, +145.0, 3.24)"
    )
    assert len(net) == 186 and abs(mean - 145.0) < 0.05 and abs(t - 3.24) < 0.005, "canary failed"
    print("CANARY OK")
    return 0


def main(argv):
    if argv == ["canary"]:
        return canary()
    if argv != ["forward"]:
        raise SystemExit("usage: i147_composite_forward.py canary | forward")
    i78 = _i78()
    i78.END = pd.Timestamp("2100-01-01")
    k, fund = i78.load(binance_wide.ROOTS)
    return forward(k, fund, spot_flows())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
