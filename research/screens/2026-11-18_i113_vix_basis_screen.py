"""I-113 VIX futures basis (rule in knowledge/ideas.md, 1c9a4cd; Simon & Campasano 2012/13 Table 4 baseline).

Data (public, curl): Cboe CFE monthly VX daily settlements (archive CFE_<code><yy>_VX.csv, per-contract VX_<date>.csv),
Cboe VIX_History.csv, Yahoo ^GSPC daily closes (hedge cell only) -> data/cache/vix/ (development rows only, to DEV_END).
Steps: download, power (signal-free), run (development); I-114 (card 9428854): test_download, test (short leg only).
Run: .venv/Scripts/python.exe research/screens/2026-11-18_i113_vix_basis_screen.py download | power | run | test_download | test
"""

import datetime as dt
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/cache/vix")
TEST_ROOT = Path("data/cache/vix_test")
TEST_START = pd.Timestamp("2021-09-14")
ARCHIVE = "https://cdn.cboe.com/resources/futures/archive/volume-and-price/CFE_{code}{yy}_VX.csv"
PER_CONTRACT = "https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{day}.csv"
VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
SPX_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1={a}&period2={b}&interval=1d"
CODES = "FGHJKMNQUVXZ"
DEV_END = pd.Timestamp("2021-09-13")
TRADE_START = pd.Timestamp("2007-01-02")
REQUOTE = pd.Timestamp("2007-03-26")  # before this VX was quoted at 10x VIX
MULT = 1000.0
COST = 60.0
HOLD = 5
MIN_DAYS = 10
THRESHOLD = 0.10


def get(url, agent=None):
    cmd = ["curl", "-s", "-f", "-L", url] + (["-A", agent] if agent else [])
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    return r.stdout if r.returncode == 0 else None


def rule_settlement(year, month):
    """Wednesday 30 days before the 3rd Friday of the next month (holiday shifts handled by the caller's fallbacks)."""
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    first = dt.date(ny, nm, 1)
    friday = first + dt.timedelta(days=(4 - first.weekday()) % 7 + 14)
    return friday - dt.timedelta(days=30)


def parse(raw):
    text = raw.decode("latin1")
    lines = text[text.index("Trade Date") :].splitlines()
    assert lines[0].split(",")[6] == "Settle", lines[0]
    rows = [ln.split(",") for ln in lines[1:] if ln.strip()]  # some archive rows carry a trailing comma
    return pd.DataFrame(
        {"day": pd.to_datetime([r[0] for r in rows], format="mixed"), "settle": [float(r[6] or 0) for r in rows]}
    )


def download(root=ROOT, end=DEV_END, first=(2005, 1), last=(2021, 10), spx_from="2005-01-01"):
    root.mkdir(parents=True, exist_ok=True)
    vix = pd.read_csv(io.BytesIO(get(VIX_URL)))
    vix["day"] = pd.to_datetime(vix["DATE"], format="%m/%d/%Y")
    vix[vix["day"] <= end][["day", "CLOSE"]].rename(columns={"CLOSE": "vix"}).to_csv(root / "VIX.csv", index=False)
    a, b = int(pd.Timestamp(spx_from).timestamp()), int((end + pd.Timedelta(days=1)).timestamp())
    chart = json.loads(get(SPX_URL.format(a=a, b=b), agent="Mozilla/5.0"))["chart"]["result"][0]
    spx = pd.DataFrame(
        {
            "day": pd.to_datetime(chart["timestamp"], unit="s").normalize(),
            "spx": chart["indicators"]["quote"][0]["close"],
        }
    )
    spx[spx["day"] <= end].dropna().to_csv(root / "SPX.csv", index=False)
    report = []
    for year in range(first[0], last[0] + 1):
        for month in range(1, 13):
            if (year, month) < first:
                continue
            if (year, month) > last:
                break
            parts, settle_day = [], None
            raw = get(ARCHIVE.format(code=CODES[month - 1], yy=f"{year % 100:02d}"))
            if raw:
                arc = parse(raw)
                settle_day = arc["day"].max()
                parts.append(arc)
            base = rule_settlement(year, month)
            for shift in (0, -1, -2, 1):
                day = base + dt.timedelta(days=shift)
                raw = get(PER_CONTRACT.format(day=day.isoformat()))
                if raw:
                    new = parse(raw)
                    parts.append(new)
                    settle_day = pd.Timestamp(day)  # the file name is Cboe's settlement date; archives can stop early
                    break
            if not parts:
                report.append(f"{year}-{month:02d}: missing")
                continue
            if abs((settle_day.date() - base).days) > 2:
                report.append(f"{year}-{month:02d}: settlement {settle_day.date()} far from rule date {base}; skipped")
                continue
            both = pd.concat(parts).drop_duplicates("day", keep="first")  # archive first: it wins on overlaps
            if len(parts) == 2:
                m = parts[0].merge(parts[1], on="day")
                m = m[(m.settle_x > 0) & (m.settle_y > 0)]
                bad = int((abs(m.settle_x - m.settle_y) > 0.001).sum())
                if bad:
                    report.append(f"{year}-{month:02d}: {bad} of {len(m)} overlapping settlements differ")
            both = both[(both["day"] <= end) & (both["settle"] > 0)].sort_values("day")
            both.to_csv(root / f"VX_{settle_day.date()}.csv", index=False)
    print("\n".join(report) or "all months found, overlaps agree")


