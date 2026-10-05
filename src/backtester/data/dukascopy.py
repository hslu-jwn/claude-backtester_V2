"""Dukascopy M1 downloader + Parquet cache.

Spec: ARCHITECTURE.md › Data sources › Dukascopy, ROADMAP.md › 0.1.

Dukascopy serves one LZMA-compressed `.bi5` file per symbol, UTC day and price side:

    {base_url}/{SYMBOL}/{YYYY}/{MM}/{DD}/{BID|ASK}_candles_min_1.bi5

`MM` is ZERO-BASED (January = 00). Each record is 24 bytes, big-endian:

    uint32 seconds since 00:00 UTC of that day
    uint32 open, uint32 close, uint32 low, uint32 high   (note: NOT OHLC order)
    float32 volume

Prices are integers; divide by the symbol's point factor. The parser rejects any record
whose high/low do not contain open/close, so a wrong field order fails loudly instead of
producing plausible-looking garbage.

Cache layout (git-ignored): `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet`, one file per
symbol and day with columns `ts` (UTC open time) and `bid_*` / `ask_*` OHLCV.
Dukascopy fills non-trading minutes (daily break, weekends, holidays) with flat zero-volume
candles; the cache keeps them unchanged, dropping them is 0.2's job. A day whose files are
missing or empty is cached as an empty file so a resumed download skips it.
"""

from __future__ import annotations

import http.client
import logging
import lzma
import os
import struct
import time
import urllib.parse
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

_RECORD = struct.Struct(">5If")  # time, open, close, low, high, volume
_PRICE_FIELDS = ("open", "high", "low", "close")
_COLUMNS = ["ts"] + [f"{s}_{f}" for s in ("bid", "ask") for f in (*_PRICE_FIELDS, "volume")]

DEFAULT_CACHE_DIR = Path("data/cache/dukascopy")

# Divisor turning Dukascopy's integer prices into quoted prices.
# Must be verified against a known candle (ARCHITECTURE.md › Data sources).
POINT_FACTORS: dict[str, int] = {
    "XAUUSD": 1_000,
    "GBPUSD": 100_000,
    "GBPJPY": 1_000,
}


class Side(Enum):
    BID = "BID"
    ASK = "ASK"


class DukascopyError(RuntimeError):
    """Download or parse failure that must not be silently cached."""


class ServerUnavailableError(DukascopyError):
    """All retries for one file failed with HTTP errors (503 = busy / throttling) or
    timeouts / dropped connections. A corrupt file is a plain DukascopyError instead."""


class RateLimitedError(RuntimeError):
    """HTTP 429: Dukascopy has blocked this IP for now. Every further request would fail
    too, so the whole download stops instead of marking day after day as failed."""


class DownloadStoppedError(RuntimeError):
    """Several days in a row failed with ServerUnavailableError: Dukascopy is throttling or
    unreachable, so the run stops instead of marking the rest of the range as failed."""


@dataclass(frozen=True, slots=True)
class DukascopyConfig:
    base_url: str = "https://datafeed.dukascopy.com/datafeed"
    request_delay_s: float = 2.0  # pause after every HTTP request, to be polite
    timeout_s: float = 10.0  # per connect / socket read; a 1-day file is < 100 kB
    retries: int = 5
    busy_backoff_s: float = 5.0  # after an HTTP error (503 = busy): backoff * attempt number
    network_retry_s: float = 2.0  # after a timeout / dropped connection
    user_agent: str = "backtester/0.1"
    # Stop the run after this many requested days in a row failed with 503s / timeouts.
    max_unavailable_days_in_row: int = 3


# A fetcher returns the raw file bytes, or None if the file does not exist (HTTP 404).
Fetcher = Callable[[str], bytes | None]


def day_url(symbol: str, day: date, side: Side, base_url: str) -> str:
    return (
        f"{base_url}/{symbol}/{day.year:04d}/{day.month - 1:02d}/{day.day:02d}"
        f"/{side.value}_candles_min_1.bi5"
    )


