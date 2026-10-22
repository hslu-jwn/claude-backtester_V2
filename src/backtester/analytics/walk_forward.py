"""Walk-forward splitter: each test year trades the variant that was best on the years before.

Pure and generic: input is a trade list per variant (any object with `entry_time` and `r_net`),
output the pick per test year and the chained out-of-sample trade list. Windows are yearly,
anchored (train = every year from the first one up to the year before the test year) or rolling
(train = the last `train_years` years). The pick is the variant with the highest net R over the
train years (ranking rule of ROADMAP 6.1: max net R); a tie goes to the first variant in the input
order. Nothing from the test year or later enters the pick.

Spec: ROADMAP 12.3 (splitter) and 11.7 (first user).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

ANCHORED, ROLLING = "anchored", "rolling"


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    mode: str = ANCHORED  # "anchored" or "rolling"
    train_years: int = 3  # rolling only: window length in years
    min_train_years: int = 1  # a test year needs at least this many train years

    def __post_init__(self) -> None:
        if self.mode not in (ANCHORED, ROLLING):
            raise ValueError("mode must be 'anchored' or 'rolling'")
        if self.min_train_years < 1:
            raise ValueError("min_train_years must be >= 1")
        if self.mode == ROLLING and self.train_years < 1:
            raise ValueError("train_years must be >= 1")


@dataclass(frozen=True, slots=True)
class YearPick:
    year: int  # the test year
    variant: str  # chosen on the train years
    train_net: float  # its net R over the train years
    train_years: tuple[int, ...]
    test_trades: tuple  # the chosen variant's trades entered in the test year


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    picks: tuple[YearPick, ...]

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


def walk_forward(
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
    for test in range(first + cfg.min_train_years, last + 1):
        lo = first if cfg.mode == ANCHORED else max(first, test - cfg.train_years)
        train = tuple(range(lo, test))
        if len(train) < cfg.min_train_years:
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