def calendar(vix_days):
    """VIX trade dates, then weekdays (no NYSE holiday from 2021-09-14 to 2021-10-20; test: last date to 2027-01)."""
    extra = pd.bdate_range(vix_days[-1] + pd.Timedelta(days=1), vix_days[-1] + pd.Timedelta(days=120))
    return pd.DatetimeIndex(vix_days).append(extra)


def load(roots=(ROOT,)):
    """Later roots win: test files carry the full history of contracts the development files cut at DEV_END."""
    vix = pd.concat(pd.read_csv(r / "VIX.csv", parse_dates=["day"]) for r in roots).drop_duplicates("day", keep="last")
    vix = vix.set_index("day").sort_index()["vix"]
    spx = pd.concat(pd.read_csv(r / "SPX.csv", parse_dates=["day"]) for r in roots).drop_duplicates("day", keep="last")
    spx = spx.set_index("day").sort_index()["spx"]
    contracts = {}
    for path in sorted(p for r in roots for p in r.glob("VX_*.csv")):
        s = pd.read_csv(path, parse_dates=["day"]).set_index("day")["settle"]
        s = s.where(s.index >= REQUOTE, s / 10.0)
        contracts[pd.Timestamp(path.stem[3:])] = s
    return vix, spx, contracts


def front_table(vix, contracts):
    """Per VIX trade date: the front monthly VX with >= MIN_DAYS business days to settlement, its settle, days, roll."""
    cal = calendar(vix.index)
    pos = {d: i for i, d in enumerate(cal)}
    settles = sorted(contracts)
    rows = []
    for t in vix.index:
        for s in settles:
            n = pos.get(s, cal.searchsorted(s)) - pos[t]
            if n >= MIN_DAYS:
                f = contracts[s].get(t)
                rows.append((t, s, n, f))
                break
    df = pd.DataFrame(rows, columns=["day", "contract", "days", "f"]).set_index("day")
    df["vix"] = vix
    df["roll"] = (df["f"] - df["vix"]) / df["days"]
    return df


def trades(vix, contracts, front, threshold=THRESHOLD, lag=0, end=DEV_END, start=TRADE_START, sides=(-1, 1)):
    days = vix.index
    out, i = [], days.searchsorted(start)
    while i < len(days):
        t = days[i]
        roll = front["roll"].get(t)
        if roll is None or np.isnan(roll) or abs(roll) <= threshold:
            i += 1
            continue
        side = -1 if roll > 0 else 1
        if side not in sides:
            i += 1
            continue
        k_in, k_out = i + lag, i + lag + HOLD
        if k_out >= len(days) or days[k_out] > end:
            break
        c = contracts[front.loc[t, "contract"]]
        f_in, f_out = c.get(days[k_in]), c.get(days[k_out])
        if f_in is None or f_out is None:
            i += 1
            continue
        out.append(
            {
                "signal": t,
                "entry": days[k_in],
                "exit": days[k_out],
                "side": side,
                "contract": front.loc[t, "contract"],
                "days": int(front.loc[t, "days"]),
                "gross": side * MULT * (f_out - f_in),
                "vix": vix[t],
            }
        )
        i = k_out + 1
    return pd.DataFrame(out)