def parse_bi5(raw: bytes, day: date, point_factor: int) -> pd.DataFrame:
    """Decode one daily M1 candle file into columns ts, open, high, low, close, volume."""
    if not raw:
        return _empty_side_frame()
    try:
        data = lzma.decompress(raw)
    except lzma.LZMAError as e:
        raise DukascopyError(f"{day}: not a valid LZMA file") from e
    if len(data) % _RECORD.size:
        raise DukascopyError(f"{day}: {len(data)} bytes is not a multiple of {_RECORD.size}")

    day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    rows = []
    for secs, o, c, lo, h, vol in _RECORD.iter_unpack(data):
        if not (lo <= min(o, c) and h >= max(o, c)):
            raise DukascopyError(
                f"{day} +{secs}s: inconsistent OHLC (o={o} h={h} l={lo} c={c}); "
                "field order or file format is wrong"
            )
        rows.append(
            (
                day_start + timedelta(seconds=secs),
                o / point_factor,
                h / point_factor,
                lo / point_factor,
                c / point_factor,
                float(vol),
            )
        )
    return pd.DataFrame(rows, columns=["ts", *_PRICE_FIELDS, "volume"])


def merge_sides(bid: pd.DataFrame, ask: pd.DataFrame) -> pd.DataFrame:
    """Join bid and ask on the minute. Minutes present on one side only keep NaN on the other."""
    merged = pd.merge(
        bid.add_prefix("bid_").rename(columns={"bid_ts": "ts"}),
        ask.add_prefix("ask_").rename(columns={"ask_ts": "ts"}),
        on="ts",
        how="outer",
    )
    merged["ts"] = pd.to_datetime(merged["ts"], utc=True)
    return merged[_COLUMNS].sort_values("ts", ignore_index=True)


def http_fetcher(config: DukascopyConfig) -> Fetcher:
    """Fetch over one kept-alive HTTPS connection per host, so a flaky network (hotspot)
    doesn't pay a TLS handshake per file. Returns None on 404, raises DukascopyError after
    the last retry.

    A failure on a reused connection the server has silently closed is retried once
    immediately on a fresh connection, without counting as an attempt.
    """
    conns: dict[str, http.client.HTTPSConnection] = {}

    def drop(host: str) -> None:
        if conn := conns.pop(host, None):
            conn.close()

    def get(host: str, path: str) -> tuple[int, bytes]:
        if host not in conns:
            conns[host] = http.client.HTTPSConnection(host, timeout=config.timeout_s)
        conn = conns[host]
        conn.request("GET", path, headers={"User-Agent": config.user_agent})
        resp = conn.getresponse()
        return resp.status, resp.read()

    def fetch(url: str) -> bytes | None:
        parts = urllib.parse.urlsplit(url)
        host, path = parts.netloc, parts.path
        stale_retry_used = False
        attempt = 0
        while attempt < config.retries:
            attempt += 1
            reused = host in conns
            try:
                status, body = get(host, path)
            except (ConnectionResetError, BrokenPipeError) as e:
                # RemoteDisconnected is a ConnectionResetError: the idle connection was closed.
                drop(host)
                if reused and not stale_retry_used:
                    stale_retry_used = True
                    attempt -= 1
                    continue
                err: Exception = e
                wait = config.network_retry_s
            # OSError covers timeouts, refused/reset connections (WinError 10060/10054) and
            # TLS errors; HTTPException covers truncated responses (IncompleteRead).
            except (OSError, http.client.HTTPException) as e:
                drop(host)
                err = e
                wait = config.network_retry_s
            else:
                time.sleep(config.request_delay_s)
                if status == 200:
                    return body
                if status == 404:
                    return None
                if status == 429:
                    raise RateLimitedError(f"HTTP 429 Too Many Requests for {url}")
                err = DukascopyError(f"HTTP {status}")
                wait = config.busy_backoff_s * attempt
            log.warning("attempt %d/%d failed for %s: %s", attempt, config.retries, url, err)
            if attempt < config.retries:
                time.sleep(wait)
        raise ServerUnavailableError(f"giving up on {url}: {err}")

    return fetch


class DayStatus(Enum):
    CACHED = "cached"  # already on disk, skipped
    DOWNLOADED = "downloaded"
    EMPTY = "empty"  # no file / empty file from Dukascopy, empty file cached
    FAILED = "failed"  # nothing written; a rerun will retry it


