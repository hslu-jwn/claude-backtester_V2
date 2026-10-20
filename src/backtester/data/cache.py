"""The Parquet day cache: one file per symbol and UTC day, written by `data/histdata.py`.

Spec: ARCHITECTURE.md › Data sources › histdata.com.

Layout (git-ignored): `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet` with the columns
`ts` (UTC minute open time) and `bid_*` / `ask_*` OHLCV. A day without data is cached as
an empty file, so it is known and not mistaken for a missing day.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.dataset

_PRICE_FIELDS = ("open", "high", "low", "close")
COLUMNS = ["ts"] + [f"{s}_{f}" for s in ("bid", "ask") for f in (*_PRICE_FIELDS, "volume")]

DEFAULT_CACHE_DIR = Path("data/cache/histdata")
MT5_CACHE_DIR = Path("data/cache/mt5")  # FTMO M1 bars, written by `data/mt5_download.py`


def cache_path(cache_dir: Path, symbol: str, day: date) -> Path:
    return Path(cache_dir) / symbol / f"{day.year:04d}" / f"{day.isoformat()}.parquet"


def read_cached_day(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


@dataclass(frozen=True)
class ReadConfig:
    chunk_files: int = 60  # day files read per step when a caller wants progress / cancel


READ = ReadConfig()


def read_cached_days(
    paths: list[Path],
    on_chunk: Callable[[int, int], None] | None = None,
    chunk_files: int = READ.chunk_files,
) -> pd.DataFrame:
    """Several day files as one frame (cache columns, file order), read in one go: with
    years cached that is about 9 times faster than one file at a time.

    With `on_chunk(files_done, files_total)` the files are read `chunk_files` at a time and the
    callback is called after each chunk (the backtest page's loading bar and its cancel; an
    exception raised in it stops the read)."""
    if len(paths) == 1:
        frame = read_cached_day(paths[0])
        if on_chunk is not None:
            on_chunk(1, 1)
        return frame
    if not paths:
        return empty_cache_frame()
    if on_chunk is None:
        table = pyarrow.dataset.dataset([str(p) for p in paths], format="parquet").to_table()
    else:
        tables = []
        for i in range(0, len(paths), chunk_files):
            chunk = paths[i : i + chunk_files]
            tables.append(
                pyarrow.dataset.dataset([str(p) for p in chunk], format="parquet").to_table()
            )
            on_chunk(i + len(chunk), len(paths))
        table = pa.concat_tables(tables, promote_options="permissive")  # ms / us files mix
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
