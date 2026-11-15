"""Wave 5 power lines (knowledge/reviews/2026-11-15-fable-idea-universe.md › Wave 5): signal-free, before any look.

For each row: event count N in development and the root-mean-square of the holding-window return (the sd of a +-1
signed trade return when the mean is small). Optimistic MDE at t 3 = 3 x rms / sqrt(N), treating every trade as
independent (date clustering only makes it larger). A row whose halved guessed gross is below this optimistic MDE is
closed without a look. No rule direction is applied, so no mean is seen.
Rows: FB-186 (US macro releases, release + 5 min -> 16:00 NY, 6 symbols), FB-190 (central-bank decisions,
decision + 15 min -> 17:00 NY, the bank's USD pair), FB-066 (AUDNZD from AUDUSD / NZDUSD daily closes, |z| > 2 vs the
250-day mean, 20-day hold), FB-028 / FB-029 (own-decile funding extremes, all USDT perps, 72 h BTC-hedged).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_wave5_power_lines.py
"""
import importlib.util
from datetime import date
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
DEV_END = date(2021, 9, 13)
CAL = pd.read_csv("data/news/economic_events.csv", encoding="utf-8-sig")
CAL["t"] = pd.to_datetime(CAL.scheduled_timestamp_utc)
CAL = CAL[(CAL.impact == "High") & (CAL.t < "2021-09-14")]


def m1_frame(sym, start, end, sources=DEFAULT_SOURCES):
    d = load_m1(sym, sources, start, end)
    return pd.Series(d.close, index=pd.to_datetime(d.open_s, unit="s", utc=True))


def window_returns(sym, times, end_hm="16:00", offset_min=5):
    s = m1_frame(sym, date(2020, 1, 1), DEV_END)
    out = []
    for t in times:
        a = s.asof(t + pd.Timedelta(minutes=offset_min))
        local = t.tz_convert(NY)
        e = pd.Timestamp(f"{local.date()} {end_hm}", tz=NY).tz_convert("UTC")
        if e <= t + pd.Timedelta(minutes=offset_min):
            continue
        b = s.asof(e)
        if np.isfinite(a) and np.isfinite(b):
            out.append(b / a - 1)
    return np.array(out) * 1e4


def line(name, r, guess_lo, guess_hi, extra=""):
    r = np.asarray(r, float)
    rms = np.sqrt(np.mean(r**2))
    mde = 3 * rms / np.sqrt(len(r))
    verdict = "SCREEN" if guess_hi / 2 >= mde else "CLOSED on power"
    print(f"{name}: N {len(r)}, rms {rms:.0f} bp, optimistic MDE(t3) {mde:.1f} bp; halved guess {guess_lo / 2:.1f}-"
          f"{guess_hi / 2:.1f} -> {verdict} {extra}")


def fb186():
    names = ["Non-Farm Employment Change", "CPI m/m", "CPI y/y", "ISM Manufacturing PMI", "ISM Services PMI"]
    times = sorted(set(CAL[(CAL.currency == "USD") & CAL.event_name.isin(names)].t))
    r = np.concatenate([window_returns(s, times) for s in ("US30", "NAS100", "GER40", "EURUSD", "USDJPY", "XAUUSD")])
    line("FB-186 macro release continuation", r, 5, 15, f"({len(times)} release times 2020-01..2021-09)")


def fb190():
    banks = {"EUR": ("EURUSD", "Main Refinancing Rate"), "GBP": ("GBPUSD", "Official Bank Rate"),
             "JPY": ("USDJPY", "BOJ Policy Rate|Monetary Policy Statement"), "AUD": ("AUDUSD", "Cash Rate"),
             "NZD": ("NZDUSD", "Official Cash Rate"), "CAD": ("USDCAD", "Overnight Rate"),
             "CHF": ("USDCHF", "SNB Monetary Policy Assessment")}
    r, n = [], 0
    for cur, (sym, pat) in banks.items():
        times = sorted(set(CAL[(CAL.currency == cur) & CAL.event_name.str.contains(pat)].t))
        n += len(times)
        r.append(window_returns(sym, times, end_hm="17:00", offset_min=15))
    line("FB-190 central-bank continuation", np.concatenate(r), 5, 15, f"({n} decisions 2020-01..2021-09)")


def daily_close(sym):
    pre = m1_frame(sym, date(2010, 1, 1), date(2014, 12, 31), SymbolSources.single("data/cache/histdata_presample", [sym]))
    dev = m1_frame(sym, date(2015, 1, 1), DEV_END)
    s = pd.concat([pre, dev])
    return s.groupby(s.index.tz_convert(NY).date).last()


def fb066():
    x = np.log(daily_close("AUDUSD")) - np.log(daily_close("NZDUSD"))
    x = x.dropna()
    z = (x - x.rolling(250).mean()) / x.rolling(250).std()
    fwd = (x.shift(-20) - x) * 1e4
    hit = (z.abs() > 2) & fwd.notna()
    days, last = [], None  # one position at a time: a new entry only after the 20-day hold ends
    for i, (d, h) in enumerate(hit.items()):
        if h and (last is None or i >= last + 20):
            days.append(d)
            last = i
    line("FB-066 AUDNZD range reversion", fwd.loc[days], 80, 150,
         f"({len(days)} entries {x.index[250]}..{x.index[-1]}; 20-day rms over all days {np.sqrt((fwd**2).mean()):.0f} bp)")


def fb028_029():
    spec = importlib.util.spec_from_file_location("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
    i78 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(i78)
    k, fund = i78.load()
    btc = k["BTCUSDT"].close
    r_hi, r_lo = [], []
    for sym, d in k.items():
        if sym == "BTCUSDT" or sym not in fund:
            continue
        f = fund[sym].resample("1D").sum()  # daily funding
        c = d.close
        j = pd.concat({"c": c, "b": btc, "f": f}, axis=1).dropna()
        if len(j) < 200:
            continue
        dec_hi = j.f.expanding(90).quantile(0.9).shift(1)
        dec_lo = j.f.expanding(90).quantile(0.1).shift(1)
        hedged = (np.log(j.c.shift(-3) / j.c) - np.log(j.b.shift(-3) / j.b)) * 1e4
        for cond, out in ((j.f > dec_hi, r_hi), (j.f < dec_lo, r_lo)):
            ev = hedged[cond & hedged.notna()]
            out.append(ev.iloc[::3])  # at most one entry per 72 h per coin
    for name, out, lo, hi in (("FB-028 funding top decile short 72 h", r_hi, 50, 120),
                              ("FB-029 funding bottom decile long 72 h", r_lo, 50, 150)):
        ev = pd.concat(out)
        line(name, ev.to_numpy(), lo, hi, "(OI / price filters not applied: they only shrink N)")
        dm = ev.groupby(level=0).mean()  # date-clustered: one mean per entry day
        line(f"  {name[:6]} date-clustered", dm.to_numpy(), lo, hi, f"({len(dm)} entry days)")


if __name__ == "__main__":
    print("FB-215 auction pooled: I-71 sd/event ~ 9 x sqrt(83) / 2.16 = 38 bp; ~47 MSCI dates x 6 indices -> optimistic"
          f" MDE {3 * 38 / np.sqrt(47 * 6):.1f} bp vs halved guess 3 bp -> CLOSED on power")
    print(f"FB-040 unlock short: sd ~2,000 bp, ~150 events a year x 3 -> MDE {3 * 2000 / np.sqrt(450):.0f} bp vs halved "
          "guess 100-200 bp (and the unlock data is unverified) -> CLOSED on power")
    fb186()
    fb190()
    fb066()
    fb028_029()
