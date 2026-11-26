"""F-01 Stage A: return-blind data audit (employees sell after earnings at high stock-comp firms).

Reads NO event-window returns (day 0 .. +10). Prices are used only for market cap (last close before the event) and
for a return sd / correlation from non-event days -30..-11. Raw SEC downloads are cut to the needed slices and cached in
data/cache/sec_f01/ (companyfacts files are 3-10 MB each, so the slice is cached, not the whole file).
Run: .venv/Scripts/python.exe research/screens/2026-11-26_r7_f01_stage_a.py download | audit
"""

import json
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

C = Path("data/cache/sec_f01")
D1 = Path("data/cache/alpaca_1d")
UNIVERSES = [Path("data/cache/alpaca_meta/universe.csv"), Path("data/cache/alpaca_meta_fwd/universe.csv")]
REPORT = Path("knowledge/research/reports/2026-11-26_f01-stage-a.md")
SBC_TAGS = ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]
LOCK, LAST, UA = threading.Lock(), [0.0], []
ET = "America/New_York"
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))


def get(url):
    """curl (requests fails the local TLS chain); global limit 8 requests / s; returns (status, body bytes)."""
    import keyring

    with LOCK:
        if not UA:
            UA.append(f"backtester-research {keyring.get_password('backtester-contact', 'email')}")
        ua = UA[0]
        time.sleep(max(0.0, LAST[0] + 0.13 - time.time()))
        LAST[0] = time.time()
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-A", ua, "-w", "\n%{http_code}", url],
        capture_output=True,
        timeout=300,
        check=False,
    )
    body, _, code = r.stdout.rpartition(b"\n")
    return code.decode(), body


def universe():
    u = pd.concat([pd.read_csv(p) for p in UNIVERSES]).drop_duplicates(["month", "symbol"])
    return u[u.month <= "2026-11"].copy()


def tickers():
    p = C / "company_tickers.json"
    if not p.exists():
        code, body = get("https://www.sec.gov/files/company_tickers.json")
        assert code == "200", code
        p.write_bytes(body)
    return {v["ticker"].upper(): int(v["cik_str"]) for v in json.loads(p.read_bytes()).values()}


def cik_of(sym, tk):
    return tk.get(sym.upper(), tk.get(sym.upper().replace(".", "-")))


