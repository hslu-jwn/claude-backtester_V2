"""Daily wide Binance universe and complete monthly archive updates.

Spec: strategy-crypto_flow.md › Venue, data, costs; Build.
Only this module knows the on-disk wide-universe layout.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOTS = (Path("data/cache/binance_wide"), Path("data/cache/binance_wide_test"))
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
CDN = "https://data.binance.vision/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
KCOLS = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
)
FCOLS = ("calc_time", "funding_interval_hours", "last_funding_rate")
PRICE_COLUMNS = ("open", "close", "volume", "quote_volume", "taker_buy_volume")


def _csv(raw: str, names: Sequence[str]) -> pd.DataFrame:
    header = 0 if not raw[:1].isdigit() else None
    return pd.read_csv(io.StringIO(raw), header=header, names=None if header == 0 else names)


def _parts(symbol: str, roots: Sequence[Path], kind: str, names) -> list[pd.DataFrame]:
    return [
        _csv(path.read_text(encoding="utf-8"), names)
        for root in roots
        if (path := root / kind / f"{symbol}.csv").exists()
    ]


def read_klines(symbol: str, roots: Sequence[Path] = ROOTS) -> pd.DataFrame:
    """UTC days, first root wins on overlap, in chronological order."""
    parts = _parts(symbol, roots, "klines_1d", KCOLS)
    if not parts:
        return pd.DataFrame(columns=PRICE_COLUMNS, index=pd.DatetimeIndex([], tz="UTC"))
    data = pd.concat(parts, ignore_index=True)
    data.index = pd.to_datetime(data.open_time, unit="ms", utc=True).dt.normalize()
    return data.loc[~data.index.duplicated(), list(PRICE_COLUMNS)].sort_index()


def read_funding(symbol: str, roots: Sequence[Path] = ROOTS) -> pd.Series:
    """Settlements floored to UTC minutes, as in the frozen reference screen."""
    parts = _parts(symbol, roots, "funding", FCOLS)
    if not parts:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    data = pd.concat(parts, ignore_index=True)
    return pd.Series(
        data.last_funding_rate.to_numpy(),
        index=pd.to_datetime(data.calc_time, unit="ms", utc=True).dt.floor("min"),
    ).sort_index()


def symbols(roots: Sequence[Path] = ROOTS) -> list[str]:
    """Sorted union of daily CSV stems across roots."""
    return sorted({p.stem for root in roots for p in (root / "klines_1d").glob("*.csv")})


def _fetch(url: str, params: dict | None = None) -> bytes:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.content


def _listing(prefix: str, fetch: Callable, delimiter: str | None = None):
    keys, prefixes, marker = [], [], ""
    while True:
        params = {"prefix": prefix, "marker": marker}
        if delimiter:
            params["delimiter"] = delimiter
        root = ET.fromstring(fetch(S3, params=params))
        # Strip the S3 XML namespace; also permits namespace-free fixture listings.
        for node in root.iter():
            node.tag = node.tag.rsplit("}", 1)[-1]
        page_keys = [node.text for node in root.iter("Key")]
        page_prefixes = [node.text for node in root.iter("Prefix") if node.text != prefix]
        keys.extend(page_keys)
        prefixes.extend(page_prefixes)
        if root.findtext("IsTruncated") != "true":
            return keys, prefixes
        next_marker = root.findtext("NextMarker") or (page_keys or page_prefixes)[-1]
        if next_marker == marker:
            raise ValueError("S3 listing did not advance")
        marker = next_marker


def update(root: Path, end_month: str, *, fetch: Callable = _fetch) -> None:
    """Append missing complete months, independently for prices and funding.

    ``fetch(url, params=None) -> bytes`` handles both listings and ZIPs. Each CSV
    is replaced atomically only after all its requested downloads succeeded.
    Spec: strategy-crypto_flow.md › Build (monthly archives only).
    """
    requested = datetime.strptime(end_month, "%Y-%m").strftime("%Y-%m")
    complete = (datetime.now(UTC).date().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    end_month = min(requested, complete)
    base = "data/futures/um/monthly/"
    _, prefixes = _listing(base + "klines/", fetch, "/")
    universe = sorted({p.rstrip("/").rsplit("/", 1)[-1] for p in prefixes})
    for symbol in universe:
        if not symbol.endswith("USDT") or "_" in symbol:
            continue
        for kind, prefix, names, time_col in (
            ("klines_1d", f"{base}klines/{symbol}/1d/", KCOLS, "open_time"),
            ("funding", f"{base}fundingRate/{symbol}/", FCOLS, "calc_time"),
        ):
            path = root / kind / f"{symbol}.csv"
            old = _csv(path.read_text(encoding="utf-8"), names) if path.exists() else None
            last = (
                pd.to_datetime(old[time_col], unit="ms", utc=True).max().strftime("%Y-%m")
                if old is not None and len(old)
                else "2023-12"
            )
            keys, _ = _listing(prefix, fetch)
            keys = sorted(
                key
                for key in keys
                if (match := re.search(r"(\d{4}-\d{2})\.zip$", key))
                and last < match[1] <= end_month
            )
            if not keys:
                continue
            parts = [old] if old is not None else []
            for key in keys:
                with zipfile.ZipFile(io.BytesIO(fetch(CDN + key))) as archive:
                    parts.append(_csv(archive.read(archive.namelist()[0]).decode(), names))
            data = pd.concat(parts, ignore_index=True)
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            try:
                data.to_csv(temporary, index=False)
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
