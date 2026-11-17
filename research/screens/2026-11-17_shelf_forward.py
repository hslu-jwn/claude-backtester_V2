"""Shelf forward logs (M3; docs/research-runner.md › Verdicts and shelf; rules set by the user 2026-11-17).

Every row runs its frozen screen rule unchanged on periods from its forward start and appends them to
research/forward/shelf_<row>.csv (append-only, `backtester.tools.forward_log`). Before any forward period counts, a
canary reruns the same function on the development period and must reproduce the row's registered headline.
Crypto rows (weekly, Monday entry): I-100 wide funding carry, I-84 spot-minus-perp flow, I-98 spot-hedged carry.
Data: perps from `binance_wide.ROOTS` (update: `binance_wide.update`), spot from data/cache/binance_wide_spot (dev)
and data/cache/binance_wide_spot_fwd (`binance_wide.update_spot`, months after 2026-09).
H11 Gotobi G1 (USDJPY, frozen one-time-test grid, engine with today's default costs; per trade, R) and I-71 UK100
review-auction short (per event, bp) read the MT5 cache (kept current by the MT5 download, not here). I-105
overnight -> close reversal at the official open on the wide share universe (per day, bp): official opening and
closing auction prints (Alpaca auctions endpoint), universe formed monthly from fresh daily bars (card 2 rule).
Canaries: crypto rows reproduce net and t; H11 and I-71 reproduce trade counts and gross (their cost tables changed
after registration; today's costs apply forward); I-105 reproduces I-102's diagnostic on the development table
(daily opens; forward uses the official prints, knowledge/ideas.md I-105).
Run: .venv/Scripts/python.exe research/screens/2026-11-17_shelf_forward.py canary | update | log | status
"""

import importlib.util
import json
import math
import shutil
import sys
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data import alpaca, binance_wide
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools import forward_log
from backtester.tools import research_grid as rg
from backtester.tools.entry_screen import load_m1
from backtester.tools.research_helpers import run_variant


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


