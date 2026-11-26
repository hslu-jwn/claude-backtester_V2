"""CRSP fast-track IPO census (return-blind; feasibility, not a test).

The only price read per IPO is its first-day close (eligibility input); no later price, return or index data.
Sources: Nasdaq IPO calendar (priced deals), SEC form index (424B4 -> CIK), SEC submissions (SIC, address) and
companyfacts (cover-page shares outstanding).
Run: .venv/Scripts/python.exe research/screens/2026-11-26_fasttrack_census.py download | census
"""

import gzip
import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

C = Path("data/cache/fasttrack")
D1 = Path("data/cache/alpaca_1d")
UNIVERSES = [
    Path("data/cache/alpaca_meta/universe.csv"),
    Path("data/cache/alpaca_meta_fwd/universe.csv"),
]
REPORT = Path("knowledge/research/reports/2026-11-26_fasttrack-census.md")
LOCK, LAST, UA = threading.Lock(), [0.0], []
US_STATES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "PR",
}
# UNVERIFIED proxy: the CRSP fast-track size line, USD bn (R8 report: about 2.4 in Dec 2024, 3.0 in Jun 2026).
BP_REF = 2.4e9


def get(url, sec=True, gap=0.13):
    """curl (the venv Python lacks the issuer CA chain); returns (status, body bytes). SEC: at most ~8 requests/s."""
    import keyring

    with LOCK:
        if sec and not UA:
            UA.append(f"backtester-research {keyring.get_password('backtester-contact', 'email')}")
        ua = UA[0] if sec else "Mozilla/5.0"
        time.sleep(max(0.0, LAST[0] + gap - time.time()))
        LAST[0] = time.time()
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-m", "120", "-A", ua, "-w", "\n%{http_code}", url],
        capture_output=True,
        check=False,
    )
    body, _, code = r.stdout.rpartition(b"\n")
    return code.decode(), body


def nasdaq_months():
    (C / "nasdaq").mkdir(parents=True, exist_ok=True)
    for m in pd.period_range("2017-03", "2025-12", freq="M"):
        p = C / "nasdaq" / f"{m}.json"
        if p.exists():
            continue
        for wait in (0.5, 5, 30):
            code, body = get(
                f"https://api.nasdaq.com/api/ipo/calendar?date={m}", sec=False, gap=wait
            )
            if code == "200" and body.lstrip().startswith(b"{"):
                p.write_bytes(body)
                break
            print("nasdaq", m, code, "retry slower (no bypass)", flush=True)
        else:
            print("nasdaq", m, "DROPPED after backoff", flush=True)


def form_idx():
    (C / "idx").mkdir(exist_ok=True)
    for q in pd.period_range("2017Q1", "2026Q1", freq="Q"):
        p = C / "idx" / f"{q}.csv"
        if p.exists():
            continue
        code, body = get(
            f"https://www.sec.gov/Archives/edgar/full-index/{q.year}/QTR{q.quarter}/form.gz"
        )
        assert code == "200", (q, code)
        rows = []
        for line in gzip.decompress(body).decode("latin-1").splitlines():
            if line.startswith(("424B4", "424B1")):
                t = line[:12].strip()
                m = re.match(r"(.*?)\s+(\d{1,10})\s+(\d{4}-\d\d-\d\d)\s+(\S+)$", line[12:].strip())
                if m:
                    rows.append([t, m[1].strip(), int(m[2]), m[3], m[4]])
        pd.DataFrame(rows, columns=["form", "name", "cik", "date", "path"]).to_csv(p, index=False)


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower())
    s = re.sub(
        r"\b(inc|corp|corporation|co|ltd|limited|plc|holdings?|group|the|llc|lp|de|new|class|a|ordinary shares?)\b",
        " ",
        s,
    )
    return " ".join(s.split())


def ipo_list():
    rows = []
    for p in sorted((C / "nasdaq").glob("*.json")):
        j = json.loads(p.read_text())
        rows.extend((j.get("data", {}).get("priced") or {}).get("rows") or [])
    d = pd.DataFrame(rows)
    d["date"] = pd.to_datetime(d.pricedDate, format="%m/%d/%Y")
    d["shares_off"] = pd.to_numeric(d.sharesOffered.str.replace(",", ""), errors="coerce")
    d["price"] = pd.to_numeric(d.proposedSharePrice.str.replace(",", ""), errors="coerce")
    d = d.drop_duplicates(["proposedTickerSymbol", "date"])
    return d[(d.date >= "2017-03-01") & (d.date <= "2025-12-31")].reset_index(drop=True)


