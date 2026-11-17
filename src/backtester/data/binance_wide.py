"""Daily wide Binance universe and complete monthly archive updates.

Spec: strategy-crypto_flow.md › Venue, data, costs; Build.
Only this module knows the on-disk wide-universe layout.
"""

from __future__ import annotations

import io
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

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
    d = pd.read_csv(io.StringIO(raw), header=header, names=None if header == 0 else names)
    for col in ("open_time", "close_time"):  # Binance spot archives use microseconds from 2025
        if col in d:
            d[col] = d[col].where(d[col] < 10**14, d[col] // 1000)
    return d


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
    # standard-library TLS with the system certificate store (verification on): the venv's certifi bundle
    # 2026.10.19 fails Binance's S3 / CDN chain while the Windows store verifies it (2026-11-17)
    url = urllib.parse.quote(url, safe=":/%")  # non-ASCII symbol names (requests did this itself)
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(
                url, timeout=60, context=ssl.create_default_context()
            ) as response:
                return response.read()
        except urllib.error.HTTPError:
            raise  # a missing file or a refusal is not transient
        except OSError:  # dropped connection, timeout: hundreds of requests per update
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    raise AssertionError("unreachable")


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


def _complete(end_month: str) -> str:
    requested = datetime.strptime(end_month, "%Y-%m").strftime("%Y-%m")
    complete = (datetime.now(UTC).date().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    return min(requested, complete)


def _append_months(
    path: Path, prefix: str, names, time_col: str, after: str, end_month: str, fetch
) -> None:
    """Append the archive months after the file's last month (or `after`) up to `end_month`; atomic replace."""
    old = _csv(path.read_text(encoding="utf-8"), names) if path.exists() else None
    last = (
        pd.to_datetime(old[time_col], unit="ms", utc=True).max().strftime("%Y-%m")
        if old is not None and len(old)
        else after
    )
    keys, _ = _listing(prefix, fetch)
    keys = sorted(
        key
        for key in keys
        if (match := re.search(r"(\d{4}-\d{2})\.zip$", key)) and last < match[1] <= end_month
    )
    if not keys:
        return
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


def update(root: Path, end_month: str, *, fetch: Callable = _fetch) -> None:
    """Append missing complete months, independently for prices and funding.

    ``fetch(url, params=None) -> bytes`` handles both listings and ZIPs. Each CSV
    is replaced atomically only after all its requested downloads succeeded.
    Spec: strategy-crypto_flow.md › Build (monthly archives only).
    """
    end_month = _complete(end_month)
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
            _append_months(
                root / kind / f"{symbol}.csv", prefix, names, time_col, "2023-12", end_month, fetch
            )


def update_spot(
    root: Path,
    symbols: Sequence[str],
    end_month: str,
    *,
    start_after: str,
    fetch: Callable = _fetch,
) -> None:
    """Spot daily klines of the given (perp) symbols: complete months after `start_after` (or the file's last month).
    Forward logs of the shelf rows I-84 / I-98 (research-runner.md › Verdicts and shelf)."""
    end_month = _complete(end_month)
    for symbol in symbols:
        prefix = f"data/spot/monthly/klines/{symbol}/1d/"
        _append_months(
            root / "klines_1d" / f"{symbol}.csv",
            prefix,
            KCOLS,
            "open_time",
            start_after,
            end_month,
            fetch,
        )
