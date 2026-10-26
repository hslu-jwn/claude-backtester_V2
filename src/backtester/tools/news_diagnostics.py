"""Descriptive economic-calendar splits. Spec: docs/news.md > Research split.

This pure reporter requires an explicitly supplied schedule and never reads calendar files.
"""

from __future__ import annotations

import json
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, date

from backtester.data import news
from backtester.data.news import Calendar, NewsConfig, relevant


def news_split(trades, calendar: Calendar | None, config: NewsConfig) -> list[dict]:
    """Classify entry UTC days/minutes; retain precoverage trades as no_calendar.

    Exact events mark their release minute, independently of execution blackout settings.
    Nonexact events mark days only; minutes on those days are uncertain, never news-free.
    """
    if calendar is None:
        return []
    boundaries = (
        sorted(
            date.fromisoformat(s.strip()) for s in config.source_boundaries.split(",") if s.strip()
        )
        if config.separate_source_periods
        else []
    )
    grouped = defaultdict(list)
    indices = {}
    for trade in trades:
        if trade.entry_time.tzinfo is None or trade.entry_time.utcoffset() is None:
            raise ValueError("trade entry time must be timezone-aware")
        at = trade.entry_time.astimezone(UTC)
        day = at.date()
        minute = at.replace(second=0, microsecond=0)
        covered = max(date(2020, 1, 2), calendar.coverage_start) <= day <= calendar.coverage_end
        if trade.symbol not in indices:
            exact_days, exact_minutes, uncertain = set(), set(), []
            for event in calendar.events:
                if event.impact != "High" or not relevant(event, trade.symbol, config):
                    continue
                if event.time_precision in ("minute", "second") and event.scheduled_at:
                    release = event.scheduled_at.astimezone(UTC)
                    exact_days.add(release.date())
                    exact_minutes.add(release.replace(second=0, microsecond=0))
                elif event.time_precision == "range" and event.window_start and event.window_end:
                    uncertain.append(
                        (
                            event.window_start.astimezone(UTC).date(),
                            event.window_end.astimezone(UTC).date(),
                        )
                    )
                elif event.day:
                    uncertain.append((event.day, event.day))
            indices[trade.symbol] = exact_days, exact_minutes, uncertain
        days, minutes, uncertain = indices[trade.symbol]
        unknown_minute = any(start <= day <= end for start, end in uncertain)
        period_index = sum(day >= boundary for boundary in boundaries)
        lower = boundaries[period_index - 1].isoformat() if period_index else "start"
        upper = boundaries[period_index].isoformat() if period_index < len(boundaries) else "end"
        source_period = f"{lower}/{upper}" if covered else "no_calendar"
        for dimension, bucket in (
            ("day", "news" if day in days or unknown_minute else "news_free"),
            (
                "minute",
                "news" if minute in minutes else "uncertain" if unknown_minute else "news_free",
            ),
        ):
            grouped[
                trade.symbol, source_period, dimension, bucket if covered else "no_calendar"
            ].append(trade.r_net)
    return [
        {
            "symbol": symbol,
            "source_period": period,
            "dimension": dimension,
            "bucket": bucket,
            "trades": len(values),
            "net_r": sum(values),
            "calendar_sha256": calendar.sha256,
        }
        for (symbol, period, dimension, bucket), values in sorted(grouped.items())
    ]


class ResearchCalendars:
    """One schedule snapshot per configured calendar, isolated to a research invocation.

    Spec: news.md > Research split. Result accessors are never constructed here.
    """

    def __init__(self, settings):
        self.calendars = {}
        self.metadata = {}
        for item in settings:
            config = item.engine.news
            key = self.key(config)
            if key in self.calendars:
                continue
            calendar = news.load_calendar(config)
            self.calendars[key] = calendar
            self.metadata[key] = {
                "path": config.path,
                "status": "loaded" if calendar else "no calendar",
                "sha256": calendar.sha256 if calendar else None,
                "coverage_start": calendar.coverage_start.isoformat() if calendar else None,
                "coverage_end": calendar.coverage_end.isoformat() if calendar else None,
                "high_counts": calendar.high_counts if calendar else (),
                "quality_counts": calendar.quality_counts if calendar else (),
            }

    @staticmethod
    def key(config):
        return (
            config.path,
            config.quality_errors,
            config.uncertain_policy,
            config.source_boundaries,
        )

    def digest(self, config):
        calendar = self.calendars[self.key(config)]
        return calendar.sha256 if calendar else None

    def manifest(self):
        # JSON round trip makes tuple/list equality stable on resume.
        return json.loads(json.dumps(list(self.metadata.values())))

    def verify(self, folder):
        path = folder / "research.json"
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            previous = old.get("news_calendars")
            if previous is not None and previous != self.manifest():
                raise ValueError(
                    "news calendar changed since the saved research run; use a new grid name"
                )
            # Legacy results were produced without any calendar execution filter.
            if previous is None and any(c is not None for c in self.calendars.values()):
                raise ValueError(
                    "news calendar changed from an unversioned saved run; use a new grid name"
                )

    def write_run(self, folder, config, trades):
        calendar = self.calendars[self.key(config)]
        data = {**self.metadata[self.key(config)], "rows": news_split(trades, calendar, config)}
        (folder / "news.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        settings_path = folder / "settings.json"
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["calendar_sha256"] = self.digest(config)
            settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


_active: ContextVar[ResearchCalendars | None] = ContextVar("research_news", default=None)


@contextmanager
def research_calendars(settings, folder):
    calendars = ResearchCalendars(settings)
    calendars.verify(folder)
    token = _active.set(calendars)
    try:
        yield calendars
    finally:
        _active.reset(token)


def active_calendars():
    return _active.get()


def write_research(folder, variants, info, results_dir):
    """Combine every variant and saved test without reinterpreting another CSV version."""
    from backtester.tools.research_diagnostics import write_csv

    records = [("development", 0, v.id, folder / "variants" / v.id) for v in variants]
    test_path = folder / "test.csv"
    if test_path.exists():
        import csv

        with test_path.open(encoding="utf-8", newline="") as stream:
            records.extend(
                ("test", int(r["test_run"]), r["variant_id"], results_dir / r["run_folder"])
                for r in csv.DictReader(stream)
            )
    rows = []
    for period, number, variant_id, run_folder in records:
        path = run_folder / "news.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.extend(
                {"period": period, "test_run": number, "variant_id": variant_id, **r}
                for r in data["rows"]
            )
    enabled = any(m["sha256"] for m in info.get("news_calendars", []))
    info["news"] = rows if enabled else None
    if enabled:
        write_csv(
            folder / "news.csv",
            rows,
            ("period", "test_run", "variant_id", "bucket", "calendar_sha256"),
        )
    else:
        (folder / "news.csv").unlink(missing_ok=True)


def markdown(info):
    lines = ["", "## Economic calendar", ""]
    for item in info.get("news_calendars", []):
        lines.append(f"- {item['path']}: {item['status']}; SHA256 {item['sha256'] or 'none'}.")
        for source, year, count in item["high_counts"]:
            lines.append(f"- High events: {source}, {year}: {count}.")
    if info.get("news") is None:
        lines.append("News split disabled (no calendar).")
    else:
        lines.append(
            "Per-variant day/minute counts and net R, including no_calendar, are in `news.csv`."
        )
    return lines
