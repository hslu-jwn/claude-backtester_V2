"""Binance USD-M futures trade data -> 1m bars with order flow (ROADMAP 11.9).

    python -m backtester.tools.binance_download                          # BTCUSDT + ETHUSDT, 2020-01 .. latest
    python -m backtester.tools.binance_download BTCUSDT --start 2024-01 --end 2024-01

Source: the public bulk archive https://data.binance.vision (user-approved, 2026-10-15).
Per month `data/futures/um/monthly/aggTrades/<SYM>/<SYM>-aggTrades-<YYYY>-<MM>.zip`, and for
months without a monthly file yet, one `.../daily/aggTrades/...-<YYYY>-<MM>-<DD>.zip` per day.
Each zip has a `.CHECKSUM` file (SHA256); a mismatch is an error and nothing is written.

Downloads are untrusted data: each zip goes to its own temp folder (`TMP_DIR`), only its one
CSV member is stream-parsed (never extracted, nothing executed), and the zip is deleted after
the month is cached.

Writes (all git-ignored, one file per UTC day, minutes without trades have no row, a day
without trades is an empty file):
- `data/cache/binance/<SYM>/<YYYY>/<date>.parquet`: the columns of `data/cache.py`;
  `bid_*` = `ask_*` = trade OHLC (spread 0), `bid_volume` = `ask_volume` = volume (base
  asset), so `SymbolSources` / every tool reads it like any other source.
- `data/cache/binance_flow/<SYM>/<YYYY>/<date>.parquet`: `ts, volume, buy_volume,
  sell_volume, delta, trades`. Buy = taker buy (`is_buyer_maker` False), delta = buy - sell,
  trades = sum(last_trade_id - first_trade_id + 1).
- `data/cache/binance_funding/<SYM>.csv`: `calc_time` (UTC), `funding_interval_hours`,
  `last_funding_rate`, from the monthly fundingRate files (for the cost model later).

Resumable: a month (or day) whose day files all exist is skipped. The daily fallback only
covers days before today (UTC); a daily file that is not published yet is skipped and picked
up by the next run.
"""

from __future__ import annotations

import csv
import hashlib
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from backtester.data.cache import COLUMNS, cache_path, empty_cache_frame, write_atomic
from backtester.paths import DATA_DIR

BASE_URL = "https://data.binance.vision/data/futures/um"
DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT")
FIRST_MONTH = date(2020, 1, 1)
CACHE_DIR = DATA_DIR / "cache/binance"
FLOW_DIR = DATA_DIR / "cache/binance_flow"
FUNDING_DIR = DATA_DIR / "cache/binance_funding"
TMP_DIR = DATA_DIR / "raw/binance_tmp"
FLOW_COLUMNS = ["ts", "volume", "buy_volume", "sell_volume", "delta", "trades"]
FUNDING_COLUMNS = ["calc_time", "funding_interval_hours", "last_funding_rate"]
TRADE_COLUMNS = (
    "agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
    "transact_time", "is_buyer_maker",
)  # fmt: skip
CHUNK_ROWS = 2_000_000  # CSV rows parsed at a time (memory)
MICROSECOND_LIMIT = 10**14  # a time above this is in microseconds, not milliseconds
MS_PER_MINUTE = 60_000
RETRIES = 4
TIMEOUT_S = 60
BLOCK_BYTES = 1 << 20


class ChecksumError(Exception):
    """The downloaded zip does not match its .CHECKSUM file."""


class NotFoundError(Exception):
    """The archive has no such file (HTTP 404): not published yet or never existed."""


Fetch = Callable[[str, Path], None]  # (url, destination file); raises NotFoundError on 404


