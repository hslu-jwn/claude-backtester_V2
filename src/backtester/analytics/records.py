"""Trades read back from a run's trades.csv (runner.py `TRADE_COLUMNS`). Spec: ROADMAP.md › 3.6.

`TradeRecord` has the attributes `analytics/metrics.py` reads (`r_gross`, `r_net`,
`planned_r`, `entry_time`, `exit_time`, `symbol`, …), so the results page computes every
number from the file with the same functions that wrote summary.json.

Runs written before the `confluence` column existed: the confluence is taken from the
reason text (the item before "TP1 …", e.g. "…, 5m BOS 07:35, fvg, TP1 min R").
"""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _float(value) -> float | None:
    return None if value in (None, "") else float(value)


def _time(value) -> datetime | None:
    if value in (None, ""):
        return None
    return value if isinstance(value, datetime) else datetime.fromisoformat(value)


def confluence_from_reason(reason: str) -> str:
    items = reason.split(", ")
    for i, item in enumerate(items):
        if item.startswith("TP1") and i > 0:
            return items[i - 1]
    return ""


@dataclass(frozen=True)
class TradeRecord:
    id: int
    symbol: str
    direction: str  # "long" / "short"
    session: str  # "london 2026-09-02" ("" if none)
    entry_time: datetime  # close time of the entry candle
    entry_candle: datetime
    entry: float
    initial_stop: float
    take_profit: float | None  # None: no take profit
    take_profit_2: float | None
    tp1_share: float
    planned_r: float | None
    exit_time: datetime
    exit_price: float
    exit_reason: str
    r_gross: float
    r_net: float
    spread_r: float
    commission_r: float
    tags: frozenset[str]
    confluence: str
    reason: str
    parts: tuple[dict, ...]
    take_profit_3: float | None = None  # strategy 2 (files before it: none)
    tp2_share: float | None = None
    swap_r: float = 0.0  # inside r_net (files before swap: 0)
    funding_r: float = 0.0  # inside r_net (files before funding: 0)
    risk_weight: float = 1.0  # portfolio component stop risk; R fields are already weighted
    limit_fill: bool = False  # older CSVs have no entry kind: assume market
    entry_fill: float | None = None  # preserve actual fill for MTM; old files reconstruct spread
    tp_levels_touched: int = 0  # old files did not track touches
    tp_levels_touched_not_filled: int = 0

    @classmethod
    def from_row(cls, row: Mapping) -> TradeRecord:
        """From a trades.csv row (strings) or a `runner.trade_rows` row (typed values)."""
        reason = row.get("reason") or ""
        parts = row.get("parts") or "[]"
        return cls(
            id=int(row["id"]),
            symbol=row["symbol"],
            direction=row["direction"],
            session=row.get("session") or "",
            entry_time=_time(row["entry_time"]),
            entry_candle=_time(row["entry_candle"]),
            entry=float(row["entry"]),
            initial_stop=float(row["initial_stop"]),
            take_profit=_float(row.get("take_profit")),
            take_profit_2=_float(row.get("take_profit_2")),
            tp1_share=float(row.get("tp1_share") or 1.0),
            planned_r=_float(row.get("planned_rr")),
            exit_time=_time(row["exit_time"]),
            exit_price=float(row["exit_price"]),
            exit_reason=row["exit_reason"],
            r_gross=float(row["r_gross"]),
            r_net=float(row["r_net"]),
            spread_r=float(row.get("spread_r") or 0.0),
            commission_r=float(row.get("commission_r") or 0.0),
            tags=frozenset(t for t in (row.get("tags") or "").split(";") if t),
            confluence=row.get("confluence") or confluence_from_reason(reason),
            reason=reason,
            parts=tuple(json.loads(parts) if isinstance(parts, str) else parts),
            take_profit_3=_float(row.get("take_profit_3")),
            tp2_share=_float(row.get("tp2_share")),
            swap_r=float(row.get("swap_r") or 0.0),
            funding_r=float(row.get("funding_r") or 0.0),
            limit_fill=str(row.get("limit_fill", False)).lower() == "true",
            entry_fill=_float(row.get("entry_fill")),
            tp_levels_touched=int(row.get("tp_levels_touched") or 0),
            tp_levels_touched_not_filled=int(row.get("tp_levels_touched_not_filled") or 0),
        )


def read_trades(folder: Path) -> list[TradeRecord]:
    """The run's trades in file order (entry time order)."""
    path = Path(folder) / "trades.csv"
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [TradeRecord.from_row(row) for row in csv.DictReader(f)]
