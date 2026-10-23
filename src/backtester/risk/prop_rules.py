"""Daily guard and FTMO limits for the live bot. Spec: docs/live-trading.md › Risk,
docs/risk-management.md › Daily & account protection, Prop-firm field.

- The FTMO day runs from midnight `Europe/Prague` (CE(S)T) to the next midnight; days with a DST
  change are 23 / 25 h long. Never a fixed UTC offset.
- Day P/L = equity now - balance at the day's start (closed + floating).
- Personal daily stop (default -2 %): no new orders, own positions closed, until the next day.
- FTMO limits (2-Step): daily loss 5 % of the initial balance, measured from the day-start
  balance; max loss 10 % static of the initial balance. Reaching a limit counts as a breach
  (rule set by the user, 2026-10-22).

(The preset list for other firms and the prop-firm field of the backtest come later, ROADMAP 5.6.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

FTMO_ZONE = "Europe/Prague"
EPS = 1e-9  # float noise at the limits


@dataclass(frozen=True, slots=True)
class GuardConfig:
    daily_stop_percent: float = 2.0  # personal stop (rule set by the user)
    ftmo_daily_loss_percent: float = 5.0  # FTMO 2-Step
    ftmo_max_loss_percent: float = 10.0  # FTMO 2-Step, static
    initial_balance: float = 100_000.0  # challenge size: base of both FTMO loss limits
    zone: str = FTMO_ZONE

    def __post_init__(self) -> None:
        for name in (
            "daily_stop_percent",
            "ftmo_daily_loss_percent",
            "ftmo_max_loss_percent",
            "initial_balance",
        ):
            val = getattr(self, name)
            if not (math.isfinite(val) and val > 0):
                label = f"{name} (daily stop)" if name == "daily_stop_percent" else name
                raise ValueError(f"{label} must be finite and > 0")
        ZoneInfo(self.zone)


@dataclass(frozen=True, slots=True)
class GuardStatus:
    day_pl: float
    day_pl_percent: float
    stop_trading: bool  # no new orders, close own positions (also true on a breach)
    breach: bool  # an FTMO limit is reached: close everything and stop the bot
    reason: str = ""


def prague_day_start(now: datetime, zone: str = FTMO_ZONE) -> datetime:
    """UTC instant of the last midnight in `zone` at or before `now` (an aware datetime)."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    tz = ZoneInfo(zone)
    midnight = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(UTC)


def evaluate(
    config: GuardConfig,
    day_start_balance: float,
    equity: float,
    initial_balance: float | None = None,
) -> GuardStatus:
    """Today's P/L against the personal stop and the FTMO limits."""
    if not math.isfinite(day_start_balance) or day_start_balance <= 0:
        raise ValueError("day_start_balance must be > 0")

    if not math.isfinite(equity):
        raise ValueError("equity must be finite")
    if initial_balance is not None and (not math.isfinite(initial_balance) or initial_balance <= 0):
        raise ValueError("initial_balance must be > 0")
    initial = config.initial_balance if initial_balance is None else initial_balance
    day_pl = equity - day_start_balance
    percent = day_pl / day_start_balance * 100
    if equity <= initial * (1 - config.ftmo_max_loss_percent / 100) + EPS:
        return GuardStatus(day_pl, percent, True, True, "FTMO max loss reached")
    if -day_pl >= initial * config.ftmo_daily_loss_percent / 100 - EPS:
        return GuardStatus(day_pl, percent, True, True, "FTMO daily loss reached")
    if percent <= -config.daily_stop_percent + EPS:
        return GuardStatus(day_pl, percent, True, False, f"daily stop reached ({percent:.2f} %)")
    return GuardStatus(day_pl, percent, False, False)