def http_fetch(url: str, dest: Path) -> None:
    """Stream `url` to `dest` (a new file in the temp folder), retrying transient errors."""
    last: Exception | None = None
    for _ in range(RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp, open(dest, "wb") as out:
                while block := resp.read(BLOCK_BYTES):
                    out.write(block)
            return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                dest.unlink(missing_ok=True)
                raise NotFoundError(url) from e
            last = e
        except OSError as e:  # URLError, timeouts, connection resets
            last = e
    dest.unlink(missing_ok=True)
    raise ConnectionError(f"download failed after {RETRIES} tries: {url}: {last}")


def archive_url(kind: str, symbol: str, period: str, daily: bool) -> str:
    """`kind` aggTrades / fundingRate, `period` YYYY-MM or YYYY-MM-DD."""
    freq = "daily" if daily else "monthly"
    return f"{BASE_URL}/{freq}/{kind}/{symbol}/{symbol}-{kind}-{period}.zip"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(BLOCK_BYTES):
            h.update(block)
    return h.hexdigest()


def download_verified(url: str, tmp_dir: Path, fetch: Fetch) -> Path:
    """Download the zip and its .CHECKSUM, verify SHA256; on any failure delete both and raise."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / url.rsplit("/", 1)[1]
    sum_path = zip_path.with_name(zip_path.name + ".CHECKSUM")
    try:
        fetch(url, zip_path)
        fetch(url + ".CHECKSUM", sum_path)
        words = sum_path.read_text(encoding="utf-8", errors="replace").split()
        if sha256_of(zip_path) != (words[0].lower() if words else ""):
            raise ChecksumError(f"checksum mismatch: {url}")
    except BaseException:
        zip_path.unlink(missing_ok=True)
        raise
    finally:
        sum_path.unlink(missing_ok=True)
    return zip_path


def _csv_member(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if len(names) != 1:
        raise ValueError(f"expected one CSV in the zip, found {zf.namelist()}")
    return names[0]


def _has_header(zf: zipfile.ZipFile, member: str) -> bool:
    with zf.open(member) as f:
        first = f.readline().decode("utf-8", errors="replace").strip()
    return not first[:1].isdigit()


def _partial_bars(chunk: pd.DataFrame) -> pd.DataFrame:
    """One chunk of trades -> partial per-minute aggregates (mergeable across chunks)."""
    t = chunk["transact_time"].to_numpy("int64")
    if len(t) and t.max() >= MICROSECOND_LIMIT:
        t = t // 1000
    qty = chunk["quantity"].astype(float)
    buyer_maker = chunk["is_buyer_maker"].astype(str).str.lower().eq("true")
    df = pd.DataFrame(
        {
            "minute": t // MS_PER_MINUTE,
            "t": t,
            "id": chunk["agg_trade_id"].to_numpy("int64"),
            "price": chunk["price"].astype(float),
            "buy": qty.where(~buyer_maker, 0.0),
            "sell": qty.where(buyer_maker, 0.0),
            "trades": chunk["last_trade_id"].to_numpy("int64")
            - chunk["first_trade_id"].to_numpy("int64")
            + 1,
        }
    ).sort_values(["t", "id"], kind="stable")
    g = df.groupby("minute", sort=True)
    return pd.DataFrame(
        {
            "first_key": g["t"].min(), "last_key": g["t"].max(),
            "open": g["price"].first(), "high": g["price"].max(),
            "low": g["price"].min(), "close": g["price"].last(),
            "buy": g["buy"].sum(), "sell": g["sell"].sum(), "trades": g["trades"].sum(),
        }
    )  # fmt: skip


def parse_trades_zip(zip_path: Path, chunk_rows: int = CHUNK_ROWS) -> pd.DataFrame:
    """Stream the CSV of an aggTrades zip -> 1m bars (index = UTC minute open in minutes since
    epoch): open, high, low, close, buy, sell, trades. Open / close are by trade time."""
    parts: list[pd.DataFrame] = []
    with zipfile.ZipFile(zip_path) as zf:
        member = _csv_member(zf)
        skip = 1 if _has_header(zf, member) else 0
        with zf.open(member) as f:
            reader = pd.read_csv(
                f, header=None, names=list(TRADE_COLUMNS), skiprows=skip, chunksize=chunk_rows,
                dtype={"is_buyer_maker": "string", "price": "float64", "quantity": "float64"},
            )  # fmt: skip
            parts = [_partial_bars(chunk) for chunk in reader if len(chunk)]
    if not parts:
        return pd.DataFrame(columns=["open", "high", "low", "close", "buy", "sell", "trades"])
    allp = pd.concat(parts)
    by_first = allp.sort_values("first_key", kind="stable").groupby(level=0)
    by_last = allp.sort_values("last_key", kind="stable").groupby(level=0)
    g = allp.groupby(level=0)
    out = pd.DataFrame(
        {
            "open": by_first["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
            "close": by_last["close"].last(), "buy": g["buy"].sum(),
            "sell": g["sell"].sum(), "trades": g["trades"].sum(),
        }
    )  # fmt: skip
    return out.sort_index()


def _utc(minutes: pd.Index) -> pd.DatetimeIndex:
    return pd.to_datetime(minutes.to_numpy("int64") * MS_PER_MINUTE, unit="ms", utc=True)


def day_frames(bars: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Bars of one UTC day -> (cache-format frame, flow frame)."""
    if bars.empty:
        flow = pd.DataFrame({c: pd.Series(dtype="float64") for c in FLOW_COLUMNS})
        return empty_cache_frame(), flow.astype({"ts": "datetime64[ns, UTC]"})
    ts = _utc(bars.index)
    volume = (bars["buy"] + bars["sell"]).to_numpy(float)
    cache = pd.DataFrame({"ts": ts})
    for f in ("open", "high", "low", "close"):
        cache[f"bid_{f}"] = bars[f].to_numpy(float)
        cache[f"ask_{f}"] = bars[f].to_numpy(float)
    cache["bid_volume"] = volume
    cache["ask_volume"] = volume
    flow = pd.DataFrame(
        {
            "ts": ts, "volume": volume, "buy_volume": bars["buy"].to_numpy(float),
            "sell_volume": bars["sell"].to_numpy(float),
            "delta": (bars["buy"] - bars["sell"]).to_numpy(float),
            "trades": bars["trades"].to_numpy("int64"),
        }
    )  # fmt: skip
    return cache[COLUMNS], flow


@dataclass(frozen=True)
class BinanceConfig:
    cache_dir: Path = CACHE_DIR
    flow_dir: Path = FLOW_DIR
    funding_dir: Path = FUNDING_DIR
    tmp_dir: Path = TMP_DIR


def _days_done(cfg: BinanceConfig, symbol: str, days: list[date]) -> bool:
    return all(
        cache_path(cfg.cache_dir, symbol, d).exists()
        and cache_path(cfg.flow_dir, symbol, d).exists()
        for d in days
    )


def write_days(cfg: BinanceConfig, symbol: str, bars: pd.DataFrame, days: list[date]) -> int:
    """Write the cache + flow file of every day in `days`. Trades outside `days` are an
    error (a file must stay inside its period); nothing is written then."""
    by_day = pd.Series(_utc(bars.index).date, index=bars.index) if len(bars) else None
    if by_day is not None:
        stray = set(by_day.unique()) - set(days)
        if stray:
            raise ValueError(f"{symbol}: trades outside the file's period: {sorted(stray)[:3]}")
    for d in days:
        part = bars if by_day is None else bars[by_day.to_numpy() == d]
        cache, flow = day_frames(part)
        write_atomic(cache, cache_path(cfg.cache_dir, symbol, d))
        write_atomic(flow, cache_path(cfg.flow_dir, symbol, d))
    return len(bars)


def month_days(month: date) -> list[date]:
    nxt = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return [month + timedelta(days=i) for i in range((nxt - month).days)]


def _process_zip(cfg, symbol, url, days, fetch, log) -> int:
    zip_path = download_verified(url, cfg.tmp_dir, fetch)
    try:
        size = zip_path.stat().st_size
        n = write_days(cfg, symbol, parse_trades_zip(zip_path), days)
    finally:
        zip_path.unlink(missing_ok=True)
    log(f"{symbol} {days[0]}..{days[-1]}: {size / 1e6:,.1f} MB zip, {n:,} bars")
    return n


@dataclass(frozen=True)
class MonthResult:
    symbol: str
    month: date
    bars: int
    skipped: bool  # already cached
    daily: bool  # built from daily files
    missing_days: int  # daily files not published yet


def download_month(
    symbol: str, month: date, cfg: BinanceConfig, fetch: Fetch, today: date, log=lambda t: None
) -> MonthResult:
    """aggTrades of one month -> day files. The monthly zip if the month is over and it
    exists, else the daily zips of the days before `today` (UTC; today's is still growing)."""
    all_days = month_days(month)
    days = [d for d in all_days if d < today]
    if not days or _days_done(cfg, symbol, days):
        return MonthResult(symbol, month, 0, True, False, 0)
    if len(days) == len(all_days):  # month over: monthly file may exist
        url = archive_url("aggTrades", symbol, f"{month.year:04d}-{month.month:02d}", False)
        try:
            n = _process_zip(cfg, symbol, url, all_days, fetch, log)
            return MonthResult(symbol, month, n, False, False, 0)
        except NotFoundError:
            pass
    bars_n = missing = 0
    for d in days:
        if _days_done(cfg, symbol, [d]):
            continue
        url = archive_url("aggTrades", symbol, d.isoformat(), True)
        try:
            bars_n += _process_zip(cfg, symbol, url, [d], fetch, log)
        except NotFoundError:
            missing += 1
    return MonthResult(symbol, month, bars_n, False, True, missing)


def download_funding(
    symbol: str, months: list[date], cfg: BinanceConfig, fetch: Fetch, log=lambda t: None
) -> int:
    """Monthly fundingRate files -> `binance_funding/<SYM>.csv` (months already in it are
    skipped, months without a monthly file ignored). Returns the rows in the file."""
    path = cfg.funding_dir / f"{symbol}.csv"
    rows: dict[str, list[str]] = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = {r["calc_time"]: [r[h] for h in FUNDING_COLUMNS] for r in csv.DictReader(f)}
    have = {k[:7] for k in rows}
    new = False
    for m in months:
        label = f"{m.year:04d}-{m.month:02d}"
        if label in have:
            continue
        try:
            url = archive_url("fundingRate", symbol, label, False)
            zip_path = download_verified(url, cfg.tmp_dir, fetch)
        except NotFoundError:
            continue
        try:
            with zipfile.ZipFile(zip_path) as zf, zf.open(_csv_member(zf)) as raw:
                for r in csv.reader(line.decode("utf-8") for line in raw):
                    if not r or not r[0][:1].isdigit():
                        continue  # header
                    stamp = datetime.fromtimestamp(int(r[0]) / 1000, UTC).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    rows[stamp] = [stamp, r[1], r[2]]
                    new = True
        finally:
            zip_path.unlink(missing_ok=True)
        log(f"{symbol} funding {label}")
    if new or not path.exists():
        cfg.funding_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".csv.tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(FUNDING_COLUMNS)
            w.writerows(rows[k] for k in sorted(rows))
        tmp.replace(path)
    return len(rows)


def months_between(start: date, end: date) -> list[date]:
    out, m = [], start.replace(day=1)
    while m <= end:
        out.append(m)
        m = (m + timedelta(days=32)).replace(day=1)
    return out


def download_symbol(
    symbol: str, start: date, end: date, cfg: BinanceConfig | None = None,
    fetch: Fetch = http_fetch, today: date | None = None, log=lambda t: None,
) -> list[MonthResult]:  # fmt: skip
    cfg = cfg or BinanceConfig()
    today = today or datetime.now(UTC).date()
    months = months_between(start, end)
    results = [download_month(symbol, m, cfg, fetch, today, log) for m in months]
    download_funding(symbol, months, cfg, fetch, log)
    return results
