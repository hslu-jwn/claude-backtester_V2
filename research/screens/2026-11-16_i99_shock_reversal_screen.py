"""I-99 single-name shock reversal vs a flat index (Fable FB-121; rule fixed in knowledge/ideas.md, commit aff8c2c).

Development only 2016-01-04 .. 2021-09-13, Alpaca 1Min SIP (data/cache/alpaca, ignored), 33 FTMO names of I-96, QQQ
as the index. Price grid per session: P[0] = 09:30 open, P[m] = close of the bar opening 09:30 + m - 1 (m = 1..390),
forward-filled. r30 at m = P[m] / P[m-30] - 1, evaluated m = 30 (10:00) .. 330 (15:00); entry = open of the bar
opening at 09:30 + m; exit P[325] (15:55). sigma30 and the gap sd use only the previous 20 sessions.
Run: .venv/Scripts/python.exe research/screens/2026-11-16_i99_shock_reversal_screen.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/cache/alpaca")
START, END = pd.Timestamp("2016-01-04"), pd.Timestamp("2021-09-13")
NAMES = [
    "AAPL",
    "AMZN",
    "GOOG",
    "MSFT",
    "NVDA",
    "TSLA",
    "V",
    "WMT",
    "META",
    "GE",
    "BA",
    "RTX",
    "LMT",
    "PLTR",
    "AMD",
    "QCOM",
    "AVGO",
    "CSCO",
    "JNJ",
    "MCD",
    "SBUX",
    "KO",
    "MSTR",
    "CVX",
    "FDX",
    "JPM",
    "DIS",
    "IBM",
    "SNOW",
    "ASML",
    "AZN",
    "BRK.B",
    "XOM",
]
SPREADS = pd.read_csv("research/share_spreads_2026-11-15.csv").set_index("symbol")
SLIP, LOOKBACK, MIN_DAYS = 1.0, 20, 15
LISTED = {
    "SNOW": "2020-09-16",
    "PLTR": "2020-09-30",
}  # Alpaca keeps the reused ticker's old history (SNOW = Intrawest 2016-17)


def grid(sym):
    """Sessions x 391 price grid (P[0] = open, P[m] = close at 09:30 + m) and bar opens, NY trading days."""
    files = [f for f in sorted((ROOT / sym).glob("*.csv")) if "2015-12" <= f.stem <= "2021-09"]
    d = pd.concat([pd.read_csv(f) for f in files if f.stat().st_size > 60])
    t = pd.to_datetime(d.ts, utc=True).dt.tz_convert("America/New_York")
    m = (t.dt.hour * 60 + t.dt.minute - 570).to_numpy()
    keep = (m >= 0) & (m < 390)
    keep &= (t >= pd.Timestamp(LISTED.get(sym, "2000-01-01"), tz="America/New_York")).to_numpy()
    day = t.dt.tz_localize(None).dt.normalize().to_numpy()[keep]
    days = pd.DatetimeIndex(np.unique(day))
    row = days.get_indexer(day)
    P = np.full((len(days), 391), np.nan)
    O = np.full((len(days), 390), np.nan)
    P[row, m[keep] + 1] = d.close.to_numpy()[keep]
    O[row, m[keep]] = d.open.to_numpy()[keep]
    P[:, 0] = (
        pd.DataFrame(O).bfill(axis=1).iloc[:, 0].to_numpy()
    )  # first traded open of the session
    P = pd.DataFrame(P).ffill(axis=1).to_numpy()
    O = np.where(np.isnan(O), P[:, :390], O)  # a bar with no trade opens at the last price
    return days, P, O


def prior_sd(x, n=LOOKBACK, k=1):
    """sd of the previous n sessions' values (x: sessions x k), NaN with fewer than MIN_DAYS sessions."""
    s = pd.DataFrame(x)
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = s.iloc[max(0, i - n) : i].to_numpy().ravel()
        w = w[~np.isnan(w)]
        if len(w) >= MIN_DAYS * k:
            out[i] = w.std(ddof=1)
    return out


def prepare(sym, cal):
    days, P, O = grid(sym)
    idx = cal.get_indexer(days)
    ok = idx >= 0
    G = np.full((len(cal), 391), np.nan)
    Op = np.full((len(cal), 390), np.nan)
    G[idx[ok]], Op[idx[ok]] = P[ok], O[ok]
    r30 = G[:, 30:] / G[:, :-30] - 1  # column j = minute j + 30
    blocks = G[:, 30::30] / G[:, 0:-30:30] - 1  # 13 non-overlapping 30-min returns
    sig = prior_sd(blocks, k=13)
    close = G[:, 390]
    prev = np.r_[np.nan, close[:-1]]
    cc = close / prev - 1
    gap_sd = prior_sd(cc[:, None])
    gap = G[:, 0] / prev - 1
    return {"G": G, "O": Op, "r30": r30, "sig": sig, "gap": gap, "gap_sd": gap_sd}