def match_cik(d):
    idx = pd.concat([pd.read_csv(p) for p in sorted((C / "idx").glob("*.csv"))])
    idx["date"] = pd.to_datetime(idx.date)
    idx["n"] = idx.name.map(norm)
    by = {k: g for k, g in idx.groupby("n")}
    out = []
    for _, r in d.iterrows():
        g = by.get(norm(r.companyName))
        cik = None
        if g is not None:
            g = g[
                (g.date >= r.date - pd.Timedelta(days=4))
                & (g.date <= r.date + pd.Timedelta(days=4))
            ]
            if len(g):
                cik = int(g.cik.iloc[0])
        out.append(cik)
    return out


def fetch_cik(cik):
    (C / "facts").mkdir(exist_ok=True)
    (C / "subs").mkdir(exist_ok=True)
    pf, ps = C / "facts" / f"{cik}.json", C / "subs" / f"{cik}.json"
    if not ps.exists():
        code, body = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        out = {"code": code}
        if code == "200":
            j = json.loads(body)
            out |= {
                "sic": j.get("sic"),
                "state": (j.get("addresses", {}).get("business") or {}).get("stateOrCountry"),
                "inc": j.get("stateOfIncorporation"),
                "name": j.get("name"),
            }
        ps.write_text(json.dumps(out))
    if not pf.exists():
        code, body = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        out = {"code": code, "shares": []}
        if code == "200":
            sh = (
                json.loads(body)["facts"]
                .get("dei", {})
                .get("EntityCommonStockSharesOutstanding", {})
            )
            out["shares"] = [
                [x["end"], x["val"], x["filed"], x["accn"]]
                for x in sh.get("units", {}).get("shares", [])
            ]
        pf.write_text(json.dumps(out))


