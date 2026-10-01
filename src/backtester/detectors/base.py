"""Common interface for all detectors.

Contract (see CLAUDE.md › Invariant #1):
- `update(view)` is called exactly once per newly closed candle, in time order.
- It may only read `view` (candles 0..cursor) and its own internal state.
- It returns the events CONFIRMED by `view.current`; it never edits past events.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from backtester.core.series import SeriesView


@dataclass(frozen=True, slots=True)
class Event:
    """Base for everything a detector emits."""

    confirmed_index: int  # index of the candle that confirmed the pattern
    confirmed_at: datetime  # close time of that candle; nothing may act on it earlier


E = TypeVar("E", bound=Event)


class Detector(ABC, Generic[E]):
    @abstractmethod
    def update(self, view: SeriesView) -> list[E]:
        """Process `view.current` and return newly confirmed events."""
