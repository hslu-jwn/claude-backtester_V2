"""Seeded random-walk M1 candles with a symbol's real volatility profile.

Spec: risk-management.md > Monte Carlo report > D (random price paths): a strategy with no
edge must lose about the mean cost per trade on such paths; an "edge" that survives on them
is an artifact of the code or the costs.

`VolatilityProfile.from_candles` measures, from real M1 candles (cache layout, bid columns),
per UTC hour of day: the st.dev of the M1 log return and the mean wick (share of price);
which minutes of the week have candles at all (weekday x minute of day, so indices keep their
trading hours and weekends stay empty); the st.dev of the jump across a trading break (gap,
per hour of the first candle after it); and the starting price.
`generate_frame` draws one path: zero drift, normal returns, exponential wicks, open =
previous close inside a session. `write_path` stores it in the normal Parquet day layout
(`data/cache.py`, bid only, volume and ask NaN, exactly like a histdata.com cache), so
`SymbolSources` and the runner read it without knowing it is synthetic.

Simplification: sigma is per UTC hour, so after a DST change the US open moves one hour
against the profile; fine for a no-edge control.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data.adapters.cache_adapter import cached_days
from backtester.data.cache import (
    COLUMNS,
    cache_path,
    empty_cache_frame,
    read_cached_days,
    write_atomic,
)
from backtester.data.resample import drop_flat_minutes
from backtester.data.sources import PRICE_DIGITS, SymbolSources

MINUTES_PER_DAY = 1440
HOURS = 24
WEEKDAYS = 7


@dataclass(frozen=True)
class RandomWalkConfig:
    paths: int = 20  # random paths per symbol (spec D)
    years: int = 2  # length of each path (spec D)
    seed: int = 42
    start: date = date(2024, 1, 1)  # first day of every path (a Monday)
    break_minutes: int = 5  # a gap of more than this many minutes between candles is a break
    min_presence: float = 0.05  # (weekday, minute) with candles on fewer days has none
    min_break_samples: int = 20  # breaks per hour needed for an own gap st.dev, else pooled

    @property
    def end(self) -> date:
        """Last day (inclusive) of a path."""
        return self.start.replace(year=self.start.year + self.years) - timedelta(days=1)


DEFAULT_CONFIG = RandomWalkConfig()


@dataclass(frozen=True)
class VolatilityProfile:
    start_price: float
    digits: int
    sigma: tuple[float, ...]  # 24, st.dev of the M1 log return by UTC hour
    wick: tuple[float, ...]  # 24, mean wick (one side) as share of price by UTC hour
    break_sigma: tuple[float, ...]  # 24, st.dev of the log jump over a break, by resume hour
    presence: tuple[tuple[float, ...], ...]  # 7 x 1440, share of days with a candle (Mon = 0)

    @classmethod
    def from_candles(
        cls, m1: pd.DataFrame, digits: int, config: RandomWalkConfig = DEFAULT_CONFIG
    ) -> VolatilityProfile:
        """Measure the profile from cache-layout M1 candles (bid columns, `ts` UTC)."""
        m1 = drop_flat_minutes(m1).sort_values("ts").reset_index(drop=True)
        if len(m1) < 2:
            raise ValueError("need at least two candles to measure a volatility profile")
        ts = m1["ts"]
        o, h, lo, c = (m1[f"bid_{k}"].to_numpy(float) for k in ("open", "high", "low", "close"))
        hour = ts.dt.hour.to_numpy()
        gap_min = ts.diff().dt.total_seconds().to_numpy() / 60.0
        sigma = _by_hour(np.log(c / o), hour, gap_min == 1.0, np.std)
        wicks = ((h - np.maximum(o, c)) + (np.minimum(o, c) - lo)) / 2.0 / c
        wick = _by_hour(wicks, hour, np.ones(len(c), bool), np.mean)
        jump = np.log(o / np.concatenate([[np.nan], c[:-1]]))
        brk = gap_min > config.break_minutes
        pooled = float(np.std(jump[brk])) if brk.any() else 0.0
        break_sigma = tuple(
            float(np.std(jump[brk & (hour == hr)]))
            if (brk & (hour == hr)).sum() >= config.min_break_samples
            else pooled
            for hr in range(HOURS)
        )
        days = pd.date_range(ts.iloc[0].date(), ts.iloc[-1].date(), freq="D")
        per_weekday = np.bincount(days.weekday, minlength=WEEKDAYS).astype(float)
        counts = np.zeros((WEEKDAYS, MINUTES_PER_DAY))
        minute = (ts.dt.hour * 60 + ts.dt.minute).to_numpy()
        np.add.at(counts, (ts.dt.weekday.to_numpy(), minute), 1.0)
        presence = counts / np.maximum(per_weekday, 1.0)[:, None]
        presence[presence < config.min_presence] = 0.0
        return cls(
            start_price=float(c[-1]),
            digits=digits,
            sigma=tuple(sigma),
            wick=tuple(wick),
            break_sigma=break_sigma,
            presence=tuple(tuple(row) for row in presence),
        )


def _by_hour(values, hour, mask, fn) -> list[float]:
    out = []
    for hr in range(HOURS):
        sel = values[mask & (hour == hr)]
        out.append(float(fn(sel)) if len(sel) > 1 else 0.0)
    return out


def load_profile(
    symbol: str,
    cache_dir: Path,
    start: date,
    end: date,
    digits: int | None = None,
    config: RandomWalkConfig = DEFAULT_CONFIG,
) -> VolatilityProfile:
    """Profile of `symbol` measured on the cached days [start, end] of `cache_dir`."""
    days = [d for d in cached_days(symbol, cache_dir) if start <= d <= end]
    if not days:
        raise ValueError(f"{symbol}: no cached day between {start} and {end} in {cache_dir}")
    frame = read_cached_days([cache_path(cache_dir, symbol, d) for d in days])
    return VolatilityProfile.from_candles(
        frame, PRICE_DIGITS[symbol] if digits is None else digits, config
    )


def generate_frame(
    profile: VolatilityProfile,
    symbol: str,
    path_index: int,
    config: RandomWalkConfig = DEFAULT_CONFIG,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """One random path as a cache-layout M1 frame (days [start, end], UTC). Same seed,
    symbol and path index give the same candles; another path index gives other prices."""
    start, end = start or config.start, end or config.end
    rng = np.random.default_rng([config.seed, path_index, zlib.crc32(symbol.encode())])
    first = datetime.combine(start, datetime.min.time(), UTC)
    n = ((end - start).days + 1) * MINUTES_PER_DAY
    grid = pd.date_range(first, periods=n, freq="min", tz=UTC)
    presence = np.array(profile.presence)
    p = presence[grid.weekday.to_numpy(), (grid.hour * 60 + grid.minute).to_numpy()]
    present = (p > 0) & (rng.random(n) < p)
    ts = grid[present]
    m = len(ts)
    if m == 0:
        return empty_cache_frame()
    hour = ts.hour.to_numpy()
    gap_min = np.concatenate(
        [
            [np.inf],
            np.diff(ts.tz_convert(None).to_numpy().astype("datetime64[s]").astype(np.int64)) / 60.0,
        ]
    )
    is_break = gap_min > config.break_minutes
    body = rng.standard_normal(m) * np.array(profile.sigma)[hour]
    jump = rng.standard_normal(m) * np.array(profile.break_sigma)[hour] * is_break
    jump[0] = 0.0  # open = previous close inside a session; a jump only across a break
    log_close = np.cumsum(jump + body)
    log_open = log_close - body
    wick = np.array(profile.wick)[hour]
    c = np.round(profile.start_price * np.exp(log_close), profile.digits)
    o = np.round(profile.start_price * np.exp(log_open), profile.digits)
    up = rng.exponential(1.0, m) * wick * c
    dn = rng.exponential(1.0, m) * wick * c
    h = np.maximum(np.round(np.maximum(o, c) + up, profile.digits), np.maximum(o, c))
    lo = np.minimum(np.round(np.minimum(o, c) - dn, profile.digits), np.minimum(o, c))
    frame = pd.DataFrame({"ts": ts, "bid_open": o, "bid_high": h, "bid_low": lo, "bid_close": c})
    for col in COLUMNS[1:]:
        if col not in frame:
            frame[col] = np.nan  # histdata.com layout: no ask, no volume
    return frame[COLUMNS]


def write_path(
    profile: VolatilityProfile,
    symbol: str,
    path_index: int,
    cache_dir: Path,
    config: RandomWalkConfig = DEFAULT_CONFIG,
    start: date | None = None,
    end: date | None = None,
) -> SymbolSources:
    """Write path `path_index` as Parquet day files under `cache_dir` and return the
    `SymbolSources` reading it. Empty days (weekends) are cached as empty files."""
    start, end = start or config.start, end or config.end
    frame = generate_frame(profile, symbol, path_index, config, start, end)
    groups = dict(tuple(frame.groupby(frame["ts"].dt.date))) if len(frame) else {}
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        part = groups[day].reset_index(drop=True) if day in groups else empty_cache_frame()
        write_atomic(part, cache_path(cache_dir, symbol, day))
    return SymbolSources.single(cache_dir, [symbol])
