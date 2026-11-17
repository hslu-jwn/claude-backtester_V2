"""Card 0 (Fable 2026-11-16): Strategy 20 regime and tail audit. Descriptive only: no new signal, no variant, no gate.

Inputs: the frozen weekly books of Strategy 20 (full universe and top-100, rebuilt here with the tool's own
compute_weeks) and Strategy 19's frozen weekly list (results/crypto_carry/test_2021_2026/trades.csv, 2021-09..2026-10).
Outputs: (a) net and t per calendar year, (b) correlation of non-overlapping block sums, (c) joint worst 10 % of weeks,
(d) median week and t with member returns capped at +-50 %, (e) deflated Sharpe with the ledger's trial counts,
(f) the closed form "volatility ~9.1 % x Sharpe passes ~83 % in ~1.65 / Sharpe^2 years" against risk.monte_carlo.
Run: .venv/Scripts/python.exe research/screens/2026-11-16_card0_s20_audit.py [--skip-f]
"""
import csv
import importlib.util
import sys
from datetime import date
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from backtester.risk.monte_carlo import Day, MonteCarloConfig, ftmo_by_risk
from backtester.tools import crypto_flow as cf

N = NormalDist()
PERIODS = (("dev", date(2020, 1, 1), date(2023, 12, 31)), ("test", date(2024, 1, 1), date(2026, 10, 31)))
CARRY = Path("results/crypto_carry/test_2021_2026/trades.csv")
CAP_BP = 5000.0
WEEKS = 52


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def book(klines, funding, config):
    """Weekly frame (index = Monday date) with net and the +-50 % capped net, per period."""
    rows = []
    for label, a, b in PERIODS:
        trades, legs = cf.compute_weeks(klines, funding, a, b, config)
        legs = pd.DataFrame(legs)
        legs["cap"] = legs.price_bp.clip(-CAP_BP, CAP_BP)
        side = legs.groupby(["week", "side"])[["price_bp", "cap"]].mean().unstack("side")
        for t in trades:
            wk = pd.Timestamp(t["entry_time"]).normalize()
            raw = side.loc[wk, ("price_bp", "long")] - side.loc[wk, ("price_bp", "short")]
            assert abs(raw - t["price_bp"]) < 1e-6, "leg means do not reproduce the trade"
            capped = side.loc[wk, ("cap", "long")] - side.loc[wk, ("cap", "short")]
            rows.append({"week": wk.tz_localize(None), "period": label, "net": t["net_bp"],
                         "net_cap": t["net_bp"] - raw + capped})
    return pd.DataFrame(rows).set_index("week")


def carry():
    d = pd.read_csv(CARRY)
    wk = pd.to_datetime(d.entry_time, utc=True).dt.normalize().dt.tz_localize(None)
    return pd.Series(d.net_bp.to_numpy(), index=wk, name="s19")


def by_year(streams):
    print("\n(a) net bp a week and t per calendar year")
    print("| year | " + " | ".join(f"{n} weeks / net / t" for n in streams) + " |")
    print("|---|" + "---|" * len(streams))
    years = sorted({y for s in streams.values() for y in s.index.year})
    for y in years:
        cells = []
        for s in streams.values():
            x = s[s.index.year == y]
            cells.append(f"{len(x)} / {x.mean():+.0f} / {tstat(x):.2f}" if len(x) > 3 else "-")
        print(f"| {y} | " + " | ".join(cells) + " |")
    cells = [f"{len(s)} / {s.mean():+.0f} / {tstat(s):.2f}" for s in streams.values()]
    print("| all | " + " | ".join(cells) + " |")
    late = [s[s.index.year > 2020] for s in streams.values()]
    print("| all without 2020 | " + " | ".join(f"{len(s)} / {s.mean():+.0f} / {tstat(s):.2f}" for s in late) + " |")