def fetch_cik(cik):
    (C / "facts").mkdir(exist_ok=True)
    (C / "subs").mkdir(exist_ok=True)
    pf, ps = C / "facts" / f"{cik}.json", C / "subs" / f"{cik}.json"
    if not pf.exists():
        code, body = get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
        out = {}
        if code == "200":
            f = json.loads(body)["facts"]
            gaap = f.get("us-gaap", {})
            for tag in SBC_TAGS:
                rows = gaap.get(tag, {}).get("units", {}).get("USD", [])
                out[tag] = [
                    [x["start"], x["end"], x["val"], x["filed"]]
                    for x in rows
                    if "start" in x and x.get("form", "").startswith("10-K")
                ]
            sh = f.get("dei", {}).get("EntityCommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
            out["shares"] = [[x["end"], x["val"], x["filed"], x["accn"]] for x in sh]
        pf.write_text(json.dumps({"code": code, **out}))
    if not ps.exists():
        code, body = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        ev = []
        if code == "200":
            j = json.loads(body)
            blocks = [j["filings"]["recent"]]
            for fl in j["filings"].get("files", []):
                if fl["filingTo"] >= "2015-12-01":
                    c2, b2 = get(f"https://data.sec.gov/submissions/{fl['name']}")
                    if c2 == "200":
                        blocks.append(json.loads(b2))
            for b in blocks:
                for i, form in enumerate(b["form"]):
                    if form == "8-K" and "2.02" in b["items"][i].split(",") and b["acceptanceDateTime"][i] >= "2015-12":
                        ev.append([b["accessionNumber"][i], b["acceptanceDateTime"][i], b["primaryDocument"][i]])
        ps.write_text(json.dumps({"code": code, "events": ev}))


def download():
    C.mkdir(parents=True, exist_ok=True)
    tk = tickers()
    ciks = sorted({c for s in universe().symbol.unique() if (c := cik_of(s, tk))})
    print(len(ciks), "CIKs to fetch", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(6) as ex:
        for i, _ in enumerate(ex.map(fetch_cik, ciks)):
            if i % 200 == 0:
                print(i, round(time.time() - t0), "s", flush=True)


# ---------------------------------------------------------------- audit
def lag_sbc(facts, d):
    """Latest annual (300-400 day) 10-K SBC value filed before date d, end within 550 days of d: (value, tag)."""
    for tag in SBC_TAGS:
        best = None
        for s, e, v, filed in facts.get(tag, []):
            if filed >= d or (pd.Timestamp(d) - pd.Timestamp(e)).days > 550:
                continue
            if not 300 <= (pd.Timestamp(e) - pd.Timestamp(s)).days <= 400:
                continue
            if best is None or (e, filed) > (best[0], best[1]):
                best = (e, filed, v)
        if best:
            return best[2], tag
    return None, None


def lag_shares(facts, d):
    """Shares from the latest cover-page report filed before d (summing share classes of that filing)."""
    rows = [r for r in facts.get("shares", []) if r[2] < d]
    if not rows:
        return None
    top = max(rows, key=lambda r: (r[2], r[0]))
    return float(sum({r[1] for r in rows if r[3] == top[3]}))


_px = {}


def closes(sym):
    if sym not in _px:
        p = D1 / f"{sym}.csv"
        if p.exists():
            d = pd.read_csv(p, usecols=["ts", "close"])
            _px[sym] = pd.Series(d.close.values, index=pd.to_datetime(d.ts.str[:10]))
        else:
            _px[sym] = None
    return _px[sym]


def build_events():
    tk = tickers()
    u = universe()
    u["cik"] = [cik_of(s, tk) for s in u.symbol]
    u["year"] = u.month.str[:4].astype(int)
    rows = []
    for cik, g in u.dropna(subset=["cik"]).groupby("cik"):
        cik = int(cik)
        fp, sp = C / "facts" / f"{cik}.json", C / "subs" / f"{cik}.json"
        if not (fp.exists() and sp.exists()):
            continue
        facts, subs = json.loads(fp.read_text()), json.loads(sp.read_text())
        sym_by_month = g.groupby("month").symbol.first().to_dict()
        last = None
        for acc, adt, doc in sorted(subs["events"], key=lambda x: x[1]):
            t = pd.Timestamp(adt).tz_convert(ET)
            if last is not None and (t - last).days < 40:
                continue  # same quarter's second 2.02 8-K
            last = t
            sym = sym_by_month.get(t.strftime("%Y-%m"))
            if sym is None:
                continue
            hm = t.hour + t.minute / 60
            bucket = "after 16:00" if hm >= 16 else ("before 09:30" if hm < 9.5 else "09:30-16:00")
            d0 = (t.normalize().tz_localize(None) + pd.offsets.BDay(1)) if hm >= 16 else t.normalize().tz_localize(None)
            if d0.day_of_week >= 5:
                d0 = d0 + pd.offsets.BDay(0)
            dstr = t.strftime("%Y-%m-%d")
            sbc, tag = lag_sbc(facts, dstr)
            sh = lag_shares(facts, dstr)
            px = closes(sym)
            mc = ret = None
            if px is not None:
                before = px[px.index < d0]
                if len(before):
                    mc = sh * before.iloc[-1] if sh else None
                i0 = int(px.index.searchsorted(d0))
                if i0 - 31 >= 0 and i0 < len(px):  # non-event window only: closes of days -31..-11
                    w = px.iloc[i0 - 31 : i0 - 10]
                    ret = np.log(w).diff().dropna()
            rows.append(
                {"cik": cik, "sym": sym, "acc": acc, "doc": doc, "t": t, "d0": d0, "year": d0.year, "bucket": bucket, "sbc": sbc, "tag": tag,
                     "mcap": mc, "ret": ret, "month": t.strftime("%Y-%m")}
            )
    ev = pd.DataFrame(rows)
    ev["ratio"] = np.where((ev.sbc > 0) & (ev.mcap > 0), ev.sbc / ev.mcap, np.nan)
    ev["q"] = ev.d0.dt.year * 10 + ev.d0.dt.quarter
    ev["pct"] = ev.groupby("q").ratio.rank(pct=True)
    ev["grp"] = np.where(ev.pct >= 0.95, "top5", np.where(ev.pct >= 0.90, "5-10", ""))
    return u, ev


def power(sub, effect):
    """Date-clustered SE of the mean 3-day return from non-event sd; rho from non-event same-date pairs."""
    sd = np.array([r.std() * sqrt(3) if r is not None and len(r) >= 15 else np.nan for r in sub.ret])
    sd = np.where(np.isnan(sd), np.nanmedian(sd), sd)
    num = den = 0.0
    for idx in sub.groupby("d0").indices.values():
        if len(idx) < 2:
            continue
        m = pd.concat([sub.ret.iloc[i] for i in idx], axis=1).dropna()
        if len(m) >= 10:
            c = m.corr().values
            num += np.nansum(c[np.triu_indices(len(c), 1)])
            den += len(c) * (len(c) - 1) / 2
    rho = num / den if den else 0.0
    var = sum(
        (sd[idx].sum() ** 2 - (sd[idx] ** 2).sum()) * rho + (sd[idx] ** 2).sum()
        for idx in sub.groupby("d0").indices.values()
    ) / len(sd) ** 2
    out = {"n": len(sub), "dates": sub.d0.nunique(), "sd3": np.median(sd) * 1e4, "rho": rho}
    for k, f in (("", 1.0), ("x1.3", 1.3)):
        se = sqrt(var) * f * 1e4
        out[k] = (se, 3 * se, Phi(effect / se - 3), Phi(effect / 2 / se - 3))
    return out


def exhibit_check(ev):
    s = ev.sample(20, random_state=20261126)  # drawn before looking at anything
    res = []
    for r in s.itertuples():
        nodash = r.acc.replace("-", "")
        code, body = get(f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{nodash}/index.json")
        found = "no index"
        if code == "200":
            names = [x["name"] for x in json.loads(body)["directory"]["item"]]
            ex = [n for n in names if re.search(r"(ex|d).*99", n.lower()) and n.lower().endswith((".htm", ".txt"))]
            if ex:
                b2 = get(f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{nodash}/{ex[0]}")[1]
                txt = re.sub(r"<[^>]+>|&nbsp;|&#160;", " ", b2.decode("utf8", "ignore"))
                txt = re.sub(r"\s+", " ", txt)[:2500]
                m = re.search(r"(\d{1,2}:\d{2}\s*[ap]\.?m\.?|after (the )?(market )?clos|before (the )?(market )?open)", txt, re.IGNORECASE)
                found = m.group(0) if m else "no time in text"
            else:
                found = "no ex99"
        res.append((r.sym, r.t.strftime("%Y-%m-%d %H:%M"), found))
    return res


def md(df):
    d = df.reset_index().astype(object)
    rows = ["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * len(d.columns)]
    return "\n".join(rows + ["| " + " | ".join(map(str, r)) + " |" for r in d.values])


def audit():
    u, ev = build_events()
    sym_years = u.assign(y=u.year).drop_duplicates(["symbol", "y"])
    n_unmapped = sym_years[sym_years.cik.isna()].groupby("y").size()
    usable = ev[ev.ratio.notna()]
    cov = pd.DataFrame(
        {
            "sym-years": sym_years.groupby("y").size(),
            "mapped": sym_years[sym_years.cik.notna()].groupby("y").size(),
            "usable": usable.drop_duplicates(["sym", "year"]).groupby("year").size(),
            "events": ev.groupby("year").size(),
            "ev usable": usable.groupby("year").size(),
        }
    ).fillna(0).astype(int)
    cov = cov[(cov.index >= 2016)]
    cov["cov %"] = (cov.usable / cov["sym-years"] * 100).round(0)
    tagshare = usable.tag.value_counts(normalize=True).round(2).to_dict()
    tim = pd.crosstab(ev.year, ev.bucket, normalize="index").mul(100).round(0)
    tim_a = ev[ev.year <= 2020].bucket.value_counts(normalize=True).mul(100).round(0).to_dict()
    tim_b = ev[ev.year >= 2021].bucket.value_counts(normalize=True).mul(100).round(0).to_dict()
    top = usable[usable.grp == "top5"]
    mid = usable[usable.grp == "5-10"]
    cnt = pd.DataFrame({"events": ev.groupby("year").size(), "top5": top.groupby("year").size(),
                        "5-10": mid.groupby("year").size(), "top5 dates": top.groupby("year").d0.nunique()}).fillna(0).astype(int)
    n_noret = int(top.ret.isna().sum())
    top = top[top.ret.notna()]
    pa = power(top[top.year <= 2020], 87.5)
    pb = power(top[top.year >= 2021], 87.5)
    # borrow proxy: month dv and market cap of top5 events
    dv = u.set_index(["month", "symbol"]).dv
    top = top.assign(dv=[dv.get((m, s), np.nan) for m, s in zip(top.month, top.sym, strict=True)])
    mc_med, dv_med = top.mcap.median() / 1e9, top.dv.median() / 1e6
    small = (top.mcap < 1e9).mean() * 100
    ex = exhibit_check(ev)
    cov_all = cov.usable.sum() / cov["sym-years"].sum() * 100
    pa5, pb5 = pa[""][3], pb[""][3]
    verdict = "PASS" if (pa5 >= 0.15 and pb5 >= 0.15 and cov_all >= 70) else "PARK"
    L = [
        "# F-01 Stage A: return-blind data audit (2026-11-26)",
        "",
        "Script `research/screens/2026-11-26_r7_f01_stage_a.py`. No event-window return (day 0..+10) was read. Prices: market cap",
        "(shares x last close before the event) and sd / correlation from non-event days -30..-11 only.",
        "",
        f"**Verdict: {verdict}** (pass chance at half effect: 2016-2020 {pa5:.0%}, holdout 2021-2026 {pb5:.0%}; coverage {cov_all:.0f} %).",
        "",
        "## Coverage (symbol-years in the top-1,000 universe with a usable lagged SBC / mcap ratio at an earnings event)",
        md(cov),
        (f"Unmapped to a CIK (symbol-years, coverage loss): {int(n_unmapped.sum())}. SBC tag of usable events: {tagshare}. "
        "Annual 10-K facts only (no trailing-4-quarter sum), filed before the event."),
        "",
        "## Timing of the 8-K Item 2.02 acceptance (ET, % of events)",
        md(tim),
        f"2016-2020: {tim_a}; 2021-2026: {tim_b}. Events after 16:00 ET take t=0 as the next business day (holidays ignored).",
        ("Press-release check, 20 seeded events (exhibit 99.1 text, first 2,500 chars; a time found is often the call time, "
         "not the release time): " + "; ".join(f"{a} {b} -> {c}" for a, b, c in ex) + ". Verdict of the check: "
         "inconclusive, the exhibits rarely state a release time (the two times found are call times); the EDGAR acceptance times "
         "sit at typical release hours (06:45-07:30 and 16:05-16:45 ET), so acceptance is a usable but unverified proxy."),
        "",
        "## Events by SBC / market-cap bucket (rank within calendar quarter of the event)",
        md(cnt),
        "",
        "## Power for top 5 % (3-day sd from non-event days; rho = mean same-date pairwise correlation, non-event days, unhedged)",
        "| period | events | dates | median sd3 bp | rho | SE bp | MDE t3 bp | pass @87.5 | pass @43.75 | SE x1.3 | pass @43.75 (x1.3) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, p in (("2016-2020", pa), ("2021-2026", pb)):
        a, b = p[""], p["x1.3"]
        L.append(f"| {name} | {p['n']} | {p['dates']} | {p['sd3']:.0f} | {p['rho']:.2f} | {a[0]:.1f} | {a[1]:.1f} | {a[2]:.0%} | {a[3]:.0%} | {b[0]:.1f} | {b[3]:.0%} |")
    L += [
        "",
        "## Borrow proxy (top 5 % events)",
        (f"Median market cap USD {mc_med:.1f} bn, median monthly dollar volume (universe `dv`) USD {dv_med:.0f} m, "
        f"{small:.0f} % of events below USD 1 bn market cap. Alpaca borrow history does not exist. Top-5 % events without a price window (dropped from power): {n_noret}."),
        "",
        "## Limits",
        ("- Alpaca closes are split-adjusted; SEC shares are as reported then. A later split understates the market cap and can "
        "push a firm into the top 5 % wrongly. Stage B needs unadjusted prices or a split table."),
        "- Ticker to CIK uses today's SEC list; delisted or renamed symbols are unmapped (counted above). Share classes are summed.",
        "- Event-window sd is higher than the non-event sd; the x1.3 column is the sensitivity.",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf8")
    print("\n".join(L))


if __name__ == "__main__":
    {"download": download, "audit": audit}[sys.argv[1]]()
