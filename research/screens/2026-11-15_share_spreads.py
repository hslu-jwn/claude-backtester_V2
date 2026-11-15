"""FTMO share-CFD weekday spreads (cost cell for Wave 3, FB-112..115; 2026-11-15). Read-only MT5 calls.

M1 bars of the last 20 US trading days for the 46 US share CFDs: median spread (bp of the close) at 09:35-09:40 and
15:50-15:55 New York, plus D1 history start. Symbols added to Market Watch are hidden again. Writes
results/share_spreads.csv. Run: .venv/Scripts/python.exe -u research/screens/2026-11-15_share_spreads.py
"""
import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import MetaTrader5 as mt5
import numpy as np
import pandas as pd

from backtester.data.mt5_download import DEFAULT_CLOCK

NY = ZoneInfo("America/New_York")
CLOCK = DEFAULT_CLOCK  # FTMO server = New York + 7 h
OUT = Path("results/share_spreads.csv")
US = ["AAPL", "AMZN", "BABA", "BAC", "GOOG", "MSFT", "NFLX", "NVDA", "PFE", "RACE", "T", "TSLA", "V", "WMT", "ZM", "META", "GE", "BA", "RTX", "LMT", "PLTR", "AMD", "INTC", "QCOM", "AVGO", "CSCO", "JNJ", "MCD", "SBUX", "KO", "MSTR", "GME", "NKE", "CVX", "FDX", "JPM", "DIS", "GM", "IBM", "ARM", "SNOW", "ASML", "AZN", "BRK.B", "XOM", "SPCX"]


def main():
    d = json.loads(Path("results/trading.json").read_text(encoding="utf-8"))
    if not mt5.initialize(path=d["terminal_path"]):
        raise SystemExit(f"MT5 init failed: {mt5.last_error()}")
    visible = {s.name for s in mt5.symbols_get() if s.visible}
    added, rows = [], []
    end = datetime.now(UTC)
    try:
        for name in US:
            if name not in visible:
                if not mt5.symbol_select(name, True):
                    continue
                added.append(name)
            info = mt5.symbol_info(name)
            r = mt5.copy_rates_range(name, mt5.TIMEFRAME_M1, end - timedelta(days=30), end)
            if r is None or not len(r) or info is None:
                continue
            f = pd.DataFrame(r)
            f["bp"] = f.spread * info.point / f.close * 1e4
            hm = CLOCK.to_utc(f.time.to_numpy()).tz_convert(NY).strftime("%H:%M")
            o = f[(hm >= "09:35") & (hm < "09:40")].bp
            c = f[(hm >= "15:50") & (hm < "15:55")].bp
            rows.append({"symbol": name, "open_bp": round(float(np.median(o)), 2) if len(o) else "",
                         "close_bp": round(float(np.median(c)), 2) if len(c) else "",
                         "all_bp": round(float(np.median(f.bp)), 2), "bars": len(f),
                         "commission_note": "spread only (MT5 bar spread)"})
            print(rows[-1])
    finally:
        for name in added:
            mt5.symbol_select(name, False)
        mt5.shutdown()
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
