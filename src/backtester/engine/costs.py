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
from datetime import datetime, timedelta
from types import MappingProxyType

from backtester.core.models import Direction
from backtester.engine.spread_table import SpreadTable
from backtester.sessions import ROLLOVER_TIME, ROLLOVER_ZONE

ROLLOVER_WEEKDAYS = range(5)  # New York Mon-Fri; no rollover on Saturday / Sunday dates
WEDNESDAY = 2  # datetime.weekday(): Monday = 0
SWAP_TRIPLE_NIGHTS = 3
COST_FILTER_TOLERANCE = 1e-12  # floating point: a cost equal to the limit is filled


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
    swap_long_per_lot: float = 0.0  # USD per 1.0 lot per night (negative = cost)
    swap_short_per_lot: float = 0.0  # USD per 1.0 lot per night (negative = cost)
    # New York weekday of the rollover that counts 3 nights (MT5 swap_rollover3days)
    swap_triple_weekday: int = WEDNESDAY

    @property
    def value_per_price_unit(self) -> float:
        """USD gained or lost per 1.0 lot when the price moves by 1.0."""
        return self.contract_size * self.quote_to_usd


USDJPY_APPROX = 150.0  # GBPJPY pip value in USD goes through USDJPY; fixed setting
FRIDAY = 4
BINANCE_TAKER_FEE = 0.0005  # placeholder: 0.05 % per side (ROADMAP 11.9)
BINANCE_REFERENCE_PRICE = MappingProxyType({"BTCUSDT": 100_000.0, "ETHUSDT": 4_000.0})  # placeholder

# Swap: FTMO's MT5 rates of 2026-10-14 (USD per lot per night, ROADMAP 10.4), the default
# since the user's decision of 2026-10-14. Today's rates, also applied to older years.

