"""I-100 wide funding-carry sort on unseen Binance perps (Fable card 1; rule fixed in knowledge/ideas.md, 502f6ee).

Development only (crypto split, no bar after 2023-12-31). Universe = data/cache/binance_wide minus the 37 symbols of
I-73 / I-73R, eligible by Strategy 20's rule (I-78 `week_rows`) and >= 7 days of funding history; weeks with < 40
eligible are skipped. Signal = funding settled in (Monday - 7 d, Monday]. Short the top quintile, long the bottom,
Monday open -> Sunday close; gross = bottom - top price + top funding - bottom funding; cost 20 bp a week.
`--power`: the signal-free line (random-quintile weekly sd), recorded before the run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i100_wide_carry_screen.py [--power]
"""

import importlib.util
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py"
)
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)

SEEN = [
    "BTC",
    "ETH",
    "BCH",
    "XRP",
    "EOS",
    "LTC",
    "TRX",
    "ETC",
    "LINK",
    "XLM",
    "ADA",
    "BNB",
    "XTZ",
    "XMR",
    "NEO",
    "DASH",
    "ATOM",
    "BAT",
    "IOST",
    "IOTA",
    "ONT",
    "QTUM",
    "VET",
    "ZEC",
    "THETA",
    "ALGO",
    "COMP",
    "KNC",
    "ZIL",
    "ZRX",
    "BAND",
    "DOGE",
    "KAVA",
    "OMG",
    "RLC",
    "SXP",
    "DOT",
]
EXCLUDED = {s + "USDT" for s in SEEN}
START = pd.Timestamp("2020-05-04")
MIN_ELIG, COST_BP, CAP_BP = 40, 20.0, 5000.0
assert len(EXCLUDED) == 37


def weeks_table(k, fund):
    """Monday -> (carry week rows with signal, all-universe rows for Strategy 20's flow spread)."""
    out = {}
    for m in i78.mondays(k):
        if m < START:
            continue
        w_all = i78.week_rows(k, fund, m)
        if w_all.empty:
            continue
        w = w_all[~w_all.sym.isin(EXCLUDED)].copy()
        sig, ok = [], []
        for s in w.sym:
            f = fund.get(s)
            ok.append(f is not None and len(f) > 0 and f.index[0] <= m - pd.Timedelta(days=7))
            sig.append(
                f[(f.index > m - pd.Timedelta(days=7)) & (f.index <= m)].sum() if ok[-1] else np.nan
            )
        w["sig"] = sig
        w = w[np.array(ok, bool)]
        if len(w) >= MIN_ELIG:
            out[m] = (w, w_all)
    return out


def carry(w, cap=None):
    w = w.sort_values(["sig", "sym"], kind="mergesort")
    n = len(w) // 5
    lo, hi = w.iloc[:n], w.iloc[-n:]
    r_lo, r_hi = lo.ret, hi.ret
    if cap is not None:
        r_lo, r_hi = r_lo.clip(-cap, cap), r_hi.clip(-cap, cap)
    price = r_lo.mean() - r_hi.mean()
    return price + hi.fund.mean() - lo.fund.mean(), price, n


def main(argv):
    k, fund = i78.load()
    weeks = weeks_table(k, fund)
    idx = sorted(weeks)
    elig = [len(weeks[m][0]) for m in idx]
    print(
        f"weeks {len(idx)} ({idx[0].date()} .. {idx[-1].date()}), eligible unseen per week min {min(elig)} "
        f"median {int(np.median(elig))} max {max(elig)}; distinct names {len(set().union(*(set(weeks[m][0].sym) for m in idx)))}"
    )
    if "--power" in argv:
        rng = np.random.default_rng(1)
        sds = []
        for _ in range(200):
            sp = []
            for m in idx:
                r = rng.permutation(weeks[m][0].ret.to_numpy())
                n = len(r) // 5
                sp.append(r[:n].mean() - r[-n:].mean())
            sds.append(np.std(sp, ddof=1))
        sd = float(np.mean(sds))
        se = sd / np.sqrt(len(idx))
        print(
            f"POWER: random-quintile weekly sd {sd:.0f} bp -> se {se:.1f}; t 3 needs {3 * se:.0f} bp a week net"
        )
        return 0

    g, p, legs = (
        pd.Series(x, index=idx) for x in zip(*(carry(weeks[m][0]) for m in idx), strict=True)
    )
    net = g - COST_BP
    t = i78.tstat(net)
    h = len(net) // 2
    halves = net.iloc[:h].mean(), net.iloc[h:].mean()
    nb = net.drop(net.nlargest(2).index).mean()
    net40 = (g - 2 * COST_BP).mean()
    kills = {
        "net <= 0": net.mean() <= 0,
        "t < 3.0": t < 3.0,
        "a half <= 0": min(halves) <= 0,
        "40 bp <= 0": net40 <= 0,
        "without 2 best <= 0": nb <= 0,
        "price part < -20": p.mean() < -20,
    }
    print(
        f"net {net.mean():+.1f} bp/week, t {t:.2f}, sd {net.std(ddof=1):.0f}; price {p.mean():+.1f}, "
        f"funding {(g - p).mean():+.1f}, cost {COST_BP:.0f}; legs {legs.min():.0f}-{legs.max():.0f}; "
        f"positive {100 * (net > 0).mean():.0f} %, worst {net.min():+.0f}"
    )
    print(
        f"halves {halves[0]:+.1f} / {halves[1]:+.1f}; at 40 bp {net40:+.1f}; without 2 best {nb:+.1f}"
    )
    hit = [a for a, b in kills.items() if b]
    verdict = "KILLED" if hit else "PASSED (development)"
    if hit == ["t < 3.0"] and 1.5 <= t < 3.0:
        verdict += " (UNPROVEN-POSITIVE under the proposed M1)"
    print("kills hit:", hit or "none", "->", verdict)

    print("\nreported, not gates:")
    gc = pd.Series([carry(weeks[m][0], CAP_BP)[0] for m in idx], index=idx) - COST_BP
    print(
        f"  capped +-50 %: net {gc.mean():+.1f} (share of mean {gc.mean() / net.mean():.2f}), t {i78.tstat(gc):.2f}; "
        f"median week {net.median():+.1f}; smallest half / mean {min(halves) / net.mean():.2f}"
    )
    by_year = net.groupby(net.index.year).agg(["count", "mean"]).round(1)
    print("  years:", by_year.to_dict("index"))
    s20 = pd.Series([i78.spread(weeks[m][1], "flow")[0] for m in idx], index=idx)
    print(
        f"  weekly correlation with Strategy 20's flow spread (long top, all names): {np.corrcoef(g, s20)[0, 1]:+.2f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