def events(s, q, sign, k, gap_days=False):
    """First trigger per session: sign * r30 <= -k sigma (sign 1 = drop -> long) with |QQQ r30| <= 0.5 sigma."""
    big_gap = np.abs(s["gap"]) > 2 * s["gap_sd"]
    valid = ~(np.isnan(s["sig"]) | np.isnan(q["sig"]) | np.isnan(s["gap_sd"])) & (
        big_gap == gap_days
    )
    with np.errstate(invalid="ignore"):
        hit = (sign * s["r30"][:, :301] <= -k * s["sig"][:, None]) & (
            np.abs(q["r30"][:, :301]) <= 0.5 * q["sig"][:, None]
        )
    rows = []
    for i in np.flatnonzero(valid & hit.any(axis=1)):
        m = 30 + int(hit[i].argmax())  # first trigger of the session
        rows.append((i, sign * (s["G"][i, 325] / s["O"][i, m] - 1) * 1e4))
    return rows


def summary(df, cost_mult=1.0):
    net = df.gross - cost_mult * df.cost
    by_date = net.groupby(df.date).mean()
    t = by_date.mean() / by_date.std(ddof=1) * np.sqrt(len(by_date))
    return net, by_date, t


def main():
    q_days, _, _ = grid("QQQ")
    cal = q_days[(q_days >= START - pd.Timedelta(days=45)) & (q_days <= END)]
    q = prepare("QQQ", cal)
    stocks = {n: prepare(n, cal) for n in NAMES if (ROOT / n).exists()}
    missing = [n for n in NAMES if n not in stocks]
    print(f"{len(stocks)} names loaded; missing: {missing or 'none'}")

    def table(sign, k, gap_days=False):
        out = []
        for n, s in stocks.items():
            c = SPREADS.loc[n, "all_bp"] / 2 + SPREADS.loc[n, "close_bp"] / 2 + 2 * SLIP
            out += [(cal[i], n, g, c) for i, g in events(s, q, sign, k, gap_days)]
        df = pd.DataFrame(out, columns=["date", "name", "gross", "cost"])
        return df[(df.date >= START) & (df.date <= END)]

    df = table(1, 3.0)
    n = len(df)
    print(f"events: {n} on {df.date.nunique()} dates")
    if n < 300:
        print("UNDERPOWERED (< 300 events): no verdict, card stays a card")
    net, by_date, t = summary(df)
    print(
        f"gross {df.gross.mean():+.1f} bp, cost {df.cost.mean():.1f}, net {net.mean():+.1f}, "
        f"t (per-date) {t:.2f}, sd {net.std():.0f}"
    )
    h1 = net[df.date.dt.year <= 2018].mean()
    h2 = net[df.date.dt.year >= 2019].mean()
    net2, _, t2 = summary(df, 2.0)
    best = by_date.nlargest(2).index
    nb = net[~df.date.isin(best)].mean()
    kills = {
        "net <= 0": net.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost": net2.mean() <= 0,
        "without 2 best dates": nb <= 0,
    }
    print(
        f"halves {h1:+.1f} / {h2:+.1f}; doubled cost {net2.mean():+.1f} (t {t2:.2f}); without 2 best dates {nb:+.1f}"
    )
    print(
        "kills hit:",
        [k for k, v in kills.items() if v] or "none",
        "->",
        "PASS" if n >= 300 and not any(kills.values()) else "KILLED" if n >= 300 else "NO VERDICT",
    )
    print("\nreported, not gates:")
    for name, d in (
        ("mirror: short after +3 sigma", table(-1, 3.0)),
        ("gap days (earnings control)", table(1, 3.0, True)),
        ("dose 2.5 sigma", table(1, 2.5)),
        ("dose 4 sigma", table(1, 4.0)),
    ):
        if len(d):
            nn, _, tt = summary(d)
            print(
                f"  {name}: {len(d)} events, gross {d.gross.mean():+.1f}, net {nn.mean():+.1f}, t {tt:.2f}"
            )
    print(
        "  by year (net):",
        net.groupby(df.date.dt.year).agg(["count", "mean"]).round(1).to_dict("index"),
    )


if __name__ == "__main__":
    main()
