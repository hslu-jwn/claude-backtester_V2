"""Calendar-month walk-forward, with the original yearly API retained for compatibility.

Pure and generic: input is a trade list per variant, output the pick per window and
the chained out-of-sample trades. Anchored training grows; rolling training has a
fixed length. Pick maximum training net R, using only already closed outcomes;
ties keep input variant order. Explicit year bounds retain the original API.

Spec: research-runner.md > Walk-forward (V2.4d item 6).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

ANCHORED, ROLLING = "anchored", "rolling"


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    mode: str = ANCHORED  # "anchored" or "rolling"
    train_years: int | None = None  # legacy yearly API only
    min_train_years: int | None = None  # legacy yearly API only
    train_months: int = 24
    test_months: int = 6
    step_months: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in (ANCHORED, ROLLING):
            raise ValueError("mode must be 'anchored' or 'rolling'")
        if self.step_months is None:
            object.__setattr__(self, "step_months", self.test_months)
        for name in (
            "train_months",
            "test_months",
            "step_months",
            "train_years",
            "min_train_years",
        ):
            value = getattr(self, name)
            if value is None and name in ("train_years", "min_train_years"):
                continue
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.step_months < self.test_months:
            raise ValueError("step_months must be >= test_months (overlap double counts trades)")


@dataclass(frozen=True, slots=True)
class YearPick:
    year: int  # the test year
    variant: str  # chosen on the train years
    train_net: float  # its net R over the train years
    train_years: tuple[int, ...]
    test_trades: tuple  # the chosen variant's trades entered in the test year


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    picks: tuple[YearPick | WindowPick, ...]
    reason: str | None = None

    @property
    def chained(self) -> tuple:
        """The out-of-sample trades: every test year's trades of its chosen variant."""
        return tuple(t for p in self.picks for t in p.test_trades)


def _net(trades: Sequence, years: set[int], test_year: int) -> float:
    # Entry-only historical inputs represent outcomes realized at entry. Real trade
    # records carry exit_time and must have closed strictly before the test year.
    return sum(
        t.r_net
        for t in trades
        if t.entry_time.year in years
        and getattr(t, "exit_time", t.entry_time) < datetime(test_year, 1, 1, tzinfo=UTC)
    )


def _yearly_walk_forward(
    variants: Mapping[str, Sequence],
    config: WalkForwardConfig | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
) -> WalkForwardResult:
    """Pick per test year. `first_year` / `last_year` default to the first / last entry year over
    all variants; years in between without trades still count (net 0)."""
    if not variants:
        raise ValueError("at least one variant is needed")
    cfg = config or WalkForwardConfig()
    years = [t.entry_time.year for trades in variants.values() for t in trades]
    if not years and first_year is None:
        return WalkForwardResult(())
    first = first_year if first_year is not None else min(years)
    last = last_year if last_year is not None else max(years)
    picks = []
    minimum = cfg.min_train_years or 1
    for test in range(first + minimum, last + 1):
        lo = first if cfg.mode == ANCHORED else max(first, test - (cfg.train_years or 3))
        train = tuple(range(lo, test))
        if len(train) < minimum:
            continue
        train_set = set(train)
        best_name, best_net = None, 0.0
        for name, trades in variants.items():
            net = _net(trades, train_set, test)
            if best_name is None or net > best_net:  # strict: a tie keeps the first
                best_name, best_net = name, net
        chosen = tuple(t for t in variants[best_name] if t.entry_time.year == test)
        picks.append(YearPick(test, best_name, best_net, train, chosen))
    return WalkForwardResult(tuple(picks))


def add_months(start: datetime, months: int) -> datetime:
    """Shift a first-of-month UTC boundary by whole calendar months."""
    year, month = divmod(start.year * 12 + start.month - 1 + months, 12)
    return datetime(year, month + 1, 1, tzinfo=UTC)


def calendar_months(start: datetime, end: datetime) -> float:
    """Whole months plus actual elapsed fraction of the final calendar month."""
    months = (end.year - start.year) * 12 + end.month - start.month
    boundary = add_months(start, months)
    return months + (end - boundary) / (add_months(boundary, 1) - boundary)


@dataclass(frozen=True, slots=True)
class WindowPick:
    window: int
    variant: str
    train_net: float
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    test_trades: tuple

    @property
    def train_months(self) -> float:
        return calendar_months(self.train_start, self.train_end)

    @property
    def test_months(self) -> float:
        return calendar_months(self.test_start, self.test_end)


def walk_forward(
    variants: Mapping[str, Sequence],
    config: WalkForwardConfig | None = None,
    first_year: int | None = None,
    last_year: int | None = None,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
) -> WalkForwardResult:
    """Spec: research-runner.md > Walk-forward. Month bounds are [start, end).

    Explicit year bounds, legacy config fields, or an unconfigured call retain
    the yearly API. Month calls infer missing bounds from entry months.
    """
    if not variants:
        raise ValueError("at least one variant is needed")
    cfg = config or WalkForwardConfig()
    legacy = (
        first_year is not None
        or last_year is not None
        or cfg.train_years is not None
        or cfg.min_train_years is not None
        or (config is None and start is None and end is None)
    )
    if legacy:
        if start is not None or end is not None:
            raise ValueError("do not combine year and month bounds")
        return _yearly_walk_forward(variants, cfg, first_year, last_year)
    entries = [t.entry_time.astimezone(UTC) for ts in variants.values() for t in ts]
    if not entries and (start is None or end is None):
        return WalkForwardResult((), "No entry dates to infer the development period.")
    start = start or min(entries).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = end or add_months(max(entries).replace(day=1), 1)
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("development bounds must be timezone-aware")
    start, end = start.astimezone(UTC), end.astimezone(UTC)
    first = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if first < start:
        first = add_months(first, 1)
    test = add_months(first, cfg.train_months)
    picks = []
    while test < end:
        lo = first if cfg.mode == ANCHORED else add_months(test, -cfg.train_months)
        stop = min(add_months(test, cfg.test_months), end)
        nets = {
            name: sum(
                t.r_net
                for t in ts
                if lo <= t.entry_time < test and getattr(t, "exit_time", t.entry_time) < test
            )
            for name, ts in variants.items()
        }
        best = max(nets, key=nets.get)  # stable input order for ties, including empty variants
        chosen = tuple(
            sorted(
                (t for t in variants[best] if test <= t.entry_time < stop),
                key=lambda t: t.entry_time,
            )
        )
        picks.append(WindowPick(len(picks) + 1, best, nets[best], lo, test, test, stop, chosen))
        test = add_months(test, cfg.step_months)
    return WalkForwardResult(
        tuple(picks),
        None
        if picks
        else "No OOS windows: development period is too short after full-month alignment.",
    )
