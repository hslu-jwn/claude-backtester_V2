"""I-103 step 1 (Fable card 7): signal-free size audit of the leveraged single-stock ETF rebalance flow.

Rule fixed in knowledge/ideas.md (1b78850). No return after 15:30 is computed here. Steps:
  funds   single-stock daily leveraged / inverse funds from Alpaca's asset names -> data/cache/sec_nport/funds.csv
          (review the printed list; company-named funds need the NAMES map)
  nport   SEC N-PORT net assets per fund series (contact string from the Credential Manager, docs/share-universe.md)
  late    per development day, one 1-min request 15:27-16:00 ET for the underlyings -> data/cache/alpaca_late/<day>.csv
  audit   F = sum (L^2 - L) x net assets x |underlying 09:30 open -> 15:30|; ratio = F / 15:30-16:00 dollar volume;
          go / no-go: >= 300 name-days with ratio >= 5 % (development: first launch .. 2024-12-31)
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i103_step1_flow_audit.py funds | nport | late | audit
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data import alpaca

META = Path("data/cache/alpaca_meta")
D1 = Path("data/cache/alpaca_1d")
NPORT = Path("data/cache/sec_nport")
LATE = Path("data/cache/alpaca_late")
DEV_END = pd.Timestamp("2024-12-31")
FIRST_LAUNCH = pd.Timestamp(
    "2022-07-01"
)  # first single-stock leveraged ETF (AXS TSLQ) listed 2022-07-13
NY = ZoneInfo("America/New_York")
# company-named funds (T-Rex and others): name fragment -> underlying ticker
NAMES = {
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Nvidia": "NVDA",
    "MicroStrategy": "MSTR",
    "Strategy": "MSTR",
    "Coinbase": "COIN",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Netflix": "NFLX",
    "Palantir": "PLTR",
    "Advanced Micro": "AMD",
    "AMD": "AMD",
    "Broadcom": "AVGO",
    "Super Micro": "SMCI",
    "Robinhood": "HOOD",
    "Rivian": "RIVN",
    "Snowflake": "SNOW",
    "Uber": "UBER",
    "Shopify": "SHOP",
    "Eli Lilly": "LLY",
    "Taiwan Semiconductor": "TSM",
    "Arm": "ARM",
    "Marathon": "MARA",
    "Riot": "RIOT",
    "Reddit": "RDDT",
    "Oracle": "ORCL",
    "Salesforce": "CRM",
}
PATTERNS = [
    re.compile(
        r"Daily (?P<u>[A-Z]{1,5}) (?P<d>Bull|Bear) (?P<l>[\d.]+)X", re.IGNORECASE
    ),  # Direxion
    re.compile(
        r"(?P<l>-?[\d.]+)[xX] (?P<d>Long|Short|Inverse) (?P<u>[A-Z]{1,5}) (Daily|ETF)"
    ),  # GraniteShares, Tradr, Leverage Shares
    re.compile(
        r"Daily Target (?P<l>[\d.]+)[xX] (?P<d>Long|Short) (?P<u>[A-Z]{1,5}) ETF"
    ),  # Defiance
    re.compile(r"AXS (?P<u>[A-Z]{1,5}) (?P<d>Bear|Bull) Daily"),  # AXS 1x inverse
    re.compile(
        r"(?P<l>[\d.]+)[xX] (?P<d>Long|Short|Inverse) (?P<name>[A-Z][A-Za-z .]+?) Daily Target"
    ),  # T-Rex
]


def leverage(m):
    lev = float(m.groupdict().get("l") or 1.0)
    neg = m.group("d").lower() in ("bear", "short", "inverse")
    return -abs(lev) if neg else abs(lev)


def funds():
    a = []
    for st in ("active", "inactive"):
        a += json.loads((META / f"assets_{st}.json").read_text())
    stocks = {p.stem for p in D1.glob("*.csv")}
    rows = []
    for x in a:
        name = x.get("name") or ""
        if "Daily" not in name or x["exchange"] == "OTC":
            continue
        for pat in PATTERNS:
            m = pat.search(name)
            if not m:
                continue
            u = m.groupdict().get("u")
            if not u and m.groupdict().get("name"):
                u = next(
                    (t for k, t in NAMES.items() if m.group("name").strip().startswith(k)), None
                )
            if u and u in stocks:
                rows.append({"fund": x["symbol"], "underlying": u, "L": leverage(m), "name": name})
            break
    f = pd.DataFrame(rows).drop_duplicates("fund").sort_values(["underlying", "fund"])
    NPORT.mkdir(parents=True, exist_ok=True)
    f.to_csv(NPORT / "funds.csv", index=False)
    print(f"{len(f)} single-stock funds on {f.underlying.nunique()} underlyings")
    print(f.to_string(index=False, max_colwidth=60))


def sec_get(url, ua):
    for k in range(5):
        r = subprocess.run(
            ["curl", "-s", "-A", ua, "-w", "\n%{http_code}", url],
            check=False,
            capture_output=True,
            timeout=120,
        )
        body, _, code = r.stdout.rpartition(b"\n")
        time.sleep(0.15)  # SEC fair access: <= 10 requests a second
        if code == b"200":
            return body.decode("utf-8", "replace")
        if code == b"404":
            return None
        time.sleep(3 * (k + 1))
    raise RuntimeError(f"SEC HTTP {code.decode()} for {url}")


def nport():
    import keyring

    ua = f"backtester-research {keyring.get_password('backtester-contact', 'email')}"
    tick = {
        r[3]: r
        for r in json.loads(sec_get("https://www.sec.gov/files/company_tickers_mf.json", ua))[
            "data"
        ]
    }
    f = pd.read_csv(NPORT / "funds.csv")
    for fund in f.fund:
        path = NPORT / f"{fund}.csv"
        if path.exists():
            continue
        if fund not in tick:
            print(f"{fund}: not in SEC's fund ticker map", flush=True)
            pd.DataFrame(columns=["date", "net_assets"]).to_csv(path, index=False)
            continue
        cik, series = tick[fund][0], tick[fund][1]
        rows, start = [], 0
        while True:
            atom = sec_get(
                f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={series}&type=NPORT-P"
                f"&dateb=&owner=include&count=100&start={start}&output=atom",
                ua,
            )
            links = re.findall(r"<filing-href>([^<]+)</filing-href>", atom or "")
            for link in links:
                acc = link.rsplit("/", 2)[-2]
                x = (
                    sec_get(
                        f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml", ua
                    )
                    or ""
                )
                d, na = re.findall(r"<repPdDate>([^<]+)<", x), re.findall(r"<netAssets>([^<]+)<", x)
                if d and na and series in x:
                    rows.append((d[0], float(na[0])))
            if len(links) < 100:
                break
            start += 100
        pd.DataFrame(sorted(set(rows)), columns=["date", "net_assets"]).to_csv(path, index=False)
        print(f"{fund}: {len(rows)} reports", flush=True)


def daily(sym):
    p = D1 / f"{sym}.csv"
    if not p.exists() or p.stat().st_size < 60:
        return None
    d = pd.read_csv(p, usecols=["ts", "open", "close"])
    d.index = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY).dt.tz_localize(None).dt.normalize()
    return d[~d.index.duplicated()]


def late():
    f = pd.read_csv(NPORT / "funds.csv")
    unders = sorted(f.underlying.unique())
    fetch = alpaca.http_fetch(*alpaca.keys())
    alpaca.download_batch(sorted(set(f.fund)), "1Day", "2015-07-01", fetch, D1)
    first = FIRST_LAUNCH  # fund tickers can carry an older security's history (reused symbols)
    days = daily("SPY").index
    LATE.mkdir(parents=True, exist_ok=True)
    for d in days[(days >= first) & (days <= DEV_END)]:
        path = LATE / f"{d:%Y-%m-%d}.csv"
        if path.exists():
            continue
        t0 = d.replace(hour=15, minute=27).tz_localize(NY).tz_convert("UTC")
        t1 = d.replace(hour=16, minute=0).tz_localize(NY).tz_convert("UTC")
        params = {
            "symbols": ",".join(unders),
            "timeframe": "1Min",
            "limit": 10000,
            "adjustment": "split",
            "feed": "sip",
            "start": f"{t0:%Y-%m-%dT%H:%M:00Z}",
            "end": f"{t1:%Y-%m-%dT%H:%M:00Z}",
        }
        rows = []
        while True:
            page = fetch(params)
            for s, bars in (page.get("bars") or {}).items():
                rows += [(s, b["t"], b["c"], b["v"], b.get("vw") or b["c"]) for b in bars]
            if not page.get("next_page_token"):
                break
            params = {**params, "page_token": page["next_page_token"]}
        b = pd.DataFrame(rows, columns=["symbol", "ts", "close", "volume", "vwap"])
        cut = d.replace(hour=15, minute=30).tz_localize(NY).tz_convert("UTC")
        after = pd.to_datetime(b.ts, utc=True) >= cut
        out = pd.DataFrame(
            {
                "p1530": b[~after].groupby("symbol").close.last(),
                "dv_late": (b[after].vwap * b[after].volume).groupby(b[after].symbol).sum(),
            }
        ).rename_axis("symbol")
        out.to_csv(path)
        if d.day <= 3:
            print(f"late {d.date()}: {len(out)} underlyings", flush=True)


def audit():
    f = pd.read_csv(NPORT / "funds.csv")
    late_t = {
        pd.Timestamp(p.stem): pd.read_csv(p, index_col="symbol") for p in sorted(LATE.glob("*.csv"))
    }
    days = sorted(late_t)
    aum = {}
    for fund in f.fund:
        rep, px = pd.read_csv(NPORT / f"{fund}.csv"), daily(fund)
        if rep.empty or px is None:
            continue
        rep.index = pd.to_datetime(rep.date)
        c = px.close.reindex(days).ffill()
        a = pd.Series(np.nan, index=days)
        for (
            d0,
            na,
        ) in (
            rep.net_assets.items()
        ):  # carried forward by the fund's own return until the next report (A1)
            seg = c.loc[d0:]
            if len(seg) and np.isfinite(seg.iloc[0]):
                a.loc[seg.index] = na * seg / seg.iloc[0]
        aum[fund] = a
    rows = []
    for u, g in f.groupby("underlying"):
        px = daily(u)
        if px is None:
            continue
        for d in days:
            t = late_t[d]
            if (
                u not in t.index
                or d not in px.index
                or not np.isfinite(t.loc[u, "dv_late"])
                or t.loc[u, "dv_late"] <= 0
            ):
                continue
            r = abs(t.loc[u, "p1530"] / px.loc[d, "open"] - 1)
            flow = np.nansum(  # a fund without net assets that day (not launched / no report yet) adds 0
                [
                    (L * L - L) * aum[x].get(d, np.nan)
                    for x, L in zip(g.fund, g.L, strict=True)
                    if x in aum
                ]
            )
            if np.isfinite(flow) and flow > 0:
                rows.append((d, u, flow * r, t.loc[u, "dv_late"]))
    a = pd.DataFrame(rows, columns=["day", "underlying", "F", "dv_late"])
    a["ratio"] = a.F / a.dv_late
    n5, n10 = int((a.ratio >= 0.05).sum()), int((a.ratio >= 0.10).sum())
    print(
        f"name-days with a fund flow: {len(a)} ({a.day.min().date()} .. {a.day.max().date()}), "
        f"{a.underlying.nunique()} underlyings, funds with net assets {len(aum)} of {len(f)}"
    )
    print(
        f"ratio >= 5 %: {n5} name-days on {a[a.ratio >= 0.05].day.nunique()} dates; >= 10 %: {n10}"
    )
    print("by year (ratio >= 5 %):", a[a.ratio >= 0.05].groupby(a.day.dt.year).size().to_dict())
    print(
        "top underlyings (ratio >= 5 %):",
        a[a.ratio >= 0.05].underlying.value_counts().head(10).to_dict(),
    )
    print("ratio quantiles:", a.ratio.quantile([0.5, 0.9, 0.99]).round(4).to_dict())
    print(
        "GO (>= 300 name-days at >= 5 %)"
        if n5 >= 300
        else "NO-GO: closed on size, no return looked at"
    )


if __name__ == "__main__":
    {"funds": funds, "nport": nport, "late": late, "audit": audit}[sys.argv[1]]()