def hedge(tr, front, spx, contracts):
    """Paper eq. 3-4: daily front-VX change on S&P % return and return x days, fitted on all prior calendar years."""
    days = front.index
    rows = []
    for a, b in zip(days[:-1], days[1:]):
        c = front.loc[a, "contract"]
        f0, f1 = contracts[c].get(a), contracts[c].get(b)
        if f0 is None or f1 is None or a not in spx.index or b not in spx.index:
            continue
        r = 100.0 * (spx[b] / spx[a] - 1.0)
        rows.append((b, f1 - f0, r, r * front.loc[a, "days"]))
    reg = pd.DataFrame(rows, columns=["day", "df", "r", "rd"]).set_index("day")
    coefs = {}
    for year in sorted(set(tr["entry"].dt.year)):
        x = reg[reg.index.year < year]
        X = np.column_stack([np.ones(len(x)), x["r"], x["rd"]])
        coefs[year] = np.linalg.lstsq(X, x["df"].to_numpy(), rcond=None)[0]
    pnl = []
    for _, row in tr.iterrows():
        _, b1, b2 = coefs[row["entry"].year]
        s0, s1 = spx.get(row["entry"]), spx.get(row["exit"])
        if s0 is None or s1 is None:
            pnl.append(np.nan)
            continue
        h = -row["side"] * MULT * (b1 + b2 * row["days"]) / (0.01 * s0 * 50.0)
        pnl.append(h * 50.0 * (s1 - s0))
    return np.array(pnl), coefs