i78 = _load("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
i100 = _load("i100", "research/screens/2026-11-17_i100_wide_carry_screen.py")
wave1 = _load("wave1", "research/screens/2026-11-15_wave1_xs_crypto_screen.py")
i98 = _load("i98", "research/screens/2026-11-15_i98_basis_carry_screen.py")
i102 = _load("i102", "research/screens/2026-11-17_i102_open_reversal_screen.py")
card2 = _load("card2", "research/screens/2026-11-17_card2_share_universe.py")

FORWARD = Path("research/forward")
SPOT_DEV = Path("data/cache/binance_wide_spot/klines_1d")
SPOT_FWD = Path("data/cache/binance_wide_spot_fwd")
CRYPTO_START = pd.Timestamp("2026-11-23")  # first Monday after the shelf was set up (2026-11-17)
DEV = (pd.Timestamp("2020-01-01"), pd.Timestamp("2023-12-31"))
COLS = ("period", "n", "gross_bp", "net_bp")
COLS_R = ("period", "n", "gross_r", "net_r")
FX_START = date(2026, 11, 18)  # first day after the shelf was set up
SHARE_START = pd.Timestamp("2026-11-18")
UNI_HIST = Path("data/cache/alpaca_meta/universe.csv")
META_F, D1F = Path("data/cache/alpaca_meta_fwd"), Path("data/cache/alpaca_1d_fwd")
AUCT = Path("data/cache/alpaca_auctions_fwd")
LONDON = ZoneInfo("Europe/London")


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


def rows_h11(start, end):
    """Gotobi G1 exactly as the one-time-test grid (research/grids/timed_hold_gotobi_test.toml), USDJPY only."""
    spec = rg.load_grid("research/grids/timed_hold_gotobi_test.toml")
    settings = rg.variant_settings(spec, rg.expand(spec)[0][0])
    res = run_variant(["USDJPY"], start, end, settings, DEFAULT_SOURCES, 4)
    return [
        {
            "period": f"{t.entry_time.astimezone(UTC):%Y-%m-%d}",
            "n": 1,
            "gross_r": t.r_gross,
            "net_r": t.r_net,
        }
        for t in res.trades
        if t.entry_time.astimezone(UTC).date() >= start
    ]


def i71_events(y0, y1):
    """Third Friday of Mar / Jun / Sep / Dec and the last weekday of Feb / May / Aug / Nov (I-71, frozen)."""
    out = set()
    for y in range(y0, y1 + 1):
        for m in (3, 6, 9, 12):
            d = date(y, m, 15)
            out.add(d + timedelta(days=(4 - d.weekday()) % 7))
        for m in (2, 5, 8, 11):
            d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
            while d.weekday() > 4:
                d -= timedelta(days=1)
            out.add(d)
    return out


def rows_i71(sources, start, end):
    """Short UK100 at the close of the 15:29 London M1 bar, cover at the close of the 16:35 bar (I-71, frozen)."""
    d = load_m1("UK100", sources, start, end)
    bars = {}
    for open_s, c in zip(d.open_s.tolist(), d.close.tolist(), strict=True):
        t = datetime.fromtimestamp(open_s, UTC).astimezone(LONDON)
        if (t.hour, t.minute) in ((15, 29), (16, 35)) and t.weekday() < 5:
            bars.setdefault(t.date(), {})[(t.hour, t.minute)] = (
                c,
                datetime.fromtimestamp(open_s + 60, UTC),
            )
    cfg, out = CostConfig(), []
    for day in sorted(e for e in i71_events(start.year, end.year) if start <= e <= end):
        b = bars.get(day, {})
        if (15, 29) not in b or (16, 35) not in b:
            continue
        (p0, t0), (p1, _) = b[(15, 29)], b[(16, 35)]
        rt = cfg.spread("UK100", fill_spread_time(t0), p0) + 2 * cfg.slippage("UK100", p0)
        gross = -1e4 * (p1 / p0 - 1)
        out.append(
            {
                "period": f"{day:%Y-%m-%d}",
                "n": 1,
                "gross_bp": gross,
                "net_bp": gross - 1e4 * rt / p0,
            }
        )
    return out


def rows_i105(t, members, start):
    """t: day x symbol tables open / close / prev_close (SPY included); I-102's sort at the open, open -> close."""
    out = []
    for d in t["close"].index:
        if d < start:
            continue
        m = [s for s in members.get(d.strftime("%Y-%m"), []) if s in t["close"].columns]
        spy = t["open"].loc[d, "SPY"] / t["prev_close"].loc[d, "SPY"] - 1
        f = pd.DataFrame(
            {
                "s": t["open"].loc[d, m] / t["prev_close"].loc[d, m] - 1 - spy,
                "r": (t["close"].loc[d, m] / t["open"].loc[d, m] - 1) * 1e4,
            }
        ).dropna()
        if len(f) >= i102.MIN_NAMES and np.isfinite(spy):
            g = i102.spread(f)
            out.append(
                {
                    "period": f"{d:%Y-%m-%d}",
                    "n": len(f) // 10,
                    "gross_bp": g,
                    "net_bp": g - i102.COST,
                }
            )
    return out


def members_of(path):
    return pd.read_csv(path).groupby("month").symbol.apply(list).to_dict()


def _print(lst, pref, alt):
    p = [q["p"] for q in lst or [] if q.get("c") == pref] or [
        q["p"] for q in lst or [] if q.get("c") == alt
    ]
    return p[0] if p else math.nan


def auctions(symbols, start):
    """Official opening / closing auction prints per symbol and day (condition Q / M preferred, else O / 6)."""
    key, secret = alpaca.keys()
    h = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    end = datetime.now(UTC) - timedelta(minutes=16)
    rows = []
    for i in range(0, len(symbols), 200):
        token = None
        while True:
            url = (
                f"https://data.alpaca.markets/v2/stocks/auctions?symbols={','.join(symbols[i : i + 200])}"
                f"&start={start:%Y-%m-%d}T00:00:00Z&end={end:%Y-%m-%dT%H:%M:00Z}&feed=sip&limit=10000"
                + (f"&page_token={token}" if token else "")
            )
            page = json.loads(
                urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120).read()
            )
            for sym, days in (page.get("auctions") or {}).items():
                rows += [
                    (sym, x["d"], _print(x.get("o"), "Q", "O"), _print(x.get("c"), "M", "6"))
                    for x in days
                ]
            token = page.get("next_page_token")
            if not token:
                break
    a = pd.DataFrame(rows, columns=["symbol", "day", "open", "close"])
    a["day"] = pd.to_datetime(a.day)
    return a