def blocks(a, b):
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    print(f"\n(b) Strategy 20 vs Strategy 19 on {len(j)} shared weeks ({j.index[0].date()} .. {j.index[-1].date()})")
    print("| block length (weeks) | blocks | correlation of block sums |")
    print("|---|---|---|")
    for k in (1, 4, 13, 26):
        n = len(j) // k
        s = j.iloc[: n * k].to_numpy().reshape(n, k, 2).sum(axis=1)
        print(f"| {k} | {n} | {np.corrcoef(s[:, 0], s[:, 1])[0, 1]:+.2f} |")
    half = j.rolling(26).sum().dropna()
    print(f"rolling 26-week sums (overlapping, {len(half)} points): correlation {half.corr().iloc[0, 1]:+.2f}")
    return j


def joint_tail(j):
    n = len(j)
    k = max(1, round(0.1 * n))
    print(f"\n(c) joint worst 10 % of weeks ({k} of {n})")
    print("| conditioning stream | its mean in its worst weeks | other stream's mean there | other negative % | "
          "other's mean in all weeks |")
    print("|---|---|---|---|---|")
    worst = {}
    for me, other in ((j.columns[0], j.columns[1]), (j.columns[1], j.columns[0])):
        w = j.nsmallest(k, me)
        worst[me] = set(w.index)
        print(f"| {me} | {w[me].mean():+.0f} | {w[other].mean():+.0f} | {100 * (w[other] < 0).mean():.0f} | "
              f"{j[other].mean():+.0f} |")
    both = len(worst[j.columns[0]] & worst[j.columns[1]])
    print(f"weeks in both worst deciles: {both} (expected if independent: {k * k / n:.1f})")
    eq = j / j.std(ddof=1)
    mix = eq.mean(axis=1)
    print(f"equal-risk mix: worst week {mix.min():+.2f} own-sd units vs {eq.min().min():+.2f} for the worse single "
          f"stream; mix t {tstat(mix):.2f}")


def tails(books):
    print(f"\n(d) plain vs member returns capped at +-{CAP_BP / 100:.0f} % (bp a week)")
    print("| book | period | weeks | mean | median | t | capped mean | capped median | capped t | capped / plain |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for name, b in books.items():
        for label in ("dev", "test", "all"):
            x = b if label == "all" else b[b.period == label]
            print(f"| {name} | {label} | {len(x)} | {x.net.mean():+.1f} | {x.net.median():+.1f} | {tstat(x.net):.2f} | "
                  f"{x.net_cap.mean():+.1f} | {x.net_cap.median():+.1f} | {tstat(x.net_cap):.2f} | "
                  f"{x.net_cap.mean() / x.net.mean():.2f} |")


def trial_counts():
    spec = importlib.util.spec_from_file_location("family_budget", Path(__file__).with_name("family_budget.py"))
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    with open("research/ledger.csv", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if not r["id"].startswith("HV-") and r["stage"] in fb.LOOK_STAGES]
    count = lambda keep: sum(fb.cells(r["cells"]) for r in rows if keep(r))  # noqa: E731
    return {"family crypto_xs_factors": count(lambda r: r["family"] == "crypto_xs_factors"),
            "all crypto families": count(lambda r: r["family"].startswith("crypto")),
            "whole ledger": count(lambda r: True)}


def deflated(x, trials):
    """Bailey & Lopez de Prado deflated Sharpe; trial-Sharpe sd taken as 1 / sqrt(T) (no skill, per period)."""
    x = np.asarray(x, float)
    t = len(x)
    sr = x.mean() / x.std(ddof=1)
    z = (x - x.mean()) / x.std(ddof=0)
    skew, kurt = (z**3).mean(), (z**4).mean()
    g = 0.5772156649
    sr0 = (1 / np.sqrt(t)) * ((1 - g) * N.inv_cdf(1 - 1 / trials) + g * N.inv_cdf(1 - 1 / (trials * np.e)))
    dsr = N.cdf((sr - sr0) * np.sqrt(t - 1) / np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr**2))
    return sr * np.sqrt(WEEKS), sr0 * np.sqrt(WEEKS), skew, kurt, dsr


