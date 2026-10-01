"""Load candles from local CSV files: data/raw/<SYMBOL>_<TF>.csv

Expected header: timestamp,open,high,low,close[,volume]
`timestamp` is ISO-8601 (candle open time). Naive timestamps are treated as UTC.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path

from backtester.core.models import Candle, Timeframe
from backtester.data.adapters.base import DataAdapter


class CsvAdapter(DataAdapter):
    def __init__(self, root: str | Path = "data/raw"):
        self.root = Path(root)

    def path_for(self, symbol: str, timeframe: Timeframe) -> Path:
        return self.root / f"{symbol}_{timeframe.name}.csv"

    def fetch(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[Candle]:
        start, end = _utc(start), _utc(end)
        out: list[Candle] = []
        with self.path_for(symbol, timeframe).open(newline="") as f:
            for row in csv.DictReader(f):
                ts = _utc(datetime.fromisoformat(row["timestamp"]))
                if start <= ts < end:
                    out.append(
                        Candle(
                            ts=ts,
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row.get("volume") or 0.0),
                        )
                    )
        out.sort(key=lambda c: c.ts)
        return out


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
