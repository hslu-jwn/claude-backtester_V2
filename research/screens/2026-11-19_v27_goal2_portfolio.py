"""Read-only goal-2 portfolio screen; returns are assigned to their UTC exit month."""

import importlib.util
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.data.sources import BINANCE_CACHE_DIR, SymbolSources
from backtester.engine.costs import FUNDING_DIR
from backtester.tools import crypto_carry, crypto_flow


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


i109 = _load("i109", "research/screens/2026-11-17_i109_treasury_month_end_screen.py")


def weekly(rows):
    if not rows:
        return pd.Series(dtype=float)
    dates = pd.to_datetime([r["exit_time"] for r in rows], utc=True).tz_localize(None)
    return pd.Series([r["net_bp"] for r in rows], index=dates).sort_index()


def describe(name, period, x, frequency):
    x = x.dropna()
    if x.empty:
        print(f"{name} [{period}]: n=0")
        return
    sd = x.std(ddof=1)
    t = x.mean() / sd * np.sqrt(len(x)) if sd > 0 else np.nan
    sharpe = x.mean() / sd * np.sqrt(frequency) if sd > 0 else np.nan
    print(f"{name} [{period}; {x.index.min()} to {x.index.max()}]: n={len(x)}, "
          f"mean={x.mean():+.2f} bp, sd={sd:.2f} bp, t={t:.2f}, Sharpe={sharpe:.2f}")


def monthly(x):
    return x.groupby(x.index.to_period("M")).sum()


def portfolio(frame):
    sd = frame.std(ddof=1)
    if len(frame) < 2 or (sd <= 0).any() or sd.isna().any():
        return None
    weights = (1 / sd) / (1 / sd).sum() * len(sd)
    assert np.isclose(weights.sum(), len(sd))
    # Average standardized streams; one unit is one stream's monthly overlap SD.
    returns = (frame / sd).mean(axis=1)
    equity = np.r_[0.0, returns.cumsum().to_numpy()]
    dd = (equity - np.maximum.accumulate(equity)).min()
    vol = returns.std(ddof=1)
    return returns.mean(), vol, returns.mean() / vol * np.sqrt(12) if vol > 0 else np.nan, dd


def main():
    sample = pd.Series([1.0, 2.0, -1.0])
    assert np.isclose(sample.corr(sample), 1.0)
    assert portfolio(pd.DataFrame({"a": sample, "b": sample})) is not None
    print("Self-check: identical-stream correlation=1; equal-risk weights sum to stream count: OK")
    print("Weekly returns bucketed by UTC exit date; monthly observations summed in bp.")
    streams = {}
    roots = binance_wide.ROOTS
    if not binance_wide.symbols(roots) or not any((p / "funding").is_dir() for p in roots):
        print(f"Flow skipped: missing daily or funding cache in {roots}")
    else:
        k, funding = crypto_flow.load()
        streams["flow"] = weekly(crypto_flow.compute_weeks(k, funding)[0])
    syms = crypto_carry.DEFAULT.symbols
    missing = [str(FUNDING_DIR / f"{s}.csv") for s in syms if not (FUNDING_DIR / f"{s}.csv").exists()]
    if not BINANCE_CACHE_DIR.exists():
        missing.append(str(BINANCE_CACHE_DIR))
    if missing:
        print(f"Carry skipped: missing cache: {', '.join(missing)}")
    else:
        funding = crypto_carry.read_funding(syms)
        sources = SymbolSources.single(BINANCE_CACHE_DIR, syms)
        streams["carry"] = weekly(crypto_carry.compute_weeks(funding, sources)[0])
    rates = {}
    if (i109.FRED / "DGS10.csv").exists():
        rates["development"] = (i109.months(i109.returns("DGS10")).excess - i109.COST).loc[:"2021-08"]
    else:
        print(f"Treasury development skipped: missing {i109.FRED / 'DGS10.csv'}")
    ief = Path("data/cache/alpaca_1d/IEF.csv")
    if ief.exists():
        rates["test"] = (i109.months(i109.etf("IEF", "2021-09-14", "2026-10-31")).raw
                         - i109.COST).loc["2021-10":"2026-10"]
    else:
        print(f"Treasury test skipped: missing {ief}")
    for name, x in streams.items():
        describe(name, "crypto development 2020-2023", x.loc["2020":"2023"], 52)
        describe(name, "crypto test 2024+", x.loc["2024":], 52)
    for regime, x in rates.items():
        describe("Treasury " + ("DGS10 excess" if regime == "development" else "IEF raw"),
                 "Treasury " + regime, x, 12)
    crypto_months = {name: monthly(x) for name, x in streams.items()}
    for label, start, end, rate in (
        ("crypto development / Treasury development", "2020-01", "2021-08", "development"),
        ("crypto development / Treasury test", "2021-10", "2023-12", "test"),
        ("crypto test / Treasury test", "2024-01", "2100-12", "test"),
    ):
        parts = {name: x.loc[start:end] for name, x in crypto_months.items()}
        if rate in rates:
            parts["Treasury"] = rates[rate].loc[start:end]
        print(f"\nOverlap [{label}; {start} to {end}]")
        for a, b in itertools.combinations(parts, 2):
            pair = pd.concat([parts[a], parts[b]], axis=1, join="inner").dropna()
            corr = pair.iloc[:, 0].corr(pair.iloc[:, 1]) if len(pair) >= 2 else np.nan
            print(f"  correlation {a} / {b}: n={len(pair)}, r={corr:.3f}")
        if len(parts) < 2:
            print("  combination unavailable: fewer than two streams")
            continue
        frame = pd.concat(parts, axis=1, join="inner").dropna().sort_index()
        for omitted in [None, *frame.columns]:
            f = frame if omitted is None else frame.drop(columns=omitted)
            result = portfolio(f)
            name = "all" if omitted is None else f"without {omitted}"
            if result is None:
                print(f"  {name}: n={len(f)}, unavailable (insufficient or zero-variance overlap)")
            else:
                mean, sd, sharpe, dd = result
                print(f"  {name}: n={len(f)}, mean={mean:+.3f}, sd={sd:.3f}, "
                      f"annual Sharpe={sharpe:.2f}, max drawdown={dd:.3f} monthly-SD units")
    print("Combination uses average standardized returns; leave-one-out uses the same full overlap.")


if __name__ == "__main__":
    main()
