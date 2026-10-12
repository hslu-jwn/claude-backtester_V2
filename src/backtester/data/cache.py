"""The Parquet day cache: one file per symbol and UTC day, written by `data/histdata.py`.

Spec: ARCHITECTURE.md › Data sources › histdata.com.

Layout (git-ignored): `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet` with the columns
`ts` (UTC minute open time) and `bid_*` / `ask_*` OHLCV. A day without data is cached as
an empty file, so it is known and not mistaken for a missing day.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow.dataset

_PRICE_FIELDS = ("open", "high", "low", "close")
COLUMNS = ["ts"] + [f"{s}_{f}" for s in ("bid", "ask") for f in (*_PRICE_FIELDS, "volume")]

DEFAULT_CACHE_DIR = Path("data/cache/histdata")


def cache_path(cache_dir: Path, symbol: str, day: date) -> Path:
    return Path(cache_dir) / symbol / f"{day.year:04d}" / f"{day.isoformat()}.parquet"


def read_cached_day(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def read_cached_days(paths: list[Path]) -> pd.DataFrame:
    """Several day files as one frame (cache columns, file order), read in one go: with
    years cached that is about 9 times faster than one file at a time."""
    if len(paths) == 1:
        return read_cached_day(paths[0])
    if not paths:
        return empty_cache_frame()
    table = pyarrow.dataset.dataset([str(p) for p in paths], format="parquet").to_table()
    frame = table.to_pandas()
    return frame[COLUMNS] if len(frame) else empty_cache_frame()


def empty_cache_frame() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="float64") for c in COLUMNS[1:]})
    frame.insert(0, "ts", pd.Series(dtype="datetime64[ns, UTC]"))
    return frame


def write_atomic(frame: pd.DataFrame, path: Path) -> None:
    """Write via a temp file + rename so an interrupted run never leaves a half file
    that would later be skipped as 'cached'."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, path)
