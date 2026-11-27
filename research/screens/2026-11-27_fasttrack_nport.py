"""N-PORT check of the fast-track census: does Vanguard Total Stock Market Index (CRSP US Total Market) hold each IPO soon after listing?

Return-blind: only identifiers (name, ticker/CUSIP/ISIN), share balance and report date are read from the holdings;
value / price columns are never parsed. Raw N-PORT XML is reduced to (name, title, cusip, isin, balance) and cached.
Run: .venv/Scripts/python.exe research/screens/2026-11-27_fasttrack_nport.py list | download | check
"""

import json
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd

C = Path("data/cache/fasttrack/nport")
CEN = Path("data/cache/fasttrack/census.csv")
LOCK, LAST, UA = threading.Lock(), [0.0], []
CIK = 36405  # Vanguard Index Funds (registrant); series is picked from the XML (seriesId / name)
SERIES = "S000002848"  # Vanguard Total Stock Market Index Fund


def get(url, rng=None):
    """curl (requests fails the local TLS chain); one downloader, at most 8 requests / s; returns (status, body)."""
    import keyring

    with LOCK:
        if not UA:
            UA.append(f"backtester-research {keyring.get_password('backtester-contact', 'email')}")
        ua = UA[0]
        time.sleep(max(0.0, LAST[0] + 0.13 - time.time()))
        LAST[0] = time.time()
    r = subprocess.run(
        [
            "curl",
            "-s",
            "--compressed",
            "-A",
            ua,
            *(["-r", rng] if rng else []),
            "-w",
            "\n%{http_code}",
            url,
        ],
        capture_output=True,
        timeout=300,
        check=False,
    )
    body, _, code = r.stdout.rpartition(b"\n")
    return code.decode(), body


def list_filings():
    """All NPORT-P filings of the registrant -> C/filings.csv."""
    code, body = get(f"https://data.sec.gov/submissions/CIK{CIK:010d}.json")
    assert code == "200", code
    j = json.loads(body)
    rows = []
    blocks = [j["filings"]["recent"]]
    for f in j["filings"].get("files", []):
        c, b = get("https://data.sec.gov/submissions/" + f["name"])
        assert c == "200", c
        blocks.append(json.loads(b))
    for b in blocks:
        rows += [dict(zip(b, v)) for v in zip(*b.values())]
    df = pd.DataFrame(rows)
    df = df[df.form.str.startswith("NPORT-P")][
        ["accessionNumber", "filingDate", "reportDate", "form"]
    ]
    df.to_csv(C / "filings.csv", index=False)
    print(len(df), "NPORT-P filings", df.reportDate.min(), df.reportDate.max())


def tag(x, t):
    m = re.search(rf"<{t}>([^<]*)</{t}>", x)
    return m.group(1) if m else ""


def identify():
    """Series of every filing from the first 3 KB of primary_doc.xml (header only) -> C/series.csv."""
    f = pd.read_csv(C / "filings.csv")
    out = []
    for a in f.accessionNumber:
        c, b = get(
            f"https://www.sec.gov/Archives/edgar/data/{CIK}/{a.replace('-', '')}/primary_doc.xml",
            "0-3500",
        )
        x = b.decode("utf8", "ignore")
        out.append((a, c, tag(x, "seriesId"), tag(x, "seriesName"), tag(x, "repPdDate")))
    df = pd.DataFrame(
        out, columns=["accessionNumber", "http", "seriesId", "seriesName", "repPdDate"]
    )
    df.to_csv(C / "series.csv", index=False)
    print(df.http.value_counts().to_dict(), df.seriesName.nunique(), "series")


def download():
    """Holdings of the Total Stock Market series, reduced to name / title / cusip / isin / balance / units / country.

    Value, price and percentage tags are never extracted (return-blind). Raw XML is not stored.
    """
    s = pd.read_csv(C / "series.csv")
    s = s[s.seriesId == SERIES].sort_values("repPdDate")
    for a, d in zip(s.accessionNumber, s.repPdDate):
        p = C / f"tsm_{d}.csv"
        if p.exists():
            continue
        code, b = get(
            f"https://www.sec.gov/Archives/edgar/data/{CIK}/{a.replace('-', '')}/primary_doc.xml"
        )
        assert code == "200", (a, code)
        x = b.decode("utf8", "ignore")
        rows = []
        for blk in re.findall(r"<invstOrSec>(.*?)</invstOrSec>", x, flags=re.DOTALL):
            rows.append(
                {
                    "name": tag(blk, "name"),
                    "title": tag(blk, "title"),
                    "cusip": tag(blk, "cusip"),
                    "isin": tag(blk, "isin"),
                    "balance": tag(blk, "balance"),
                    "units": tag(blk, "units"),
                    "country": tag(blk, "invCountry"),
                    "assetCat": tag(blk, "assetCat"),
                }
            )
        pd.DataFrame(rows).to_csv(p, index=False)
        print(d, len(rows))


