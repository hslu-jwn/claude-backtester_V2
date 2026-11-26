"""Rule 201 (SEC short-sale circuit breaker) trigger census, RETURN-BLIND (R8, 2026-11-26).

Subcommands:  download | census
Archives (anonymous HTTP, see knowledge/research/reports/2026-11-26_r8-feasibility.md section 1):
  Nasdaq daily txt, NYSE group daily xls, Cboe yearly csv  ->  data/cache/rule201/
The census never reads a price on or after a trigger day. Daily closes are used only for the
non-trigger-day return sd and correlation (days >= 5 trading days away from any trigger of that name).
Run: .venv/Scripts/python.exe research/screens/2026-11-26_rule201_census.py download|census
"""
import csv
import datetime as dt
import re
import struct
import subprocess
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache" / "rule201"
START, END = dt.date(2016, 1, 1), dt.date(2026, 10, 31)
NQ = "https://www.nasdaqtrader.com/dynamic/symdir/shorthalts/shorthalts{d}.txt"
NYSE = ("https://ftp.nyse.com/NYSEGroupSSRCircuitBreakers/NYSEGroupSSRCircuitBreakers_{y}/"
        "NYSEGroupSSRCircuitBreakers_{ym}/NYSEGroupSSRCircuitBreakers{d}.xls")
CBOE = ("https://www-api.cboe.com/us/equities/market_statistics/short_sale_circuit_breakers/downloads/"
        "BatsCircuitBreakers{y}.csv")
MISSING = CACHE / "missing.txt"  # "kind key status"