def download():
    C.mkdir(parents=True, exist_ok=True)
    nasdaq_months()
    form_idx()
    d = ipo_list()
    d["cik"] = match_cik(d)
    ciks = sorted(set(d.cik.dropna().astype(int)))
    print(len(d), "priced deals,", len(ciks), "matched CIKs", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(4) as ex:
        for i, _ in enumerate(ex.map(fetch_cik, ciks)):
            if i % 200 == 0:
                print(i, round(time.time() - t0), "s", flush=True)


def first_day_close(sym, d):
    """First-day close only: the first row of the file, if it falls 0-7 days after the pricing date (else None)."""
    p = D1 / f"{sym}.csv"
    if not p.exists():
        return None, None
    x = pd.read_csv(p, usecols=["ts", "close"], nrows=1)
    if x.empty:
        return None, None
    day = pd.Timestamp(x.ts.iloc[0][:10])
    return (float(x.close.iloc[0]), day) if 0 <= (day - d).days <= 7 else (None, day)


def cover_shares(cik, d):
    """Cover-page shares of the first periodic report filed after pricing (distinct class values of that filing summed)."""
    f = json.loads((C / "facts" / f"{cik}.json").read_text())
    rows = [r for r in f["shares"] if r[2] > d.strftime("%Y-%m-%d")]
    if not rows:
        return None
    first = min(rows, key=lambda r: (r[2], r[0]))
    return float(sum({r[1] for r in rows if r[3] == first[3]}))


def census():
    d = ipo_list()
    d["cik"] = match_cik(d)
    sp = SPY_BP()
    recs = []
    for _, r in d.iterrows():
        sym = r.proposedTickerSymbol
        why = None
        sic = state = None
        if pd.isna(r.cik):
            why = "no_cik"
        else:
            s = json.loads((C / "subs" / f"{int(r.cik)}.json").read_text())
            sic, state = s.get("sic"), s.get("state")
            if sic in ("6770", "6726", "6189"):
                why = "spac_or_fund"
            elif state not in US_STATES:
                why = "non_us"
        if why is None and re.search(r"acquisition|merger", r.companyName, re.IGNORECASE):
            why = "spac_name"
        close = sh = None
        if why is None:
            close, _day = first_day_close(sym, r.date)
            sh = cover_shares(int(r.cik), r.date)
            if close is not None and not 0.1 <= close / r.price <= 10:
                why = (
                    "split_adjusted_close"  # Alpaca closes are split-adjusted, cover shares are not
                )
            elif close is None:
                why = "no_first_close"
            elif not sh:
                why = "no_shares"
        mc = close * sh if why is None else None
        flt = r.shares_off / sh if why is None else None
        bp = BP_REF * sp(r.date)
        recs.append(
            {
                "date": r.date,
                "sym": sym,
                "name": r.companyName,
                "exch": r.proposedExchange,
                "cik": r.cik,
                "sic": sic,
                "state": state,
                "why": why,
                "close1": close,
                "shares": sh,
                "mcap": mc,
                "float_proxy": flt,
                "bp": bp,
                "pred": (why is None and mc >= bp and flt >= 0.10),
            }
        )
    out = pd.DataFrame(recs)
    out["year"] = out.date.dt.year
    out.to_csv(C / "census.csv", index=False)
    u = pd.concat([pd.read_csv(p) for p in UNIVERSES]).drop_duplicates(["month", "symbol"])
    keys = set(zip(u.month, u.symbol.str.upper()))
    ok = out[out.why.isna()].copy()
    # tradable top-1000 "by T+4": member in the month of the IPO or the next month (first-day date + 4 trading days <= 6 cal days)
    ok["m0"] = ok.date.dt.strftime("%Y-%m")
    ok["m1"] = (ok.date + pd.Timedelta(days=7)).dt.strftime("%Y-%m")
    ok["in_u"] = [
        (a, s.upper()) in keys or (b, s.upper()) in keys for a, b, s in zip(ok.m0, ok.m1, ok.sym)
    ]
    ok.to_csv(C / "census_eligible.csv", index=False)
    tab = (
        pd.DataFrame(
            {
                "priced": out.groupby("year").size(),
                "operating_us": out[out.why.isna() | out.why.isin(["no_first_close", "no_shares"])]
                .groupby("year")
                .size(),
                "no_cik": out[out.why == "no_cik"].groupby("year").size(),
                "no_close_or_shares": out[out.why.isin(["no_first_close", "no_shares"])]
                .groupby("year")
                .size(),
                "pred_size_float": ok.groupby("year").pred.sum(),
                "pred_size_only": ok[ok.mcap >= ok.bp].groupby("year").size(),
                "pred_in_top1000": ok[ok.pred & ok.in_u].groupby("year").size(),
                "size_only_at_1.5bn": ok[ok.mcap >= 1.5e9].groupby("year").size(),
                "size_only_at_3bn": ok[ok.mcap >= 3e9].groupby("year").size(),
            }
        )
        .fillna(0)
        .astype(int)
    )
    tab.to_csv(C / "census_by_year.csv")
    first = u.groupby(u.symbol.str.upper()).month.min()
    pr = ok[ok.pred].copy()
    pr["first_m"] = pr.sym.str.upper().map(first)
    pr["lag"] = [
        (pd.Period(f, "M") - pd.Period(m, "M")).n if isinstance(f, str) and f >= m else None
        for f, m in zip(pr.first_m, pr.m0)
    ]
    print("predicted events:", len(pr), "| ever in top-1000 after IPO:", int(pr.lag.notna().sum()))
    print("months from IPO month to first universe month (0 = same month):")
    print(pr.lag.value_counts(dropna=False).sort_index().to_string())
    print("ever-in-universe by year:", pr[pr.lag.notna()].groupby("year").size().to_dict())
    print(tab.to_string())
    print(out.why.value_counts(dropna=False).to_string())
    print("pred total", int(ok.pred.sum()), "in top1000", int((ok.pred & ok.in_u).sum()))


def SPY_BP():
    """Breakpoint scaling: SPY close (market level only, not an IPO price) relative to 2024-12-31."""
    x = pd.read_csv(D1 / "SPY.csv", usecols=["ts", "close"])
    s = pd.Series(x.close.values, index=pd.to_datetime(x.ts.str[:10]))
    ref = s[:"2024-12-31"].iloc[-1]
    return lambda dt: float(s[:dt].iloc[-1] / ref)


if __name__ == "__main__":
    {"download": download, "census": census}[sys.argv[1]]()