def sample():
    """Census rows with a usable close and shares (why empty), 2019-03 on."""
    d = pd.read_csv(CEN)
    d = d[d.why.isna() & (d.date >= "2019-03-01")].copy()
    d["cik"] = d.cik.astype(int)
    return d


def names():
    """Former and current SEC names per CIK -> C/names/<cik>.json (names only)."""
    (C / "names").mkdir(exist_ok=True)
    for cik in sample().cik.unique():
        p = C / "names" / f"{cik}.json"
        if p.exists():
            continue
        code, b = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
        if code != "200":
            p.write_text(json.dumps({"code": code, "names": []}))
            continue
        j = json.loads(b)
        nm = [j.get("name", "")] + [f["name"] for f in j.get("formerNames", [])]
        p.write_text(json.dumps({"code": code, "names": nm}))
    print(len(list((C / "names").glob("*.json"))), "cik name files")


SUFFIX = r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|holdings?|holding|group|class [a-c]|common stock|the|lp|llc|n v|s a|de)\b"


def norm(x):
    x = re.sub(r"[^a-z0-9 ]", " ", str(x).lower().replace("&", " and "))
    x = re.sub(SUFFIX, " ", x)
    return re.sub(r"\s+", " ", x).strip()


def third_friday(y, m):
    d = pd.Timestamp(y, m, 1)
    return d + pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)


def check():
    snaps = {}
    for p in sorted(C.glob("tsm_*.csv")):
        h = pd.read_csv(p, dtype=str)
        h = h[h.assetCat == "EC"]
        snaps[pd.Timestamp(p.stem[4:])] = set(h.name.map(norm)) | set(h.title.map(norm))
    qe = sorted(snaps)
    d = sample()
    rows = []
    for r in d.itertuples():
        nm = {norm(r.name)}
        f = C / "names" / f"{int(r.cik)}.json"
        if f.exists():
            nm |= {norm(x) for x in json.loads(f.read_text())["names"]}
        nm.discard("")
        ipo = pd.Timestamp(r.date)
        held, method = None, ""
        for q in qe:
            if q < ipo:
                continue
            hit = nm & snaps[q]
            if hit:
                held, method = q, "name" if norm(r.name) in hit else "former_name"
                break
        nxt = next((q for q in qe if q >= ipo), None)
        # diagnostic: listed after the quarterly reconstitution (3rd Friday of the quarter-end month) and T+4 <= quarter end
        diag, lag = False, None
        if nxt is not None:
            lag = (
                ipo - third_friday(nxt.year, nxt.month)
            ).days  # days after the quarterly reconstitution
            diag = lag > 0 and ipo + pd.offsets.BDay(4) <= nxt
        rows.append(
            {
                "date": r.date,
                "sym": r.sym,
                "name": r.name,
                "year": r.year,
                "pred": r.pred,
                "next_qe": nxt,
                "first_held": held,
                "match": method,
                "held_at_next_qe": held is not None and held == nxt,
                "diag": diag,
                "lag": lag,
                "mcap_m": round(r.mcap / 1e6),
            }
        )
    o = pd.DataFrame(rows)
    o.to_csv(C / "nport_check.csv", index=False)
    # coverage of snapshots: last IPO date that has a next quarter-end
    print("rows", len(o), "pred", int(o.pred.sum()), "diag", int(o.diag.sum()))
    print(
        "ever held (any snapshot):",
        o.groupby("pred").apply(lambda g: g.first_held.notna().mean()).round(3).to_dict(),
    )
    print("held at next QE:", o.groupby("pred").held_at_next_qe.mean().round(3).to_dict())
    dg = o[o.diag]
    print(pd.crosstab(dg.pred, dg.held_at_next_qe, margins=True))
    print(pd.crosstab([dg.year], [dg.pred, dg.held_at_next_qe]))
    print("non-diag by year x pred x held_next_qe")
    nd = o[~o.diag & o.next_qe.notna()]
    print(pd.crosstab(nd.pred, nd.held_at_next_qe, margins=True))
    print(
        dg[["date", "sym", "name", "pred", "mcap_m", "next_qe", "first_held", "match"]].to_string()
    )
    for lo in (-7, 0, 7):  # sensitivity: assumed reconstitution date moved by lo days
        x = o[
            o.next_qe.notna()
            & (o.lag > lo)
            & (pd.to_datetime(o.date) + pd.offsets.BDay(4) <= o.next_qe)
        ]
        t = pd.crosstab(x.pred, x.held_at_next_qe)
        print("window after recon +", lo, "days: n", len(x), t.to_dict())


if __name__ == "__main__":
    {
        "list": list_filings,
        "identify": identify,
        "download": download,
        "names": names,
        "check": check,
    }[sys.argv[1]]()