# ---------------------------------------------------------------- minimal pure-python .xls (BIFF8) reader
def _ole_stream(buf: bytes, want=("Workbook", "Book")) -> bytes:
    ssz = 1 << struct.unpack_from("<H", buf, 0x1E)[0]
    msz = 1 << struct.unpack_from("<H", buf, 0x20)[0]
    dir0, cutoff, mf0 = struct.unpack_from("<I", buf, 0x30)[0], struct.unpack_from("<I", buf, 0x38)[0], struct.unpack_from("<I", buf, 0x3C)[0]
    difat0, ndifat = struct.unpack_from("<II", buf, 0x44)
    sect = lambda i: buf[(i + 1) * ssz:(i + 2) * ssz]
    difat = [x for x in struct.unpack_from("<109I", buf, 0x4C) if x < 0xFFFFFFFA]
    s = difat0
    for _ in range(ndifat):
        v = struct.unpack(f"<{ssz // 4}I", sect(s))
        difat += [x for x in v[:-1] if x < 0xFFFFFFFA]
        s = v[-1]
    fat = [x for f in difat for x in struct.unpack(f"<{ssz // 4}I", sect(f))]

    def chain(start, table):
        out = []
        while start < 0xFFFFFFFA:
            out.append(start)
            start = table[start]
        return out

    directory = b"".join(sect(i) for i in chain(dir0, fat))
    ents = []
    for k in range(len(directory) // 128):
        e = directory[k * 128:(k + 1) * 128]
        nl = struct.unpack_from("<H", e, 0x40)[0]
        ents.append((e[:max(nl - 2, 0)].decode("utf-16le"), e[0x42], struct.unpack_from("<I", e, 0x74)[0], struct.unpack_from("<I", e, 0x78)[0]))
    root = next(e for e in ents if e[1] == 5)
    ent = next(e for e in ents if e[0] in want and e[1] == 2)
    if ent[3] >= cutoff:
        return b"".join(sect(i) for i in chain(ent[2], fat))[:ent[3]]
    mini = b"".join(sect(i) for i in chain(root[2], fat))
    minifat = [x for i in chain(mf0, fat) for x in struct.unpack(f"<{ssz // 4}I", sect(i))]
    return b"".join(mini[i * msz:(i + 1) * msz] for i in chain(ent[2], minifat))[:ent[3]]


def _rk(v: int) -> float:
    x = float(v >> 2 if not v & 0x80000000 else (v >> 2) - (1 << 30)) if v & 2 else struct.unpack("<d", struct.pack("<Q", (v & 0xFFFFFFFC) << 32))[0]
    return x / 100 if v & 1 else x


def read_xls(path: Path) -> list[list]:
    """First worksheet as a list of rows (str / float / None)."""
    data = _ole_stream(path.read_bytes())
    recs, p = [], 0
    while p + 4 <= len(data):
        rid, ln = struct.unpack_from("<HH", data, p)
        recs.append((rid, data[p + 4:p + 4 + ln]))
        p += 4 + ln
    sst: list[str] = []
    for i, (rid, body) in enumerate(recs):
        if rid != 0xFC:
            continue
        cat, bounds, j = body, [], i + 1
        while j < len(recs) and recs[j][0] == 0x3C:
            bounds.append(len(cat))
            cat += recs[j][1]
            j += 1
        pos, bi = 8, 0
        for _ in range(struct.unpack_from("<I", cat, 4)[0]):
            if pos + 3 > len(cat):
                break
            cch, fl = struct.unpack_from("<HB", cat, pos)
            pos += 3
            crun = extl = 0
            if fl & 8:
                crun = struct.unpack_from("<H", cat, pos)[0]
                pos += 2
            if fl & 4:
                extl = struct.unpack_from("<I", cat, pos)[0]
                pos += 4
            chars, wide, left = [], fl & 1, cch
            while left:
                while bi < len(bounds) and bounds[bi] < pos:
                    bi += 1
                avail = (bounds[bi] - pos) if bi < len(bounds) else len(cat) - pos
                if avail == 0 and bi < len(bounds):  # continue record starts here: flag byte first
                    wide = cat[pos] & 1
                    pos += 1
                    bi += 1
                    continue
                n = min(left, avail // (2 if wide else 1))
                chars.append(cat[pos:pos + n * (2 if wide else 1)].decode("utf-16le" if wide else "latin-1"))
                pos += n * (2 if wide else 1)
                left -= n
            pos += crun * 4 + extl
            sst.append("".join(chars))
    rows: dict[int, dict[int, object]] = defaultdict(dict)
    bof = 0
    for rid, b in recs:
        if rid == 0x809:
            bof += 1
        elif rid == 0x0A and bof >= 2:
            break
        elif bof < 2:
            continue
        elif rid == 0xFD:
            r, c, _, i = struct.unpack_from("<HHHI", b)
            rows[r][c] = sst[i]
        elif rid == 0x203:
            r, c, _ = struct.unpack_from("<HHH", b)
            rows[r][c] = struct.unpack_from("<d", b, 6)[0]
        elif rid == 0x27E:
            r, c, _, v = struct.unpack_from("<HHHI", b)
            rows[r][c] = _rk(v)
        elif rid == 0xBD:
            r, c0 = struct.unpack_from("<HH", b)
            for k in range((len(b) - 6) // 6):
                rows[r][c0 + k] = _rk(struct.unpack_from("<I", b, 6 + 6 * k + 2)[0])
        elif rid == 0x204:
            r, c, _, ln, fl = struct.unpack_from("<HHHHB", b)
            rows[r][c] = b[9:9 + ln * (2 if fl & 1 else 1)].decode("utf-16le" if fl & 1 else "latin-1")
    return [[rows[r].get(c) for c in range(max(rows[r]) + 1)] for r in sorted(rows)]


# ---------------------------------------------------------------- download
_lock, _last, _gap = threading.Lock(), [0.0], [0.26]  # _gap: seconds between requests, doubles after a bot-protection page


def _get(url: str, path: Path) -> int:
    """HTTP status via curl (the venv's Python lacks the issuers' CA chain; no TLS checks are switched off)."""
    with _lock:  # global limiter: at most 4 requests a second
        wait = _last[0] + _gap[0] - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
    tmp = path.with_suffix(path.suffix + ".part")
    r = subprocess.run(["curl", "-s", "--max-time", "40", "-o", str(tmp), "-w", "%{http_code}", url],
                       capture_output=True, text=True, check=False)
    code = int(r.stdout.strip() or 0)
    if code == 200 and tmp.exists() and tmp.stat().st_size > 0 and tmp.read_bytes()[:5].lower() == b"<html":
        code = 999  # bot-protection page instead of data: slow down and retry later, never bypass
        _gap[0] = min(_gap[0] * 2, 12)
        time.sleep(60)
    if code == 200 and tmp.exists() and tmp.stat().st_size > 0:
        tmp.replace(path)
    else:
        tmp.unlink(missing_ok=True)
    return code


def _fetch(task):
    kind, key, url, path = task
    for attempt in range(5):
        code = _get(url, path)
        if code == 200:
            return kind, key, "ok"
        if code in (301, 302, 403, 404):
            return kind, key, str(code)
        time.sleep(4 * (attempt + 1))  # 5xx / timeouts: back off
    return kind, key, "error"  # not recorded as missing: retried on the next run


def download() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    done = set()
    if MISSING.exists():
        done = {tuple(x.split()[:2]) for x in MISSING.read_text().splitlines() if x.strip()}
    tasks, d = [], START
    while d <= END:
        if d.weekday() < 5:
            s = d.strftime("%Y%m%d")
            tasks.append(("nq", s, NQ.format(d=s), CACHE / f"nq_{s}.txt"))
            tasks.append(("nyse", s, NYSE.format(y=d.year, ym=s[:6], d=s), CACHE / f"nyse_{s}.xls"))
        d += dt.timedelta(days=1)
    tasks += [("cboe", str(y), CBOE.format(y=y), CACHE / f"cboe_{y}.csv") for y in range(2016, 2027)]
    todo = [t for t in tasks if not t[3].exists() and (t[0], t[1]) not in done]
    print(f"{len(tasks)} files wanted, {len(todo)} to fetch", flush=True)
    stats, t0 = defaultdict(int), time.time()
    with ThreadPoolExecutor(4) as ex, MISSING.open("a") as mf:
        for n, (kind, key, st) in enumerate(ex.map(_fetch, todo), 1):
            stats[st] += 1
            if st not in ("ok", "error"):
                mf.write(f"{kind} {key} {st}\n")
                mf.flush()
            if n % 200 == 0:
                print(n, dict(stats), f"{time.time() - t0:.0f}s", flush=True)
            if time.time() - t0 > 540:  # stay inside a tool timeout; rerun resumes
                print("time slice used, rerun to continue", flush=True)
                break
    print("done", dict(stats))


# ---------------------------------------------------------------- census
def _day(v) -> dt.date | None:
    if isinstance(v, float):
        return (dt.datetime(1899, 12, 30) + dt.timedelta(days=int(v))).date()
    for f in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(str(v).strip().split(" ")[0], f).date()
        except ValueError:
            pass
    return None


def _tod(v) -> int | None:  # seconds after midnight
    if isinstance(v, float):
        return round((v % 1) * 86400)
    m = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AP]M)?", str(v), re.IGNORECASE)
    if not m:
        return None
    h, mi, s = int(m[1]), int(m[2]), int(m[3] or 0)
    if m[4]:
        h = h % 12 + (12 if m[4].upper() == "PM" else 0)
    return h * 3600 + mi * 60 + s


def load_triggers() -> pd.DataFrame:
    out, bad = [], defaultdict(int)
    for f in sorted(CACHE.glob("nq_*.txt")):
        for r in csv.DictReader(f.open(encoding="latin-1")):
            tt = r.get("Trigger Time") or ""
            out.append((r["Symbol"], _day(tt), _tod(tt), "nasdaq"))
    for f in sorted(CACHE.glob("nyse_*.xls")):
        try:
            rows = read_xls(f)
        except Exception as e:  # noqa: BLE001 (report, do not hide)
            bad[f.name] = str(e)[:60]
            continue
        hdr = [str(x).strip() for x in rows[0]]
        i_d, i_s, i_t = hdr.index("Trigger Date"), hdr.index("Issue Symbol"), hdr.index("Trigger Time")
        for r in rows[1:]:
            r = r + [None] * (len(hdr) - len(r))
            out.append((str(r[i_s]).strip(), _day(r[i_d]), _tod(r[i_t]), "nyse"))
    for f in sorted(CACHE.glob("cboe_*.csv")):
        for r in csv.DictReader(f.open(encoding="latin-1")):
            out.append((r["Symbol"], _day(r["Trigger Date"]), _tod(r["Trigger Time"]), "cboe"))
    df = pd.DataFrame(out, columns=["symbol", "date", "tod", "source"]).dropna(subset=["symbol", "date"])
    df = df[(df.date >= START) & (df.date <= END)]
    df["key"] = df.symbol.str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
    df["tod"] = df.tod.fillna(0)
    raw = len(df)
    df = df.sort_values("tod").drop_duplicates(["key", "date"], keep="first").sort_values(["date", "tod"]).reset_index(drop=True)
    print(f"rows {raw} -> deduped triggers {len(df)}; unreadable xls {len(bad)} {dict(list(bad.items())[:3])}")
    df.attrs["bad"] = dict(bad)
    return df


def closes(sym: str) -> pd.Series | None:
    parts = []
    for d in ("alpaca_1d", "alpaca_1d_fwd"):
        p = ROOT / "data" / "cache" / d / f"{sym}.csv"
        if p.exists():
            parts.append(pd.read_csv(p, usecols=["ts", "close"]))
    if not parts:
        return None
    x = pd.concat(parts).drop_duplicates("ts")
    return pd.Series(x.close.values, index=pd.to_datetime(x.ts.str[:10]).values).sort_index()


def census() -> None:
    tr = load_triggers()
    um = pd.concat([pd.read_csv(ROOT / "data" / "cache" / p / "universe.csv") for p in ("alpaca_meta", "alpaca_meta_fwd")])
    um = um.drop_duplicates(["month", "symbol"])
    um["key"] = um.symbol.str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
    print("universe key collisions:", int(um.duplicated(["month", "key"]).sum()))
    members = {(m, k): s for m, k, s in zip(um.month, um.key, um.symbol)}
    umonths = set(um.month)
    tr["month"] = tr.date.map(lambda d: d.strftime("%Y-%m"))
    tr["usym"] = [members.get((m, k)) for m, k in zip(tr.month, tr.key)]
    tr["uni"] = tr.usym.notna() & tr.month.isin(umonths)
    punct = um[um.symbol.str.contains(r"[^A-Z]")].symbol.unique()
    print("universe symbols with punctuation:", list(punct))
    for s in punct:  # how the file spellings look for these names
        k = re.sub(r"[^A-Z0-9]", "", s)
        print(" ", s, "-> key", k, "raw spellings in files:", sorted(tr[tr.key == k].symbol.unique())[:4])
    tr["year"] = [d.year for d in tr.date]
    # trading calendar from SPY (a calendar only, no returns)
    spy = closes("SPY")
    cal = pd.DatetimeIndex(spy.index)
    caldates = [d.date() for d in cal]
    nxt = {a: b for a, b in pairwise(caldates)}
    u = tr[tr.uni].copy()
    u["next"] = u.date.map(nxt)
    u["next_in_uni"] = [(n is not None and (members.get((n.strftime("%Y-%m"), k)) is not None)) for n, k in zip(u.next, u.key)]
    u["hasnext"] = u.next.notna()
    u["h"] = u.tod / 3600
    rows = []
    for y, g in tr.groupby("year"):
        gu = u[u.year == y]
        per = gu.groupby("date").size()
        covered = len({f"{y}-{i:02d}" for i in range(1, 13)} & umonths & {m for m in umonths if m <= "2026-10"})
        hn = gu[gu.hasnext]
        rows.append(dict(year=y, all=len(g), uni=len(gu), dates=len(per), months=covered, dates_12m=len(per) * 12 / max(covered, 1),  # noqa: C408
                         med=per.median(), p90=per.quantile(.9), max=per.max(),
                         pre10=(gu.h < 10).mean(), mid=((gu.h >= 10) & (gu.h < 15)).mean(), post15=(gu.h >= 15).mean(),
                         next_in=hn.next_in_uni.mean() if len(hn) else np.nan))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(t.round(2).to_string(index=False))
    top = u.groupby("date").size().sort_values(ascending=False).head(10)
    print("top 10 dates (universe triggers):", {str(k): int(v) for k, v in top.items()})
    ann = t[t.months > 0].dates_12m.mean()
    print("average independent universe trigger dates per year (annualised for part-years):", round(ann, 1))
    # ---- power line (no returns on or after any trigger day)
    trig_by_sym = tr.groupby("key").date.apply(lambda s: np.array(sorted(pd.to_datetime(list(s)).values)))
    um_by_sym = um.groupby("symbol").month.apply(set)
    parts = []
    for sym, months in um_by_sym.items():
        c = closes(sym)
        if c is None or len(c) < 30:
            continue
        r = c.pct_change()
        bad = np.zeros(len(c), bool)
        k = re.sub(r"[^A-Z0-9]", "", sym.upper())
        for d in trig_by_sym.get(k, []):
            i = c.index.searchsorted(d)
            bad[max(i - 5, 0):i + 6] = True
        mm = c.index.strftime("%Y-%m")
        ok = ~bad & np.isin(mm, list(months)) & r.notna().values & (np.abs(r.fillna(0).values) < 5)
        parts.append(pd.DataFrame({"date": c.index[ok], "r": r.values[ok]}))
    nt = pd.concat(parts)
    print(f"non-trigger member-days: {len(nt)} names {len(parts)}")
    res = {}
    for name, lo, hi in (("2016-2021", 2016, 2021), ("2022-2026", 2022, 2026)):
        x = nt[(nt.date.dt.year >= lo) & (nt.date.dt.year <= hi)]
        sd = x.r.std()
        g = x.groupby("date").r.agg(["mean", "size"])
        g = g[g["size"] >= 100]
        nbar = g["size"].mean()
        var_m = (g["mean"] ** 2).mean()
        rho = float(np.clip((var_m * nbar - sd**2) / (sd**2 * (nbar - 1)), 0, 1))
        gu = u[(u.year >= lo) & (u.year <= hi) & u.hasnext]
        # the next-day return must exist: next trading day inside the price data window
        per = gu.groupby("date").size()
        m_tot = int(per.sum())
        mbar = float((per**2).sum() / per.sum()) if m_tot else np.nan
        se = sd * np.sqrt((1 + (mbar - 1) * rho) / m_tot) if m_tot else np.nan
        res[name] = {"sd": sd, "rho": rho, "nbar": nbar, "M": m_tot, "dates": len(per), "mbar": mbar, "se": se, "mde": 3 * se}
        print(name, {k: round(float(v), 5) for k, v in res[name].items()})
    pd.DataFrame(res).T.to_csv(CACHE / "power.csv")
    t.to_csv(CACHE / "census_by_year.csv", index=False)
    print("missing files by kind:", pd.Series([x.split()[0] for x in MISSING.read_text().splitlines()]).value_counts().to_dict() if MISSING.exists() else {})
    print("unreadable xls:", tr.attrs.get("bad"))


if __name__ == "__main__":
    {"download": download, "census": census}[sys.argv[1]]()