def share_update():
    """Forward universe (card 2 rule on fresh daily bars from 2026-07) and the official auction prints."""
    card2.finra()
    META_F.mkdir(parents=True, exist_ok=True)
    for st in ("active", "inactive"):
        shutil.copy(card2.META / f"assets_{st}.json", META_F / f"assets_{st}.json")
    card2.META, card2.D1 = META_F, D1F
    card2.symbols()
    shutil.rmtree(D1F, ignore_errors=True)  # refetched whole each month (a few hundred requests)
    cand = (META_F / "candidates.txt").read_text().split()
    alpaca.download_batch(
        cand, "1Day", "2026-07-01", alpaca.http_fetch(*alpaca.keys()), D1F, batch=100
    )
    card2.universe()
    allm = {**members_of(UNI_HIST), **members_of(META_F / "universe.csv")}
    syms = sorted({s for mo, v in allm.items() if mo >= "2026-11" for s in v} | {"SPY"})
    AUCT.mkdir(parents=True, exist_ok=True)
    auctions(syms, SHARE_START - pd.Timedelta(days=7)).to_csv(AUCT / "auctions.csv", index=False)


def share_table():
    a = pd.read_csv(AUCT / "auctions.csv", parse_dates=["day"])
    t = {
        k: a.pivot_table(index="day", columns="symbol", values=k, aggfunc="first").sort_index()
        for k in ("open", "close")
    }
    t["prev_close"] = t["close"].shift(1)
    return t


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
    h = rows_h11(date(2015, 1, 2), date(2021, 9, 13))
    g = sum(r["gross_r"] for r in h)
    print(f"H11 dev: {len(h)} trades, gross {g:+.4f} R (registered run: 413, +23.1891)")
    assert len(h) == 413 and abs(g - 23.1891) < 1e-3
    pre = SymbolSources.single("data/cache/histdata_presample", ["UK100"])
    e = rows_i71(pre, date(2010, 1, 1), date(2014, 12, 31)) + rows_i71(
        DEFAULT_SOURCES, date(2015, 1, 1), date(2021, 9, 13)
    )
    g71 = np.mean([r["gross_bp"] for r in e])
    print(f"I-71 dev: {len(e)} events, gross {g71:+.2f} bp (registered 83, +11.7)")
    assert len(e) == 83 and abs(g71 - 11.7) < 0.05
    tab = pd.read_pickle(i102.TABLE)
    tab = {"open": tab["o0930"], "close": tab["close"], "prev_close": tab["prev_close"]}
    r105 = [
        r
        for r in rows_i105(tab, members_of(UNI_HIST), i102.START)
        if pd.Timestamp(r["period"]) <= i102.END
    ]
    gg = np.array([r["gross_bp"] for r in r105])
    tg = gg.mean() / (gg.std(ddof=1) / np.sqrt(len(gg)))
    print(
        f"I-105 dev (daily opens): {len(gg)} days, gross {gg.mean():+.2f}, t {tg:.2f} (I-102 diagnostic +12.89, 3.94)"
    )
    assert abs(gg.mean() - 12.89) < 0.01 and abs(tg - 3.94) < 0.01
    print("CANARY OK")
    return d


def update():
    """Monthly: complete months of perps (all symbols) and spot (forward root) from Binance's archives."""
    month = (pd.Timestamp.now(tz="UTC").normalize().replace(day=1) - pd.Timedelta(days=1)).strftime(
        "%Y-%m"
    )
    binance_wide.update(binance_wide.ROOTS[-1], month)
    binance_wide.update_spot(SPOT_FWD, binance_wide.symbols(), month, start_after="2026-09")
    share_update()


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
    h = rows_h11(FX_START, max(DEFAULT_SOURCES.cached_days("USDJPY")))
    print(
        f"h11: {len(h)} forward trades, {forward_log.append(FORWARD / 'shelf_h11.csv', h, COLS_R)} appended"
    )
    e = rows_i71(DEFAULT_SOURCES, FX_START, max(DEFAULT_SOURCES.cached_days("UK100")))
    print(
        f"i71: {len(e)} forward events, {forward_log.append(FORWARD / 'shelf_i71.csv', e, COLS)} appended"
    )
    if (AUCT / "auctions.csv").exists():
        members = {**members_of(UNI_HIST), **members_of(META_F / "universe.csv")}
        r = rows_i105(share_table(), members, SHARE_START)
        print(
            f"i105: {len(r)} forward days, {forward_log.append(FORWARD / 'shelf_i105.csv', r, COLS)} appended"
        )


def status():
    fb = _load("fb", "research/screens/2026-11-15_fb254_forward_boundaries.py")
    c = 2.071
    for p in sorted(FORWARD.glob("shelf_*.csv")):
        d = pd.read_csv(p)
        x = (d.net_r if "net_r" in d else d.net_bp).to_numpy(float)
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
