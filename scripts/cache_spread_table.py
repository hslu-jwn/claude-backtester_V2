"""Hourly spread tables (median / p90 by New York year and hour) from the MT5 cache, read-only.

The cache's ask is bid + MT5's bar spread (data/mt5_download.py), so ask - bid is the bar spread the
packaged table was built from by `tools/spread_table.py` from the live terminal (GBPUSD / XAUUSD rebuilt
from the cache: 239 / 254 cells identical, the rest one tick apart). Proposal of 2026-11-13
(docs/spread-table-extension.md); it writes only to OUT_DIR.

Run: PYTHONPATH=src .venv/Scripts/python.exe scripts/cache_spread_table.py SYM1,SYM2 OUT_DIR
"""
import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.tools.spread_table import SpreadCollector


def frames(symbol, first=2015):
    for y in range(first, 2027):
        files = sorted(glob.glob(f"data/cache/mt5/{symbol}/{y}/*.parquet"))
        if not files: continue
        d = pd.concat([pd.read_parquet(f, columns=["ts", "bid_close", "ask_close"]) for f in files])
        sp = (d.ask_close - d.bid_close).to_numpy()
        yield pd.DataFrame({"ts": d.ts.to_numpy(), "spread": np.nan_to_num(sp, nan=0.0)})

if __name__ == "__main__":
    syms, out = sys.argv[1].split(","), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    c = SpreadCollector()
    for s in syms:
        t = time.time(); n = 0
        for f in frames(s):
            c.add(s, f); n += len(f)
        print(s, n, f"{time.time()-t:.0f}s", flush=True)
    for stat in ("median", "p90"):
        table, cov = c.build(stat, "FTMO MT5 cache (ask - bid), NY hour")
        (out / f"cache_spread_{stat}.json").write_text(json.dumps(table.to_dict(), indent=1))
    pd.DataFrame(cov).to_csv(out / "coverage.csv", index=False)
