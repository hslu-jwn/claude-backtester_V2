"""Wide Binance USD-M universe for the crypto split (rule set by the user, 2026-11-14; research-runner.md › Periods).

Every USDT-margined perpetual on data.binance.vision (delisted ones included; dated quarterlies and non-USDT
pairs skipped): monthly 1d klines (incl. taker buy volume) and monthly funding files, months up to --end only
(default 2023-12: development; the test months are fetched later, once, for a frozen rule).
Writes data/cache/binance_wide/klines_1d/<SYM>.csv and data/cache/binance_wide/funding/<SYM>.csv (not committed).
Run: .venv/Scripts/python.exe research/screens/2026-11-14_binance_wide_download.py [--end 2023-12] [--workers 8]
Test months: ... --start 2024-01 --end 2026-10 --out data/cache/binance_wide_test
"""
import argparse
import io
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
OUT = Path("data/cache/binance_wide")
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
KCOLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count",
         "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def listing(prefix, delimiter=None):
    keys, prefixes, marker = [], [], ""
    while True:
        params = {"prefix": prefix, "marker": marker}
        if delimiter:
            params["delimiter"] = delimiter
        root = ET.fromstring(requests.get(S3, params=params, timeout=60).content)
        keys += [k.text for k in root.iter(NS + "Key")]
        prefixes += [p.text for p in root.iter(NS + "Prefix") if p.text != prefix]
        if root.findtext(NS + "IsTruncated") != "true":
            return keys, prefixes
        marker = (keys or prefixes)[-1] if not root.findtext(NS + "NextMarker") else root.findtext(NS + "NextMarker")


def fetch_csv(key, names):
    for attempt in range(4):
        try:
            r = requests.get(CDN + key, timeout=60)
            r.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(r.content))
            raw = z.read(z.namelist()[0]).decode()
            first = raw.split("\n", 1)[0]
            header = 0 if not first[:1].isdigit() else None  # later files carry a header row
            return pd.read_csv(io.StringIO(raw), header=header, names=None if header == 0 else names)
        except (requests.RequestException, zipfile.BadZipFile, ValueError):
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {key}")


def month_of(key):
    return re.search(r"(\d{4}-\d{2})\.zip$", key).group(1)


def symbol(sym, end, start="0000-00"):
    out = {}
    for kind, prefix, names in (("klines_1d", f"data/futures/um/monthly/klines/{sym}/1d/", KCOLS),
                                ("funding", f"data/futures/um/monthly/fundingRate/{sym}/", None)):
        path = OUT / kind / f"{sym}.csv"
        if path.exists():
            out[kind] = "cached"
            continue
        keys = [k for k in listing(prefix)[0] if k.endswith(".zip") and start <= month_of(k) <= end]
        if not keys:
            out[kind] = 0
            continue
        df = pd.concat([fetch_csv(k, names) for k in sorted(keys)], ignore_index=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path.with_suffix(".tmp"), index=False)
        path.with_suffix(".tmp").replace(path)
        out[kind] = len(keys)
    return sym, out


def safe(sym, end, start):
    try:
        return symbol(sym, end, start)
    except (RuntimeError, requests.RequestException, ET.ParseError) as e:
        return sym, f"ERROR {e}"


def main(argv):
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", default="2023-12")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--start", default="0000-00", help="first month (test download: 2024-01)")
    ap.add_argument("--out", type=Path, default=OUT, help="e.g. data/cache/binance_wide_test")
    a = ap.parse_args(argv)
    OUT = a.out
    _, prefixes = listing("data/futures/um/monthly/klines/", "/")
    syms = sorted(p.rstrip("/").rsplit("/", 1)[-1] for p in prefixes)
    syms = [s for s in syms if s.endswith("USDT") and "_" not in s]
    print(f"{len(syms)} USDT perps listed", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        for sym, out in ex.map(lambda s: safe(s, a.end, a.start), syms):
            print(sym, out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