def deflated_table(series):
    counts = trial_counts()
    print("\n(e) deflated Sharpe (probability the true Sharpe is > 0 after the best-of-N selection)")
    print(f"trial counts from the ledger (family_budget look stages, cells summed): {counts}")
    print("| series | weeks | yearly Sharpe | skew | kurtosis | " +
          " | ".join(f"N = {n} ({k}): hurdle / DSR" for k, n in counts.items()) + " |")
    print("|---|---|---|---|---|" + "---|" * len(counts))
    for name, x in series.items():
        cells, head = [], None
        for n in counts.values():
            sr, sr0, skew, kurt, dsr = deflated(x, max(n, 2))
            head = f"{sr:.2f} | {skew:+.2f} | {kurt:.1f}"
            cells.append(f"{sr0:.2f} / {dsr:.3f}")
        print(f"| {name} | {len(x)} | {head} | " + " | ".join(cells) + " |")


def closed_form(sharpes=(0.7, 1.0, 1.3, 2.0), runs=40, n_days=10000, seed=11):
    """One Gaussian trade a day: mean S / sqrt(252) R, sd 1 R; risk per R = 9.1 % x S / sqrt(252)."""
    print("\n(f) closed form vs risk.monte_carlo.ftmo_by_risk (2-Step, 5 % daily, 10 % static, 4 days, no time limit)")
    print("| yearly Sharpe | yearly volatility | closed form pass / years | simulator pass % (finished attempts) | "
          "simulator years to pass | daily-loss fails % | attempts |")
    print("|---|---|---|---|---|---|---|")
    rng = np.random.default_rng(seed)
    for s in sharpes:
        for mult, label in ((1.0, ""), (0.5, " (half size)")):
            vol = 0.091 * s * mult
            risk = vol / np.sqrt(252)
            k1 = 2 * s * 0.10 / vol
            cf_pass = (1 / (1 + np.exp(-k1))) * (1 - np.exp(-k1)) / (1 - np.exp(-1.5 * k1))
            cf_years = 0.15 / (s * vol)
            config = MonteCarloConfig(runs=1, risk_levels=(risk,), seed=seed)
            tot = {"attempts": 0, "passes": 0, "daily": 0, "days": []}
            for _ in range(runs):
                r = rng.normal(s / np.sqrt(252), 1.0, n_days)
                days = [Day(r=np.array([x]), events=((True, float(x)), (False, float(x)))) for x in r]
                res = ftmo_by_risk(days, [np.arange(n_days)], config)[risk]
                done = res["attempts"] - res["unfinished_attempts"]
                tot["attempts"] += done
                tot["passes"] += res["passes"]
                tot["daily"] += res["fail_daily"]
                if res["average_days_to_pass"] is not None:
                    tot["days"] += [res["average_days_to_pass"]] * res["passes"]
            n = max(tot["attempts"], 1)
            years = np.mean(tot["days"]) / 252 if tot["days"] else float("nan")
            print(f"| {s}{label} | {100 * vol:.1f} % | {100 * cf_pass:.0f} % / {cf_years:.2f} | "
                  f"{100 * tot['passes'] / n:.0f} | {years:.2f} | {100 * tot['daily'] / n:.1f} | {n} |", flush=True)


if __name__ == "__main__":
    k, f = cf.load()
    books = {"S20 full": book(k, f, cf.DEFAULT), "S20 top-100": book(k, f, cf.LIQUID)}
    for name, b in books.items():
        for label in ("dev", "test"):
            x = b[b.period == label].net
            print(f"check {name} {label}: {len(x)} weeks, net {x.mean():+.1f}, t {tstat(x):.2f}")
    s19 = carry()
    by_year({"S20 full": books["S20 full"].net, "S20 top-100": books["S20 top-100"].net, "S19 carry": s19})
    j = blocks(books["S20 full"].net.rename("s20"), s19)
    joint_tail(j)
    print("\nsame with the top-100 book:")
    joint_tail(blocks(books["S20 top-100"].net.rename("s20_top100"), s19))
    tails(books)
    full, top = books["S20 full"], books["S20 top-100"]
    deflated_table({"S20 full dev": full[full.period == "dev"].net, "S20 full test": full[full.period == "test"].net,
                    "S20 full all": full.net, "S20 full all, capped": full.net_cap,
                    "S20 top-100 all": top.net, "S19 carry 2021-09..": s19})
    if "--skip-f" not in sys.argv:
        closed_form()
