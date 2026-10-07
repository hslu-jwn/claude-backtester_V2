"""Trades in R: the open trade the engine manages and the closed trade it outputs.

Spec: ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss / Take profit.

1R = the SL distance on the chart, |entry - initial stop| in bid prices. Gross R is the
result on the chart (entry and exit at the chart levels, no costs):

    long:  r_gross = (exit - entry) / risk        short: mirrored

Net R takes the fills (long: enter at ask = bid + spread, exit at bid; short: enter at bid,
exit at ask) and the commission:  r_net = r_gross - spread_r - commission_r.

Times: `entry_time` / `exit_time` are when the engine acted, i.e. the CLOSE time of the
entry candle and of the candle in which SL / TP was hit. `entry_candle` / `exit_candle` are
those candles' open times (`Candle.ts`), for drawing the position box on the chart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle, Direction


class ExitReason(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    BREAK_EVEN = "break_even"  # the SL after its move to the entry price was hit
    END_OF_DATA = "end_of_data"  # still open at the last candle: closed at its close


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


@dataclass(frozen=True, slots=True)
class TradeResult:
    symbol: str
    direction: Direction
    entry_time: datetime
    entry_candle: datetime
    entry: float  # chart (bid) price: the entry candle's close
    entry_fill: float  # long: ask, short: bid
    initial_stop: float
    take_profit: float
    exit_time: datetime
    exit_candle: datetime
    exit_price: float  # chart (bid) price
    exit_fill: float  # long: bid, short: ask
    exit_reason: ExitReason
    r_gross: float
    r_net: float
    spread_r: float
    commission_r: float
    break_even_time: datetime | None  # when the SL moved to the entry price (None: never)
    mae_r: float  # worst floating R on the chart while open (<= 0)
    mfe_r: float  # best floating R on the chart while open (>= 0)
    tags: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    @property
    def planned_r(self) -> float:
        """R at the take profit, on the chart."""
        return _sign(self.direction) * (self.take_profit - self.entry) / self.risk


@dataclass(slots=True)
class OpenTrade:
    """A trade the engine is managing. Engine-private; strategies never see it."""

    symbol: str
    direction: Direction
    entry_time: datetime
    entry_candle: datetime
    entry: float
    entry_fill: float
    initial_stop: float
    stop_loss: float  # current SL (may move to the entry price once)
    take_profit: float
    break_even_check: datetime | None  # next session start; None once checked or if off
    tags: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""
    break_even_time: datetime | None = None
    mae_r: float = 0.0
    mfe_r: float = 0.0

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    @property
    def sign(self) -> int:
        return _sign(self.direction)

    def r_at(self, price: float) -> float:
        return self.sign * (price - self.entry) / self.risk

    def track_excursion(self, candle: Candle) -> None:
        worst, best = (candle.low, candle.high) if self.sign > 0 else (candle.high, candle.low)
        self.mae_r = min(self.mae_r, self.r_at(worst))
        self.mfe_r = max(self.mfe_r, self.r_at(best))

    def exit_on(self, candle: Candle) -> tuple[float, ExitReason] | None:
        """Exit price and reason if SL or TP is hit inside `candle`, else None.

        Only this candle's OHLC is used. SL and TP both inside the candle: SL first
        (conservative). A candle that opens beyond the SL (gap) fills at its open; one that
        opens beyond the TP fills at the TP (never better than planned).
        """
        if self.sign > 0:
            stop_hit = candle.low <= self.stop_loss
            target_hit = candle.high >= self.take_profit
            gap_fill = min(candle.open, self.stop_loss)
        else:
            stop_hit = candle.high >= self.stop_loss
            target_hit = candle.low <= self.take_profit
            gap_fill = max(candle.open, self.stop_loss)
        if stop_hit:
            reason = ExitReason.BREAK_EVEN if self.break_even_time else ExitReason.STOP_LOSS
            return gap_fill, reason
        if target_hit:
            return self.take_profit, ExitReason.TAKE_PROFIT
        return None

    def close(
        self,
        exit_time: datetime,
        exit_candle: datetime,
        exit_price: float,
        reason: ExitReason,
        spread: float,
        commission_r: float,
    ) -> TradeResult:
        exit_fill = exit_price if self.sign > 0 else exit_price + spread
        r_gross = self.r_at(exit_price)
        r_fills = self.sign * (exit_fill - self.entry_fill) / self.risk
        return TradeResult(
            symbol=self.symbol,
            direction=self.direction,
            entry_time=self.entry_time,
            entry_candle=self.entry_candle,
            entry=self.entry,
            entry_fill=self.entry_fill,
            initial_stop=self.initial_stop,
            take_profit=self.take_profit,
            exit_time=exit_time,
            exit_candle=exit_candle,
            exit_price=exit_price,
            exit_fill=exit_fill,
            exit_reason=reason,
            r_gross=r_gross,
            r_net=r_fills - commission_r,
            spread_r=spread / self.risk,
            commission_r=commission_r,
            break_even_time=self.break_even_time,
            mae_r=self.mae_r,
            mfe_r=self.mfe_r,
            tags=self.tags,
            reason=self.reason,
        )