@dataclass(slots=True)
class DayResult:
    day: date
    status: DayStatus
    rows: int = 0
    error: str = ""
    server_unavailable: bool = False  # failed with 503s / timeouts, not bad data


@dataclass
class DukascopyDownloader:
    cache_dir: Path
    config: DukascopyConfig = field(default_factory=DukascopyConfig)
    fetcher: Fetcher | None = None

    def __post_init__(self) -> None:
        self.cache_dir = Path(self.cache_dir)
        if self.fetcher is None:
            self.fetcher = http_fetcher(self.config)

    def path_for(self, symbol: str, day: date) -> Path:
        return cache_path(self.cache_dir, symbol, day)

    def download(
        self, symbol: str, start: date, end: date, today: date | None = None
    ) -> Iterator[DayResult]:
        """Download days start <= day < end. Days from `today` (UTC) on are not final yet
        on Dukascopy and are never requested.

        Raises DownloadStoppedError (after yielding the last failed day) once
        `max_unavailable_days_in_row` requested days in a row failed with 503s / timeouts.
        A day the server answered resets the count; a cached day makes no request and
        leaves it unchanged.
        """
        point_factor = _point_factor(symbol)
        today = today or datetime.now(UTC).date()
        limit = self.config.max_unavailable_days_in_row
        in_row = 0
        day = start
        while day < min(end, today):
            result = self._download_day(symbol, day, point_factor)
            yield result
            if result.status is not DayStatus.CACHED:
                in_row = in_row + 1 if result.server_unavailable else 0
            if in_row >= limit:
                raise DownloadStoppedError(
                    f"{in_row} days in a row failed with HTTP errors (503 = busy / "
                    f"throttling) or timeouts, last {symbol} {day}: {result.error}"
                )
            day += timedelta(days=1)

    def _download_day(self, symbol: str, day: date, point_factor: int) -> DayResult:
        path = self.path_for(symbol, day)
        if path.exists():
            return DayResult(day, DayStatus.CACHED)
        try:
            sides = {
                side: parse_bi5(
                    self.fetcher(day_url(symbol, day, side, self.config.base_url)) or b"",
                    day,
                    point_factor,
                )
                for side in Side
            }
        except DukascopyError as e:
            log.error("%s %s: %s", symbol, day, e)
            unavailable = isinstance(e, ServerUnavailableError)
            return DayResult(day, DayStatus.FAILED, error=str(e), server_unavailable=unavailable)

        bid, ask = sides[Side.BID], sides[Side.ASK]
        if bid.empty != ask.empty:
            msg = f"only {'ask' if bid.empty else 'bid'} data available"
            log.error("%s %s: %s", symbol, day, msg)
            return DayResult(day, DayStatus.FAILED, error=msg)

        frame = merge_sides(bid, ask) if not bid.empty else _empty_cache_frame()
        _write_atomic(frame, path)
        status = DayStatus.EMPTY if frame.empty else DayStatus.DOWNLOADED
        return DayResult(day, status, rows=len(frame))


def cache_path(cache_dir: Path, symbol: str, day: date) -> Path:
    return Path(cache_dir) / symbol / f"{day.year:04d}" / f"{day.isoformat()}.parquet"


def read_cached_day(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def _point_factor(symbol: str) -> int:
    try:
        return POINT_FACTORS[symbol]
    except KeyError:
        raise ValueError(
            f"No point factor for {symbol!r}; add it to POINT_FACTORS after verifying it "
            "against a known candle"
        ) from None


def _empty_side_frame() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="float64") for c in (*_PRICE_FIELDS, "volume")})
    frame.insert(0, "ts", pd.Series(dtype="datetime64[ns, UTC]"))
    return frame


def _empty_cache_frame() -> pd.DataFrame:
    frame = pd.DataFrame({c: pd.Series(dtype="float64") for c in _COLUMNS[1:]})
    frame.insert(0, "ts", pd.Series(dtype="datetime64[ns, UTC]"))
    return frame


def _write_atomic(frame: pd.DataFrame, path: Path) -> None:
    """Write via a temp file + rename so an interrupted run never leaves a half file
    that would later be skipped as 'cached'."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".parquet.tmp")
    frame.to_parquet(tmp, index=False)
    os.replace(tmp, path)
