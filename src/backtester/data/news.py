"""Economic schedule primitives. Spec: docs/news.md.

Schedule objects deliberately have no retrospective result fields.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import math
import warnings
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ImpactWindow:
    before_minutes: float = 0.0
    after_minutes: float = 0.0

    def __post_init__(self) -> None:
        if any(not math.isfinite(v) or v < 0 for v in (self.before_minutes, self.after_minutes)):
            raise ValueError("news windows must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class InstrumentNews:
    currencies: str = ""  # comma-separated currency codes
    countries: str = ""  # comma-separated country codes, used only without a currency
    include_global: bool = False


def _instruments() -> dict[str, InstrumentNews]:
    out = {}
    countries = {
        "USD": "US",
        "EUR": "EU",
        "GBP": "GB",
        "JPY": "JP",
        "CHF": "CH",
        "AUD": "AU",
        "CAD": "CA",
        "NZD": "NZ",
    }
    for symbol in (
        "EURUSD",
        "GBPUSD",
        "GBPJPY",
        "USDJPY",
        "USDCHF",
        "USDCAD",
        "AUDUSD",
        "NZDUSD",
        "EURGBP",
        "EURJPY",
        "AUDJPY",
        "CADJPY",
        "CHFJPY",
    ):
        currencies = (symbol[:3], symbol[3:])
        out[symbol] = InstrumentNews(
            ",".join(currencies), ",".join(countries[c] for c in currencies)
        )
    for symbol in ("XAUUSD", "XAGUSD", "NAS100", "US500", "US30", "US2000", "BTCUSD", "ETHUSD"):
        out[symbol] = InstrumentNews("USD", "US")
    out["GER40"] = InstrumentNews("EUR", "DE,EU")
    return out


@dataclass(frozen=True, slots=True)
class NewsConfig:
    path: str = "data/news/economic_events.csv"
    enabled: bool = False
    policy: str = "block_entries"  # or flag_only
    uncertain_policy: str = "block_day"  # or skip (loader reports counted warnings)
    high: ImpactWindow = field(default_factory=ImpactWindow)
    medium: ImpactWindow = field(default_factory=ImpactWindow)
    publication_delay_seconds: float = 0.0
    quality_errors: bool = False
    separate_source_periods: bool = True
    source_boundaries: str = "2025-10-24"  # comma-separated UTC coverage-change dates
    instruments: Mapping[str, InstrumentNews] = field(default_factory=_instruments)

    def __post_init__(self) -> None:
        if self.policy not in ("block_entries", "flag_only"):
            raise ValueError("news policy must be block_entries or flag_only")
        if self.uncertain_policy not in ("block_day", "skip"):
            raise ValueError("uncertain news policy must be block_day or skip")
        if not math.isfinite(self.publication_delay_seconds) or self.publication_delay_seconds < 0:
            raise ValueError("publication delay must be finite and nonnegative")
        # Own the mapping so mutating the caller's input cannot alter an existing config.
        object.__setattr__(self, "instruments", MappingProxyType(dict(self.instruments)))


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    event_id: str
    scheduled_at: datetime | None
    day: date | None
    window_start: datetime | None
    window_end: datetime | None
    time_precision: str
    currency: str
    country: str
    impact: str
    name: str
    source_provider: str


@dataclass(frozen=True, slots=True)
class Calendar:
    events: tuple[ScheduleEvent, ...]
    sha256: str
    coverage_start: date
    coverage_end: date
    high_counts: tuple[tuple[str, int, int], ...] = ()
    quality_counts: tuple[tuple[str, int], ...] = ()


def _utc(at: datetime) -> datetime:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("news timestamps must be timezone-aware")
    return at.astimezone(UTC)


class EventResults:
    """Separate, unwired result accessor. Spec: news.md > Schedule and results.

    Only source strings are returned; forecasts and previous values are never exposed.
    """

    def __init__(self, schedule: Calendar, actuals: Mapping[str, str | None]):
        self._releases = {e.event_id: e.scheduled_at for e in schedule.events}
        self._actuals = dict(actuals)

    @classmethod
    def from_csv(cls, path: str | Path) -> EventResults:
        """Explicit result-only loading; never used by strategies or the runner."""
        calendar, actuals = _parse_csv(Path(path).read_bytes(), NewsConfig(path=str(path)))
        return cls(calendar, actuals)

    def actual(self, event_id: str, now: datetime, delay: timedelta) -> str | None:
        now = _utc(now)
        if delay < timedelta(0):
            raise ValueError("publication delay must be nonnegative")
        release = self._releases.get(event_id)
        if release is None or now < _utc(release) + delay:
            return None
        return self._actuals.get(event_id)


def _codes(values: str) -> set[str]:
    return {v.strip().upper() for v in values.split(",") if v.strip()}


def relevant(event: ScheduleEvent, instrument: str, config: NewsConfig) -> bool:
    """Currency takes precedence; country is a fallback. GLOBAL is explicitly opt-in."""
    mapping = config.instruments.get(instrument.upper())
    if mapping is None:
        return False
    currency, country = event.currency.strip().upper(), event.country.strip().upper()
    if currency == "GLOBAL" or (currency in ("", "ALL") and country == "GLOBAL"):
        return mapping.include_global
    return (
        currency in _codes(mapping.currencies) if currency else country in _codes(mapping.countries)
    )


def matching_events(
    t: datetime, instrument: str, calendar: Calendar | None, config: NewsConfig
) -> tuple[ScheduleEvent, ...]:
    """Pure risk-window query, retaining simultaneous events. Spec: news.md > Windows."""
    now = _utc(t)
    if not config.enabled or calendar is None:
        return ()
    matches = []
    for event in calendar.events:
        if not relevant(event, instrument, config):
            continue
        if event.time_precision in ("minute", "second"):
            if event.scheduled_at is None:
                raise ValueError("exact news event needs a release timestamp")
            window = config.high if event.impact == "High" else config.medium
            release = _utc(event.scheduled_at)
            inside = (
                release - timedelta(minutes=window.before_minutes)
                <= now
                <= release + timedelta(minutes=window.after_minutes)
            )
        elif config.uncertain_policy == "skip":
            inside = False
        elif event.time_precision == "range":
            if event.window_start is None or event.window_end is None:
                raise ValueError("range news event needs both window ends")
            inside = _utc(event.window_start).date() <= now.date() <= _utc(event.window_end).date()
        else:
            inside = event.day == now.date()
        if inside:
            matches.append(event)
    return tuple(matches)


def blocked(t: datetime, instrument: str, calendar: Calendar | None, config: NewsConfig) -> bool:
    """Pure entry-block decision; inclusive endpoints. Spec: news.md > Windows."""
    return (
        bool(matching_events(t, instrument, calendar, config)) and config.policy == "block_entries"
    )


CSV_COLUMNS = [
    "event_id",
    "scheduled_timestamp_utc",
    "scheduled_date_utc",
    "scheduled_date_local",
    "source_timezone",
    "time_precision",
    "time_label",
    "time_window_start_utc",
    "time_window_end_utc",
    "currency",
    "country",
    "impact",
    "impact_rank",
    "event_name",
    "actual",
    "forecast",
    "previous",
    "status",
    "source_provider",
    "source_name",
    "source_url",
    "source_record_id",
    "source_retrieved_at_utc",
    "source_updated_at_utc",
    "known_at_utc",
    "point_in_time_verified",
    "point_in_time_note",
    "provenance_quality",
    "dedupe_key",
]


def _timestamp(value: str) -> datetime | None:
    return _utc(datetime.fromisoformat(value)) if value else None


def _date(value: str) -> date | None:
    return date.fromisoformat(value) if value else None


def load_calendar(config: NewsConfig) -> Calendar | None:
    """Read one immutable CSV snapshot. Spec: news.md > CSV validation.

    Missing files disable the feature; invalid existing files fail instead of disabling it.
    SHA256 covers the identical bytes parsed, including the optional UTF-8 BOM.
    """
    from backtester.paths import HOME_DIR

    path = Path(config.path)
    if not path.is_absolute():
        path = HOME_DIR / path
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        logging.getLogger(__name__).warning("no calendar: %s", path)
        return None
    calendar, _ = _parse_csv(content, config)
    return calendar


def _parse_csv(content: bytes, config: NewsConfig) -> tuple[Calendar, dict[str, str | None]]:
    reader = csv.reader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
    if next(reader, None) != CSV_COLUMNS:
        raise ValueError("news CSV header must match the explicit ordered 29-column schema")
    events, actuals, days = [], {}, []
    identities, dedupes = set(), set()
    quality = Counter()
    high = Counter()
    source_days = []
    for number, values in enumerate(reader, 2):
        if not values:
            continue
        if len(values) != len(CSV_COLUMNS):
            raise ValueError(f"news row {number}: expected 29 columns")
        row = dict(zip(CSV_COLUMNS, values, strict=True))
        try:
            event_id, key = row["event_id"], row["dedupe_key"]
            for name, value, seen in (
                ("event_id", event_id, identities),
                ("dedupe_key", key, dedupes),
            ):
                if not value.strip() or value in seen:
                    raise ValueError(f"empty or duplicate {name}")
                seen.add(value)
            impact, precision = row["impact"], row["time_precision"]
            if impact not in ("High", "Medium"):
                raise ValueError("impact must be High or Medium")
            if row["impact_rank"] != ("3" if impact == "High" else "2"):
                raise ValueError("impact_rank disagrees with impact")
            if precision not in ("second", "minute", "date", "range", "unknown"):
                raise ValueError("invalid time_precision")
            if row["point_in_time_verified"] not in ("true", "false"):
                raise ValueError("point_in_time_verified must be true or false")
            release = _timestamp(row["scheduled_timestamp_utc"])
            start = _timestamp(row["time_window_start_utc"])
            end = _timestamp(row["time_window_end_utc"])
            for column in ("source_retrieved_at_utc", "source_updated_at_utc", "known_at_utc"):
                _timestamp(row[column])
            utc_day = _date(row["scheduled_date_utc"])
            local_day = _date(row["scheduled_date_local"])
            exact = precision in ("minute", "second")
            if exact and release is None:
                raise ValueError("exact row requires scheduled_timestamp_utc")
            if not exact and release is not None:
                raise ValueError("nonexact row must keep scheduled_timestamp_utc blank")
            if release and utc_day and release.date() != utc_day:
                raise ValueError("scheduled_date_utc disagrees with timestamp")
            if precision == "range" and (start is None or end is None or start > end):
                raise ValueError("range requires both ordered window ends")
            day = release.date() if release else utc_day or local_day
            if day is None and start is None:
                raise ValueError("row needs a represented date")
            event = ScheduleEvent(
                event_id,
                release,
                day,
                start,
                end,
                precision,
                row["currency"],
                row["country"],
                impact,
                row["event_name"],
                row["source_provider"],
            )
            events.append(event)
            actuals[event_id] = row["actual"] or None
            represented = [
                d for d in (day, start.date() if start else None, end.date() if end else None) if d
            ]
            days.extend(represented)
            source_days.append((min(represented), row["source_provider"]))
            if exact and row["time_label"] in ("00:00:00", "23:59:59"):
                quality["suspicious_exact"] += 1
            # A blank UTC date is deliberately not fabricated from a local date.
            weekend_day = (
                release.date() if release else utc_day or (start.date() if start else None)
            )
            if weekend_day is not None and weekend_day.weekday() >= 5:
                quality["weekend"] += 1
            if impact == "High":
                high[row["source_provider"], min(represented).year] += 1
            if not exact and config.uncertain_policy == "skip":
                quality["uncertain_skipped"] += 1
        except ValueError as exc:
            raise ValueError(f"news row {number}: {exc}") from exc
    for boundary in sorted(
        {_date(v.strip()) for v in config.source_boundaries.split(",") if v.strip()}
    ):
        before = {s for d, s in source_days if d < boundary}
        after = {s for d, s in source_days if d >= boundary}
        if before and after and before != after:
            quality["source_boundary_changes"] += 1
    for name, count in sorted(quality.items()):
        message = f"news quality: {name}={count}"
        if config.quality_errors:
            raise ValueError(message)
        warnings.warn(message, UserWarning, stacklevel=3)
    if not events:
        raise ValueError("news calendar contains no events")
    calendar = Calendar(
        tuple(events),
        hashlib.sha256(content).hexdigest(),
        min(days),
        max(days),
        tuple((source, year, n) for (source, year), n in sorted(high.items())),
        tuple(sorted(quality.items())),
    )
    return calendar, actuals