def stats(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return len(x), float("nan"), float("nan")
    return len(x), x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def line(name, x):
    n, m, t = stats(x)
    return f"{name:<34} n {n:4d}  mean ${m:8.0f}  t {t:5.2f}"


def power():
    vix, _, contracts = load()
    front = front_table(vix, contracts)
    days = vix.index
    pnl = []
    for i in range(days.searchsorted(TRADE_START), len(days) - HOLD):
        t, e = days[i], days[i + HOLD]
        c = contracts[front.loc[t, "contract"]]
        if t in c.index and e in c.index:
            pnl.append(MULT * (c[e] - c[t]))
    sd = np.std(pnl, ddof=1)
    for n in (250, 350, 450):
        se = sd / np.sqrt(n)
        print(f"signal-free 5-day front-VX sd ${sd:,.0f} (all {len(pnl)} start dates); n {n}: se ${se:,.0f}, t 3 needs ${3 * se:,.0f} net")


def run():
    vix, spx, contracts = load()
    front = front_table(vix, contracts)
    print("data: missing front settles", int(front["f"].isna().sum()), "of", len(front), "dates")
    early = front[(front.index.year >= 2006) & (front.index.year <= 2011)]
    basis = early["f"] - early["vix"]
    print(f"canary basis 2006-2011 (front >= 10 days): mean {basis.mean():+.2f}, deciles {basis.quantile(0.9):+.2f} / {basis.quantile(0.1):+.2f} (paper +0.14, +2.01 / -1.40; paper's front is nearest contract)")
    tr = trades(vix, contracts, front)
    tr["net"] = tr["gross"] - COST
    tr["hedge"], _ = hedge(tr, front, spx, contracts)
    tr["net_h"] = tr["net"] + tr["hedge"]
    net = tr["net"].to_numpy()
    n, m, t = stats(net)
    half = tr["exit"] <= pd.Timestamp("2013-12-31")
    no2 = np.sort(net)[:-2]
    lag = trades(vix, contracts, front, lag=1)
    lag_net = lag["gross"] - COST
    gates = {
        "net > 0": m > 0,
        "t >= 3.0": t >= 3.0,
        "halves both > 0": tr.loc[half, "net"].mean() > 0 and tr.loc[~half, "net"].mean() > 0,
        "doubled cost > 0": (tr["gross"] - 2 * COST).mean() > 0,
        "without 2 best > 0": no2.mean() > 0,
        "short net > 0": tr.loc[tr.side < 0, "net"].mean() > 0,
        "long net > 0": tr.loc[tr.side > 0, "net"].mean() > 0,
        "lag 1 day net > 0": lag_net.mean() > 0,
    }
    print(line("U unhedged (gated)", net))
    print(line("  gross", tr["gross"]))
    print(line("  halves 2007-2013", tr.loc[half, "net"]))
    print(line("  halves 2014-2021", tr.loc[~half, "net"]))
    print(line("  doubled cost", tr["gross"] - 2 * COST))
    print(line("  without 2 best", no2))
    print(line("  short", tr.loc[tr.side < 0, "net"]))
    print(line("  long", tr.loc[tr.side > 0, "net"]))
    print(line("  lag 1 day", lag_net))
    for name, ok in gates.items():
        print(f"  gate {name:<20} {'pass' if ok else 'FAIL'}")
    print("VERDICT:", "PASSED every development gate" if all(gates.values()) else "KILLED")
    print("reported, not gated:")
    print(line("H hedged", tr["net_h"]))
    print(line("  H short", tr.loc[tr.side < 0, "net_h"]))
    print(line("  H long", tr.loc[tr.side > 0, "net_h"]))
    paper = tr[tr["exit"] <= pd.Timestamp("2011-12-31")]
    print(line("paper window 2007-2011 short U", paper.loc[paper.side < 0, "net"]), "(paper 82, ~$656)")
    print(line("paper window 2007-2011 long U", paper.loc[paper.side > 0, "net"]), "(paper 42, ~$1,040)")
    print(line("paper window 2007-2011 short H", paper.loc[paper.side < 0, "net_h"]), "(paper $539)")
    print(line("paper window 2007-2011 long H", paper.loc[paper.side > 0, "net_h"]), "(paper $908)")
    t15 = trades(vix, contracts, front, threshold=0.15)
    print(line("threshold 0.15 U", t15["gross"] - COST))
    print("by year (U net, H net, trades):")
    for year, g in tr.groupby(tr["exit"].dt.year):
        print(f"  {year}  U {g['net'].sum():9.0f}  H {g['net_h'].sum():9.0f}  n {len(g):3d}")
    print("worst 6 trades U:")
    print(tr.nsmallest(6, "net")[["entry", "exit", "side", "vix", "net", "net_h"]].to_string(index=False))
    print("best 4 trades U:")
    print(tr.nlargest(4, "net")[["entry", "exit", "side", "vix", "net", "net_h"]].to_string(index=False))


def test_download():
    download(TEST_ROOT, pd.Timestamp("2027-12-31"), first=(2021, 10), last=(2027, 1), spx_from="2021-01-01")


def test():
    vix, spx, contracts = load((ROOT, TEST_ROOT))
    front = front_table(vix, contracts)
    end = vix.index[-1]
    w = front[front.index >= TEST_START]
    print(f"test data: VIX to {end.date()}, missing front settles {int(w['f'].isna().sum())} of {len(w)} dates")
    tr = trades(vix, contracts, front, start=TEST_START, end=end, sides=(-1,))
    tr["net"] = tr["gross"] - COST
    tr["hedge"], _ = hedge(tr, front, spx, contracts)
    tr["net_h"] = tr["net"] + tr["hedge"]
    n, m, t = stats(tr["net"])
    no2 = np.sort(tr["net"].to_numpy())[:-2]
    gates = {"net > 0": m > 0, "t >= 1.5": t >= 1.5, "doubled cost > 0": (tr["gross"] - 2 * COST).mean() > 0,
             "without 2 best > 0": no2.mean() > 0}
    print(line("I-114 short U (gated)", tr["net"]))
    print(line("  gross", tr["gross"]))
    print(line("  doubled cost", tr["gross"] - 2 * COST))
    print(line("  without 2 best", no2))
    for name, ok in gates.items():
        print(f"  gate {name:<20} {'pass' if ok else 'FAIL'}")
    verdict = "CONFIRMED lead" if all(gates.values()) else ("FALSIFIED" if m <= 0 else "NOT CONFIRMED")
    print("VERDICT:", verdict)
    print("reported, not gated:")
    lag = trades(vix, contracts, front, lag=1, start=TEST_START, end=end, sides=(-1,))
    print(line("lag 1 day", lag["gross"] - COST))
    print(line("H hedged", tr["net_h"]))
    for year, g in tr.groupby(tr["exit"].dt.year):
        print(f"  {year}  U {g['net'].sum():9.0f}  H {g['net_h'].sum():9.0f}  n {len(g):3d}")
    print(tr.nsmallest(6, "net")[["entry", "exit", "vix", "net", "net_h"]].to_string(index=False))


if __name__ == "__main__":
    {"download": download, "power": power, "run": run, "test_download": test_download, "test": test}[sys.argv[1]]()