DEFAULT_SYMBOL_COSTS: Mapping[str, SymbolCosts] = MappingProxyType(
    {
        "XAUUSD": SymbolCosts(
            spread=0.25,
            commission_per_lot=6.0,
            contract_size=100,
            slippage=0.10,
            swap_long_per_lot=-61.27,
            swap_short_per_lot=-4.20,
        ),
        "GBPUSD": SymbolCosts(
            spread=0.00003,
            commission_per_lot=5.0,
            contract_size=100_000,
            slippage=0.00002,
            swap_long_per_lot=-5.77,
            swap_short_per_lot=-4.48,
        ),
        "GBPJPY": SymbolCosts(
            spread=0.010,
            commission_per_lot=5.0,
            contract_size=100_000,
            quote_to_usd=1 / USDJPY_APPROX,
            slippage=0.003,
            swap_long_per_lot=2.04,
            swap_short_per_lot=-13.85,
        ),
        # Indices (user, 2026-10-10): spread estimates until FTMO's are measured, no
        # commission. contract_size 1 = $1 per point per lot (FTMO .cash indices); check it
        # with `tools.mt5_info` before Phase 5. Triple swap on Friday.
        "NAS100": SymbolCosts(
            spread=1.0,
            commission_per_lot=0.0,
            contract_size=1,
            slippage=1.0,
            swap_long_per_lot=-6.912,
            swap_short_per_lot=0.339,
            swap_triple_weekday=FRIDAY,
        ),
        "US500": SymbolCosts(
            spread=0.5,
            commission_per_lot=0.0,
            contract_size=1,
            slippage=0.25,
            swap_long_per_lot=-1.2218,
            swap_short_per_lot=-0.4575,
            swap_triple_weekday=FRIDAY,
        ),
        # --- ROADMAP 11.8 / 11.9, read from the FTMO MT5 terminal on 2026-10-15 ---------
        # spread = median of the last 60 cached days of M1 bar spreads (data/cache/mt5);
        # swap = symbol_info swap points x tick value (USD per lot per night); quote_to_usd
        # from the tick value; slippage = half the spread (rough, like the others);
        # commission: FX $5 as GBPUSD, XAGUSD $6 as XAUUSD (assumptions: not in symbol_info),
        # indices / energy / DXY 0. Crypto swap is a percentage mode in MT5: 0 here.
        "EURUSD": SymbolCosts(0.00002, 5.0, 100_000, slippage=0.00001, swap_long_per_lot=-8.53, swap_short_per_lot=0.21, swap_triple_weekday=WEDNESDAY),
        "AUDUSD": SymbolCosts(0.00002, 5.0, 100_000, slippage=0.00001, swap_long_per_lot=-3.04, swap_short_per_lot=-6.54),
        "NZDUSD": SymbolCosts(0.00003, 5.0, 100_000, slippage=0.000015, swap_long_per_lot=-4.78, swap_short_per_lot=0.01),
        "EURGBP": SymbolCosts(0.00004, 5.0, 100_000, 1.3271, slippage=0.00002, swap_long_per_lot=-8.4804, swap_short_per_lot=0.0),
        "USDJPY": SymbolCosts(0.003, 5.0, 100_000, 0.00632, slippage=0.0015, swap_long_per_lot=1.0813, swap_short_per_lot=-11.0347),
        "USDCAD": SymbolCosts(0.00003, 5.0, 100_000, 0.7047, slippage=0.000015, swap_long_per_lot=0.4792, swap_short_per_lot=-8.4426),
        "USDCHF": SymbolCosts(0.00005, 5.0, 100_000, 1.2088, slippage=0.000025, swap_long_per_lot=1.5715, swap_short_per_lot=-16.2468),
        "EURJPY": SymbolCosts(0.009, 5.0, 100_000, 0.00632, slippage=0.0045, swap_long_per_lot=1.328, swap_short_per_lot=-7.6199),
        "XAGUSD": SymbolCosts(0.049, 6.0, 5000, slippage=0.0245, swap_long_per_lot=-68.05, swap_short_per_lot=0.30),
        "GER40": SymbolCosts(1.53, 0.0, 1, 1.1211, slippage=0.765, swap_long_per_lot=-5.0571, swap_short_per_lot=-0.0511, swap_triple_weekday=FRIDAY),
        "UK100": SymbolCosts(1.45, 0.0, 1, 1.3271, slippage=0.725, swap_long_per_lot=-3.2063, swap_short_per_lot=0.148, swap_triple_weekday=FRIDAY),
        "JP225": SymbolCosts(10.0, 0.0, 10, 0.00632, slippage=5.0, swap_long_per_lot=-0.5683, swap_short_per_lot=-0.1894, swap_triple_weekday=FRIDAY),
        "EU50": SymbolCosts(1.06, 0.0, 1, 1.1211, slippage=0.53, swap_long_per_lot=-1.2359, swap_short_per_lot=-0.0124, swap_triple_weekday=FRIDAY),
        "USOIL": SymbolCosts(0.075, 0.0, 100, slippage=0.0375, swap_long_per_lot=4.966, swap_short_per_lot=-22.54, swap_triple_weekday=FRIDAY),
        "UKOIL": SymbolCosts(0.069, 0.0, 100, slippage=0.0345, swap_long_per_lot=6.097, swap_short_per_lot=-27.582, swap_triple_weekday=FRIDAY),
        "DXY": SymbolCosts(0.018, 0.0, 100, slippage=0.009, swap_long_per_lot=-2.337, swap_short_per_lot=0.118, swap_triple_weekday=FRIDAY),
        "US30": SymbolCosts(2.28, 0.0, 1, slippage=1.14, swap_long_per_lot=-11.7596, swap_short_per_lot=0.5936, swap_triple_weekday=FRIDAY),
        "US2000": SymbolCosts(0.93, 0.0, 1, slippage=0.465, swap_long_per_lot=-0.5735, swap_short_per_lot=-0.0172, swap_triple_weekday=FRIDAY),
        "NATGAS": SymbolCosts(0.06, 0.0, 1000, slippage=0.03, swap_long_per_lot=-5.84, swap_short_per_lot=1.27, swap_triple_weekday=FRIDAY),
        "BTCUSD": SymbolCosts(1.0, 0.0, 1, slippage=0.5, swap_triple_weekday=FRIDAY),
        "ETHUSD": SymbolCosts(0.6, 0.0, 10, slippage=0.3, swap_triple_weekday=FRIDAY),
        # --- PLACEHOLDER, to be confirmed by the user (ROADMAP 11.9): Binance futures ---
        # taker fee 0.05 % per side as dollars per 1.0 lot (1 coin) at a fixed reference price
        # (a percentage of notional is not modelled); spread 0; funding (data/cache/binance_funding)
        # not applied yet, so swap 0.
        "BTCUSDT": SymbolCosts(0.0, 2 * BINANCE_TAKER_FEE * BINANCE_REFERENCE_PRICE["BTCUSDT"], 1),
        "ETHUSDT": SymbolCosts(0.0, 2 * BINANCE_TAKER_FEE * BINANCE_REFERENCE_PRICE["ETHUSDT"], 1),
    }
)  # fmt: skip


