"""Trading costs in R: a fixed spread per symbol and a commission per lot.

Spec: ROADMAP.md › 3.1, risk-management.md › Costs. Candles are bid prices (histdata.com
has no asks, so the spread is always this fixed setting). Longs enter at ask (bid + spread) and exit
at bid; shorts enter at bid and exit at ask, so every round trip pays one spread. The
commission is a dollar amount per lot (round turn), so in R it depends on the SL distance:

    commission_R = commission per lot / (SL distance x value of a 1.0 price move per lot)

The values are rough estimates (FTMO publishes no fixed spreads); both costs can be
switched off so backtests can compare gross and net results.

Swap (risk-management.md › Costs › Swap in the engine): a position open across the daily
rollover at 17:00 America/New_York pays one night of swap, three on the symbol's triple
weekday; in R, net only:

    swap_R = nights x swap per lot / (SL distance x value of a 1.0 price move per lot)

Slippage is stored per symbol here but not yet applied: the account simulator (`risk/`,
Phase 5) will use it.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from types import MappingProxyType
from zoneinfo import ZoneInfo

from backtester.core.models import Direction

ROLLOVER_ZONE = ZoneInfo("America/New_York")
ROLLOVER_TIME = time(17, 0)  # FTMO server midnight
ROLLOVER_WEEKDAYS = range(5)  # New York Mon-Fri; no rollover on Saturday / Sunday dates
WEDNESDAY = 2  # datetime.weekday(): Monday = 0
SWAP_TRIPLE_NIGHTS = 3


def rollover_nights(
    entry_time: datetime, exit_time: datetime, triple_weekday: int = WEDNESDAY
) -> int:
    """Nights of swap for a position held from `entry_time` to `exit_time` (aware datetimes).

    Each 17:00 New York rollover with entry_time < rollover <= exit_time counts: one exactly
    at the entry time does not (the position opened after it), one exactly at the exit time
    does (the position was still open when it happened). A rollover on a New York Monday to
    Friday counts one night, three when that New York date's weekday is `triple_weekday`;
    Saturday and Sunday dates have none. Follows New York's DST (21:00 UTC in summer,
    22:00 UTC in winter).
    """
    if exit_time <= entry_time:
        return 0
    first = entry_time.astimezone(ROLLOVER_ZONE).date()
    last = exit_time.astimezone(ROLLOVER_ZONE).date()
    nights, day = 0, first
    while day <= last:
        if day.weekday() in ROLLOVER_WEEKDAYS:
            at = datetime.combine(day, ROLLOVER_TIME, ROLLOVER_ZONE)
            if entry_time < at <= exit_time:
                nights += SWAP_TRIPLE_NIGHTS if day.weekday() == triple_weekday else 1
        day += timedelta(days=1)
    return nights


@dataclass(frozen=True, slots=True)
class SymbolCosts:
    spread: float  # ask - bid in price units
    commission_per_lot: float  # USD per 1.0 lot, round turn
    contract_size: float  # units of the base asset per 1.0 lot (100 oz, 100,000 GBP)
    quote_to_usd: float = 1.0  # USD per 1 unit of the quote currency (fixed approximation)
    # price units per market fill (entries and SL hits; TPs are limit orders), rough
    # starting estimates to check against FTMO demo fills (risk-management.md › Costs)
    slippage: float = 0.0
    swap_long_per_lot: float = 0.0  # USD per 1.0 lot per night, until filled in from MT5
    swap_short_per_lot: float = 0.0  # USD per 1.0 lot per night, until filled in from MT5
    # New York weekday of the rollover that counts 3 nights (MT5 swap_rollover3days)
    swap_triple_weekday: int = WEDNESDAY

    @property
    def value_per_price_unit(self) -> float:
        """USD gained or lost per 1.0 lot when the price moves by 1.0."""
        return self.contract_size * self.quote_to_usd


USDJPY_APPROX = 150.0  # GBPJPY pip value in USD goes through USDJPY; fixed setting

DEFAULT_SYMBOL_COSTS: Mapping[str, SymbolCosts] = MappingProxyType(
    {
        "XAUUSD": SymbolCosts(
            spread=0.25, commission_per_lot=6.0, contract_size=100, slippage=0.10
        ),
        "GBPUSD": SymbolCosts(
            spread=0.00003, commission_per_lot=5.0, contract_size=100_000, slippage=0.00002
        ),
        "GBPJPY": SymbolCosts(
            spread=0.010,
            commission_per_lot=5.0,
            contract_size=100_000,
            quote_to_usd=1 / USDJPY_APPROX,
            slippage=0.003,
        ),
        # Indices (user, 2026-10-10): spread estimates until FTMO's are measured, no
        # commission or swap for now. contract_size only
        # matters for the commission; check it with `tools.mt5_info` before Phase 5.
        "NAS100": SymbolCosts(spread=1.0, commission_per_lot=0.0, contract_size=1, slippage=1.0),
        "US500": SymbolCosts(spread=0.5, commission_per_lot=0.0, contract_size=1, slippage=0.25),
    }
)


@dataclass(frozen=True, slots=True)
class CostConfig:
    spread_enabled: bool = True  # off: no spread on fills (gross = net apart from commission)
    commission_enabled: bool = True  # off: no commission
    swap_enabled: bool = True  # off: swap_r is 0 (rates are 0 until filled from MT5 anyway)
    symbols: Mapping[str, SymbolCosts] = field(default_factory=lambda: DEFAULT_SYMBOL_COSTS)

    def for_symbol(self, symbol: str) -> SymbolCosts:
        try:
            return self.symbols[symbol]
        except KeyError:
            raise KeyError(f"no cost settings for {symbol}; add it to CostConfig.symbols") from None

    def spread(self, symbol: str) -> float:
        """Spread applied to fills (0 when switched off)."""
        if not self.spread_enabled:
            return 0.0
        return self.for_symbol(symbol).spread

    def spread_r(self, symbol: str, risk: float) -> float:
        return self.spread(symbol) / risk

    def commission_price(self, symbol: str) -> float:
        """Commission as a price distance per lot (0 when switched off)."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        return costs.commission_per_lot / costs.value_per_price_unit

    def break_even_offset(self, symbol: str) -> float:
        """Distance from the entry (chart price) to the break-even stop, so a hit there
        ends at 0R after spread and commission (strategy-session-zones.md › Stop loss)."""
        return self.spread(symbol) + self.commission_price(symbol)

    def commission_r(self, symbol: str, risk: float) -> float:
        """Commission in R for an SL distance of `risk` (price units)."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        return costs.commission_per_lot / (risk * costs.value_per_price_unit)

    def swap_r(
        self,
        symbol: str,
        direction: Direction,
        risk: float,
        entry_time: datetime,
        exits: Iterable[tuple[float, datetime]],
    ) -> float:
        """Swap in R (negative = cost, positive = credit), added to net R only.

        `exits` = (share, exit_time) of each closed part: every part pays the nights between
        the trade's entry and ITS OWN exit time, for its own share of the position. A symbol
        without cost settings has no swap (the spread would already have failed the run).
        """
        costs = self.symbols.get(symbol)
        if not self.swap_enabled or costs is None:
            return 0.0
        rate = (
            costs.swap_long_per_lot if direction is Direction.BULLISH else costs.swap_short_per_lot
        )
        nights = sum(
            share * rollover_nights(entry_time, at, costs.swap_triple_weekday)
            for share, at in exits
        )
        return nights * rate / (risk * costs.value_per_price_unit)
