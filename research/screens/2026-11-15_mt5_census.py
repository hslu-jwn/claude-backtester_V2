"""FTMO MT5 census (Fable backlog FB-228 / FB-111 / FB-302, 2026-11-15): every symbol on the server with its group,
contract size, swap (raw and in bp a night), triple-swap weekday, last-known spread and D1 history depth.

Read-only MT5 calls. A symbol must be in Market Watch for history; symbols added here are hidden again at the end
(the Market Watch list is restored). Spreads are the last known quote (a weekend run shows Friday's close or a
widened weekend spread). Writes results/mt5_census.csv.
Run: .venv/Scripts/python.exe -u research/screens/2026-11-15_mt5_census.py
"""
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import MetaTrader5 as mt5

OUT = Path("results/mt5_census.csv")
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def swap_bp(i, value):
    """bp of notional a night: mode 1 = points per lot, mode 5 = % a year of the current price."""
    if i.swap_mode == 1 and i.bid > 0:
        return value * i.point / i.bid * 1e4
    if i.swap_mode == 5:
        return value / 365 * 100
    return None


def main():
    d = json.loads(Path("results/trading.json").read_text(encoding="utf-8"))
    if not mt5.initialize(path=d["terminal_path"]):
        raise SystemExit(f"MT5 init failed: {mt5.last_error()}")
    syms = mt5.symbols_get()
    visible = {s.name for s in syms if s.visible}
    added, rows = [], []
    try:
        for s in syms:
            if s.name not in visible:
                if not mt5.symbol_select(s.name, True):
                    continue
                added.append(s.name)
            i = mt5.symbol_info(s.name)
            r = mt5.copy_rates_range(s.name, mt5.TIMEFRAME_D1, datetime(2000, 1, 1, tzinfo=UTC),
                                     datetime.now(UTC))
            first = datetime.fromtimestamp(int(r[0]["time"]), UTC).date().isoformat() if r is not None and len(r) else ""
            sl, ss = swap_bp(i, i.swap_long), swap_bp(i, i.swap_short)
            row = {"symbol": s.name, "group": s.path.split("\\")[0], "contract": i.trade_contract_size,
                   "currency_profit": i.currency_profit, "bid": i.bid,
                   "spread_bp": round((i.ask - i.bid) / i.bid * 1e4, 2) if i.bid > 0 and i.ask > 0 else "",
                   "swap_mode": i.swap_mode, "swap_long": i.swap_long, "swap_short": i.swap_short,
                   "swap_long_bp_night": round(sl, 3) if sl is not None else "",
                   "swap_short_bp_night": round(ss, 3) if ss is not None else "",
                   "triple_swap_day": DAYS[i.swap_rollover3days] if 0 <= i.swap_rollover3days < 7 else "",
                   "volume_min": i.volume_min, "d1_first": first, "d1_bars": len(r) if r is not None else 0}
            rows.append(row)
            print(row["symbol"], row["group"], row["d1_first"], row["spread_bp"], row["swap_long_bp_night"],
                  row["swap_short_bp_night"], flush=True)
    finally:
        for n in added:
            mt5.symbol_select(n, False)
        mt5.shutdown()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} symbols -> {OUT}; Market Watch restored ({len(added)} hidden again)")


if __name__ == "__main__":
    main()