@dataclass(frozen=True, slots=True)
class CostConfig:
    spread_enabled: bool = True  # off: no spread on fills (gross = net apart from commission)
    commission_enabled: bool = True  # off: no commission
    swap_enabled: bool = True  # off: swap_r is 0
    symbols: Mapping[str, SymbolCosts] = field(default_factory=lambda: DEFAULT_SYMBOL_COSTS)
    # cost filter: orders with spread + commission above this many R are not filled; 0 = off
    max_cost_r: float = 0.0
    # spread by year and hour of day (ROADMAP 6.7); None: the fixed `SymbolCosts.spread`
    spread_table: SpreadTable | None = None

    def __post_init__(self) -> None:
        if self.max_cost_r < 0:
            raise ValueError("max_cost_r must be >= 0 (0 = off)")

    def for_symbol(self, symbol: str) -> SymbolCosts:
        try:
            return self.symbols[symbol]
        except KeyError:
            raise KeyError(f"no cost settings for {symbol}; add it to CostConfig.symbols") from None

    def spread(self, symbol: str, at: datetime | None = None) -> float:
        """Spread applied to fills (0 when switched off). With a `spread_table` and a time
        `at` it is the table's spread of that time; where the table has no value (or no
        time is given) it is the fixed `SymbolCosts.spread`."""
        if not self.spread_enabled:
            return 0.0
        if self.spread_table is not None and at is not None:
            value = self.spread_table.spread_at(symbol, at)
            if value is not None:
                return value
        return self.for_symbol(symbol).spread

    def spread_r(self, symbol: str, risk: float, at: datetime | None = None) -> float:
        return self.spread(symbol, at) / risk

    def commission_price(self, symbol: str) -> float:
        """Commission as a price distance per lot (0 when switched off)."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        return costs.commission_per_lot / costs.value_per_price_unit

    def break_even_offset(self, symbol: str, at: datetime | None = None) -> float:
        """Distance from the entry (chart price) to the break-even stop, so a hit there
        ends at 0R after spread and commission (strategy-session-zones.md › Stop loss)."""
        return self.spread(symbol, at) + self.commission_price(symbol)

    def commission_r(self, symbol: str, risk: float) -> float:
        """Commission in R for an SL distance of `risk` (price units)."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        return costs.commission_per_lot / (risk * costs.value_per_price_unit)

    def too_expensive(self, symbol: str, risk: float, at: datetime | None = None) -> bool:
        """Cost filter: spread + commission in R above `max_cost_r` (never when it is 0)."""
        if not self.max_cost_r:
            return False
        cost = self.spread_r(symbol, risk, at) + self.commission_r(symbol, risk)
        return cost > self.max_cost_r + COST_FILTER_TOLERANCE

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
