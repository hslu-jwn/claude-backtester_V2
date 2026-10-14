"""Trades in R: the open trade the engine manages and the closed trade it outputs.

Spec: ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss / Take profit.

1R = the SL distance on the chart, |entry - initial stop| in bid prices. Gross R is the
result on the chart (entry and exit at the chart levels, no costs):

    long:  r_gross = (exit - entry) / risk        short: mirrored

Net R takes the fills (long: enter at ask = bid + spread, exit at bid; short: enter at bid,
exit at ask) and the commission:  r_net = r_gross - spread_r - commission_r.

Partial closes (strategy-session-zones.md › Take profit, two TPs; strategy-ny-indices.md ›
Take Profit, three): `tp1_share` of the position closes at TP1, `tp2_share` at TP2 when
there is a TP3, the rest at the last TP (or SL / break-even / end of data). Several TPs
inside one candle (no SL) are all filled. Each closed
part is a `PartialExit`; the trade's R is the share-weighted sum of its parts, gross and
net (spread and commission are paid once per unit, so they stay as for one exit).
After TP1 the rest's SL may move to the break-even level (with costs): from the next
candle on, or in the TP1 candle itself if that candle closes back beyond the level (then
the level was certainly hit after TP1).

Times: `entry_time` / `exit_time` are when the engine acted, i.e. the CLOSE time of the
entry candle and of the candle in which SL / TP was hit. `entry_candle` / `exit_candle` are
those candles' open times (`Candle.ts`), for drawing the position box on the chart.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle, Direction


class ExitReason(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    BREAK_EVEN = "break_even"  # the SL after its move to the break-even level was hit
    END_OF_DATA = "end_of_data"  # still open at the last candle: closed at its close


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


@dataclass(frozen=True, slots=True)
class PartialExit:
    """One closed part of a trade."""

    share: float  # of the whole position
    time: datetime  # close time of the candle it was closed in
    candle: datetime  # that candle's open time
    price: float  # chart (bid) price
    fill: float  # long: bid, short: ask
    reason: ExitReason
    r_gross: float  # R of this part on the chart (not weighted by its share)
    r_fills: float  # R of this part between the fills (spread included, no commission)


@dataclass(frozen=True, slots=True)
class TradeResult:
    symbol: str
    direction: Direction
    entry_time: datetime
    entry_candle: datetime
    entry: float  # chart (bid) price: the entry candle's close
    entry_fill: float  # long: ask, short: bid
    initial_stop: float
    take_profit: float  # TP1 (the whole position when take_profit_2 is None)
    exit_time: datetime  # the last part's
    exit_candle: datetime
    exit_price: float  # chart (bid) price
    exit_fill: float  # long: bid, short: ask
    exit_reason: ExitReason
    r_gross: float  # share-weighted sum of the parts
    r_net: float
    spread_r: float
    commission_r: float
    break_even_time: datetime | None  # when the SL moved to break-even (None: never)
    break_even_stop: float | None  # the moved SL: 0R net after costs (None: never moved)
    mae_r: float  # worst floating R on the chart while open (<= 0)
    mfe_r: float  # best floating R on the chart while open (>= 0)
    tags: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""
    confluence: str = ""  # entry confluence type (Order.confluence)
    take_profit_2: float | None = None
    tp1_share: float = 1.0
    parts: tuple[PartialExit, ...] = ()  # in the order they were closed
    take_profit_3: float | None = None
    tp2_share: float | None = None  # with a TP3

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    def r_at(self, price: float) -> float:
        return _sign(self.direction) * (price - self.entry) / self.risk

    @property
    def targets(self) -> list[tuple[float, float]]:
        """(price, share) of each TP."""
        return tp_targets(
            self.take_profit, self.take_profit_2, self.take_profit_3, self.tp1_share,
            self.tp2_share,
        )  # fmt: skip

    @property
    def planned_r(self) -> float:
        """R if every TP is hit (share-weighted), on the chart."""
        return sum(share * self.r_at(price) for price, share in self.targets)


def tp_targets(
    tp1: float,
    tp2: float | None,
    tp3: float | None,
    tp1_share: float,
    tp2_share: float | None,
) -> list[tuple[float, float]]:
    """(price, share) of each TP; the last one takes the rest."""
    if tp2 is None:
        return [(tp1, 1.0)]
    if tp3 is None:
        return [(tp1, tp1_share), (tp2, 1.0 - tp1_share)]
    return [(tp1, tp1_share), (tp2, tp2_share), (tp3, 1.0 - tp1_share - tp2_share)]


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
    stop_loss: float  # current SL (may move to the break-even level once)
    take_profit: float  # TP1
    break_even_check: datetime | None  # next session start; None once checked or if off
    break_even_level: float  # where a hit is 0R net: entry + spread + commission (long)
    tags: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""
    confluence: str = ""  # entry confluence type (Order.confluence)
    take_profit_2: float | None = None
    tp1_share: float = 1.0
    break_even_after_tp1: bool = False
    take_profit_3: float | None = None
    tp2_share: float | None = None
    ref: object = None  # Order.ref
    spread: float = 0.0  # added to a short's exit (fills at ask)
    break_even_time: datetime | None = None
    mae_r: float = 0.0
    mfe_r: float = 0.0
    parts: list[PartialExit] = field(default_factory=list)

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    @property
    def sign(self) -> int:
        return _sign(self.direction)

    @property
    def open_share(self) -> float:
        return 1.0 - sum(p.share for p in self.parts)

    @property
    def is_closed(self) -> bool:
        return math.isclose(self.open_share, 0.0, abs_tol=1e-12)

    @property
    def tp1_done(self) -> bool:
        return bool(self.parts)

    @property
    def targets(self) -> list[tuple[float, float]]:
        return tp_targets(
            self.take_profit, self.take_profit_2, self.take_profit_3, self.tp1_share,
            self.tp2_share,
        )  # fmt: skip

    def r_at(self, price: float) -> float:
        return self.sign * (price - self.entry) / self.risk

    def track_excursion(self, candle: Candle) -> None:
        worst, best = (candle.low, candle.high) if self.sign > 0 else (candle.high, candle.low)
        self.mae_r = min(self.mae_r, self.r_at(worst))
        self.mfe_r = max(self.mfe_r, self.r_at(best))

    def _beyond(self, price: float, level: float) -> bool:
        """`price` reached `level` in the trade's direction (long: price >= level)."""
        return self.sign * (price - level) >= 0

    def on_candle(self, candle: Candle, now: datetime) -> None:
        """Close the parts whose SL / TP is hit inside `candle`.

        Only this candle's OHLC is used. SL and a TP both inside the candle: SL first
        (conservative). A candle that opens beyond the SL (gap) fills at its open; one that
        opens beyond a TP fills at the TP (never better than planned). Several TPs inside
        one candle (no SL): all are filled.
        """
        worst, best = (candle.low, candle.high) if self.sign > 0 else (candle.high, candle.low)
        if self.sign * (worst - self.stop_loss) <= 0:
            gap_fill = self.stop_loss if self._beyond(candle.open, self.stop_loss) else candle.open
            reason = ExitReason.BREAK_EVEN if self.break_even_time else ExitReason.STOP_LOSS
            self._exit(self.open_share, candle, now, gap_fill, reason)
            return
        targets = self.targets
        hit_tp1 = False
        for i in range(len(self.parts), len(targets)):  # every part closed so far was a TP
            price, share = targets[i]
            if not self._beyond(best, price):
                break
            rest = i == len(targets) - 1
            self._exit(
                self.open_share if rest else share, candle, now, price, ExitReason.TAKE_PROFIT
            )
            hit_tp1 = hit_tp1 or i == 0
        if self.is_closed:
            return
        if hit_tp1 and self.break_even_after_tp1:
            self.move_to_break_even(now)
            if not self._beyond(candle.close, self.break_even_level):
                # closed back beyond break-even after TP1: the level was hit in this candle
                self._exit(
                    self.open_share, candle, now, self.break_even_level, ExitReason.BREAK_EVEN
                )

    def on_fill_candle(self, candle: Candle, now: datetime) -> None:
        """The candle a limit order filled in: the order of events inside it is unknown, so
        only the SL counts (SL first); a TP reached in it is not counted."""
        worst = candle.low if self.sign > 0 else candle.high
        if self.sign * (worst - self.stop_loss) <= 0:
            self._exit(self.open_share, candle, now, self.stop_loss, ExitReason.STOP_LOSS)

    def move_to_break_even(self, now: datetime) -> None:
        if self.break_even_time is None:
            self.stop_loss = self.break_even_level
            self.break_even_time = now

    def _exit(
        self, share: float, candle: Candle, now: datetime, price: float, reason: ExitReason
    ) -> None:
        fill = price if self.sign > 0 else price + self.spread
        r_fills = self.sign * (fill - self.entry_fill) / self.risk
        self.parts.append(
            PartialExit(share, now, candle.ts, price, fill, reason, self.r_at(price), r_fills)
        )

    def close_all(self, candle: Candle, now: datetime, price: float, reason: ExitReason) -> None:
        """Close what is still open (end of data)."""
        if not self.is_closed:
            self._exit(self.open_share, candle, now, price, reason)

    def result(self, commission_r: float) -> TradeResult:
        if not self.is_closed:
            raise ValueError("the trade is still open")
        last = self.parts[-1]
        return TradeResult(
            symbol=self.symbol,
            direction=self.direction,
            entry_time=self.entry_time,
            entry_candle=self.entry_candle,
            entry=self.entry,
            entry_fill=self.entry_fill,
            initial_stop=self.initial_stop,
            take_profit=self.take_profit,
            exit_time=last.time,
            exit_candle=last.candle,
            exit_price=last.price,
            exit_fill=last.fill,
            exit_reason=last.reason,
            r_gross=sum(p.share * p.r_gross for p in self.parts),
            r_net=sum(p.share * p.r_fills for p in self.parts) - commission_r,
            spread_r=self.spread / self.risk,
            commission_r=commission_r,
            break_even_time=self.break_even_time,
            break_even_stop=self.stop_loss if self.break_even_time else None,
            mae_r=self.mae_r,
            mfe_r=self.mfe_r,
            tags=self.tags,
            reason=self.reason,
            confluence=self.confluence,
            take_profit_2=self.take_profit_2,
            tp1_share=self.tp1_share if self.take_profit_2 is not None else 1.0,
            parts=tuple(self.parts),
            take_profit_3=self.take_profit_3,
            tp2_share=self.tp2_share,
        )
