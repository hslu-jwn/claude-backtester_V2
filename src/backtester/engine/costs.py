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

Percentage fees (risk-management.md › Costs, rule set by the user 2026-10-15): a symbol can
charge its commission as a share of the notional per side (`commission_pct_per_side`, entry
and exit notional at their fill prices) and its swap as a share of the notional per year per
night (`swap_*_pct_year`, notional at the entry price). Lots and contract size cancel, so in R:

    commission_R = pct x (entry fill + sum(share x exit fill)) / SL distance
    swap_R       = nights x pct_year / 365 x entry / SL distance

Binance funding (`SymbolCosts.funding`, rates from `data/cache/binance_funding/<SYM>.csv`):
every funding timestamp t with entry_time < t <= exit_time pays rate x notional (longs pay a
positive rate, shorts receive it); notional approximated at the entry price:

    funding_R = - sign x sum(share x sum(rates while open)) x entry / SL distance

Slippage applies against the trader to market entries and every non-TP exit, scaled at
the chart entry price like the fixed spread (rule set by the user, 2026-10-22).
"""

from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from functools import cache, lru_cache
from pathlib import Path
from types import MappingProxyType

from backtester.core.models import Direction
from backtester.engine.spread_table import SpreadTable
from backtester.paths import DATA_DIR
from backtester.sessions import ROLLOVER_TIME, ROLLOVER_ZONE

ROLLOVER_WEEKDAYS = range(5)  # New York Mon-Fri; no rollover on Saturday / Sunday dates
WEDNESDAY = 2  # datetime.weekday(): Monday = 0
SWAP_TRIPLE_NIGHTS = 3
DAYS_PER_YEAR = 365  # percentage swap is quoted per year, charged per night
FUNDING_DIR = DATA_DIR / "cache" / "binance_funding"
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
class FundingSeries:
    """Funding rates of one perpetual future: sorted UTC timestamps and the rate of each."""

    times: tuple[datetime, ...]
    rates: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.times) != len(self.rates):
            raise ValueError("funding times and rates differ in length")

    def rate_sum(self, entry_time: datetime, exit_time: datetime) -> float:
        """Sum of the rates with entry_time < timestamp <= exit_time (position open then)."""
        lo = bisect_right(self.times, entry_time)
        hi = bisect_right(self.times, exit_time)
        return sum(self.rates[lo:hi]) if hi > lo else 0.0


def funding_from_rows(rows: Iterable[tuple[datetime, float]]) -> FundingSeries:
    ordered = sorted(rows)
    return FundingSeries(tuple(t for t, _ in ordered), tuple(r for _, r in ordered))


@lru_cache(maxsize=16)
def load_funding(path: Path) -> FundingSeries:
    """`binance_funding/<SYM>.csv` (calc_time UTC, last_funding_rate) -> FundingSeries."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = [
            (
                datetime.fromisoformat(r["calc_time"]).replace(tzinfo=UTC),
                float(r["last_funding_rate"]),
            )
            for r in csv.DictReader(f)
        ]
    return funding_from_rows(rows)


@dataclass(frozen=True, slots=True)
class SymbolCosts:
    spread: float  # ask - bid in price units
    commission_per_lot: float  # USD per 1.0 lot, round turn
    contract_size: float  # units of the base asset per 1.0 lot (100 oz, 100,000 GBP)
    quote_to_usd: float = 1.0  # USD per 1 unit of the quote currency (fixed approximation)
    # price units per market fill (entries and non-TP exits), rough
    # starting estimates to check against FTMO demo fills (risk-management.md › Costs)
    slippage: float = 0.0
    swap_long_per_lot: float = 0.0  # USD per 1.0 lot per night (negative = cost)
    swap_short_per_lot: float = 0.0  # USD per 1.0 lot per night (negative = cost)
    # New York weekday of the rollover that counts 3 nights (MT5 swap_rollover3days)
    swap_triple_weekday: int = WEDNESDAY
    # percentage costs (0 = off); the fraction is of the notional, e.g. 0.0005 = 0.05 %
    commission_pct_per_side: float = 0.0  # per side, on top of commission_per_lot
    swap_long_pct_year: float = 0.0  # per year, charged per night (negative = cost)
    swap_short_pct_year: float = 0.0
    funding: bool = False  # Binance perpetual funding from data/cache/binance_funding
    # median price of the window the fixed spread stands for (REFERENCE_PRICES); None: the
    # spread is never scaled with the price level (CostConfig.spread_price_scaling)
    reference_price: float | None = None
    # Spec: risk-management.md > Costs > Tick rounding; None leaves levels unchanged.
    tick_size: float | None = None

    def __post_init__(self) -> None:
        if self.tick_size is not None and (
            not math.isfinite(self.tick_size) or self.tick_size <= 0
        ):
            raise ValueError("tick_size must be finite and > 0, or None")

    @property
    def value_per_price_unit(self) -> float:
        """USD gained or lost per 1.0 lot when the price moves by 1.0."""
        return self.contract_size * self.quote_to_usd


USDJPY_APPROX = 150.0  # GBPJPY pip value in USD goes through USDJPY; fixed setting
FRIDAY = 4
# Percentage fees (rule set by the user, 2026-10-15; FTMO values to be confirmed with the first
# demo trade's deal history; risk-management.md › Costs): FTMO metals 0.0014 % round turn,
# FTMO crypto 0.065 % round turn and -30 % per year swap, Binance USD-M taker 0.05 % per side.
FTMO_METAL_COMMISSION_PCT_SIDE = 0.000007
FTMO_CRYPTO_COMMISSION_PCT_SIDE = 0.000325
FTMO_CRYPTO_SWAP_PCT_YEAR = -0.30
BINANCE_TAKER_FEE = 0.0005

# Swap: FTMO's MT5 rates of 2026-10-14 (USD per lot per night, ROADMAP 10.4), the default
# since the user's decision of 2026-10-14. Today's rates, also applied to older years.

_BASE_SYMBOL_COSTS: dict[str, SymbolCosts] = (
    {
        "XAUUSD": SymbolCosts(
            spread=0.25,
            commission_per_lot=0.0,  # was $6 per lot until 2026-10-15
            commission_pct_per_side=FTMO_METAL_COMMISSION_PCT_SIDE,
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
        "XAGUSD": SymbolCosts(0.049, 0.0, 5000, slippage=0.0245, commission_pct_per_side=FTMO_METAL_COMMISSION_PCT_SIDE, swap_long_per_lot=-68.05, swap_short_per_lot=0.30),
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
        # --- V2.6 step 9 (user, 2026-10-27), FTMO symbol_info of 2026-10-27, same method ---
        # spread = median M1 bar spread of 2026-08-28..2026-10-26 (data/cache/mt5); FX $5
        # commission assumed like the other pairs, indices 0. HK50: the terminal had no HKD
        # rate (tick value 0), so quote_to_usd = the USD peg's midpoint 1 / 7.80 (assumption).
        "AUDJPY": SymbolCosts(0.009, 5.0, 100_000, 0.00634111, slippage=0.0045, swap_long_per_lot=2.24475, swap_short_per_lot=-8.44636),
        "CADJPY": SymbolCosts(0.007, 5.0, 100_000, 0.00634111, slippage=0.0035, swap_long_per_lot=0.317056, swap_short_per_lot=-3.62077),
        "NZDJPY": SymbolCosts(0.009, 5.0, 100_000, 0.00634111, slippage=0.0045, swap_long_per_lot=0.488265, swap_short_per_lot=-3.45590),
        "CHFJPY": SymbolCosts(0.015, 5.0, 100_000, 0.00634111, slippage=0.0075, swap_long_per_lot=-7.57129, swap_short_per_lot=1.13506),
        "EURAUD": SymbolCosts(0.00006, 5.0, 100_000, 0.70261, slippage=0.00003, swap_long_per_lot=-9.52739, swap_short_per_lot=1.27875),
        "GBPAUD": SymbolCosts(0.00011, 5.0, 100_000, 0.70261, slippage=0.000055, swap_long_per_lot=-9.41497, swap_short_per_lot=-0.878263),
        "AUS200": SymbolCosts(1.0, 0.0, 1, 0.70261, slippage=0.5, swap_long_per_lot=-1.27025, swap_short_per_lot=-0.351586, swap_triple_weekday=FRIDAY),
        "HK50": SymbolCosts(6.24, 0.0, 1, 1 / 7.80, slippage=3.12, swap_long_per_lot=-0.611700, swap_short_per_lot=-0.021090, swap_triple_weekday=FRIDAY),
        "BTCUSD": SymbolCosts(
            1.0, 0.0, 1, slippage=0.5, swap_triple_weekday=FRIDAY,
            commission_pct_per_side=FTMO_CRYPTO_COMMISSION_PCT_SIDE,
            swap_long_pct_year=FTMO_CRYPTO_SWAP_PCT_YEAR, swap_short_pct_year=FTMO_CRYPTO_SWAP_PCT_YEAR,
        ),
        "ETHUSD": SymbolCosts(
            0.6, 0.0, 10, slippage=0.3, swap_triple_weekday=FRIDAY,
            commission_pct_per_side=FTMO_CRYPTO_COMMISSION_PCT_SIDE,
            swap_long_pct_year=FTMO_CRYPTO_SWAP_PCT_YEAR, swap_short_pct_year=FTMO_CRYPTO_SWAP_PCT_YEAR,
        ),
        # Binance USD-M futures, regular user (2026-10-15): market fill = taker 0.05 % per side
        # of the notional, no spread, funding every 8 h from data/cache/binance_funding.
        "BTCUSDT": SymbolCosts(0.0, 0.0, 1, commission_pct_per_side=BINANCE_TAKER_FEE, funding=True),
        "ETHUSDT": SymbolCosts(0.0, 0.0, 1, commission_pct_per_side=BINANCE_TAKER_FEE, funding=True),
    }
)  # fmt: skip

# Reference prices of the fixed spreads (rule set by the user, 2026-10-16; risk-management.md ›
# Costs › Spread scaled with the price level): the median of the M1 bid close over the last 60
# cached days of the FTMO MT5 history (data/cache/mt5/<SYM>, 2026-08-16 to 2026-10-14), measured
# on 2026-10-16. The spread used for a fill is spread x fill price / reference price. Binance
# symbols have no spread (no entry here: never scaled).
REFERENCE_PRICES: Mapping[str, float] = MappingProxyType(
    {
        "XAUUSD": 4342.74, "XAGUSD": 64.58, "GBPUSD": 1.348, "GBPJPY": 209.75,
        "EURUSD": 1.15405, "AUDUSD": 0.71185, "NZDUSD": 0.57601, "EURGBP": 0.85688,
        "USDJPY": 158.058, "USDCAD": 1.39191, "USDCHF": 0.81828, "EURJPY": 179.43,
        "NAS100": 29580.48, "US500": 7696.45, "GER40": 25563.64, "UK100": 10720.5,
        "JP225": 66072.5, "EU50": 6316.47, "US30": 52172.25, "US2000": 2890.78,
        "USOIL": 92.499, "UKOIL": 102.245, "NATGAS": 2.876, "DXY": 99.673,
        "BTCUSD": 79679.87, "ETHUSD": 2498.33,
        # V2.6 step 9: 2026-08-28..2026-10-26, measured 2026-10-27
        "AUDJPY": 110.57, "CADJPY": 111.527, "NZDJPY": 89.395, "CHFJPY": 190.36,
        "EURAUD": 1.61278, "GBPAUD": 1.8914, "AUS200": 8755.7, "HK50": 24605.0,
    }
)  # fmt: skip

# Tick snapshot 2026-10-24: results/trading.json has names, no trade_tick_size.
# Fallback 10^-digits from data/sources.py PRICE_DIGITS (expanded FTMO symbols
# measured 2026-10-15; XAUUSD includes histdata precision). No runtime results reads.
# Binance has no recorded exchange tick snapshot: None, explicitly no rounding.
TICK_SIZES: Mapping[str, float | None] = MappingProxyType(
    {
        "XAUUSD": 0.001, "GBPUSD": 0.00001, "GBPJPY": 0.001,
        "EURUSD": 0.00001, "AUDUSD": 0.00001, "NZDUSD": 0.00001,
        "EURGBP": 0.00001, "USDJPY": 0.001, "USDCAD": 0.00001,
        "USDCHF": 0.00001, "EURJPY": 0.001, "XAGUSD": 0.001,
        "NAS100": 0.01, "US500": 0.01, "GER40": 0.01, "UK100": 0.01,
        "JP225": 0.01, "EU50": 0.01, "US30": 0.01, "US2000": 0.01,
        "USOIL": 0.001, "UKOIL": 0.001, "DXY": 0.001, "NATGAS": 0.001,
        "BTCUSD": 0.01, "ETHUSD": 0.01, "BTCUSDT": None, "ETHUSDT": None,
        # V2.6 step 9: FTMO trade_tick_size of 2026-10-27
        "AUDJPY": 0.001, "CADJPY": 0.001, "NZDJPY": 0.001, "CHFJPY": 0.001,
        "EURAUD": 0.00001, "GBPAUD": 0.00001, "AUS200": 0.01, "HK50": 0.01,
    }
)  # fmt: skip

DEFAULT_SYMBOL_COSTS: Mapping[str, SymbolCosts] = MappingProxyType(
    {
        name: replace(costs, reference_price=REFERENCE_PRICES.get(name), tick_size=TICK_SIZES[name])
        for name, costs in _BASE_SYMBOL_COSTS.items()
    }
)


@cache
def default_spread_table() -> SpreadTable:
    """FTMO's median spread by year and New York hour, measured 2026-10-15 (copy of
    data/spreads/ftmo_spread_median.json); the default (rule set by the user, 2026-10-26)."""
    path = Path(__file__).with_name("ftmo_spread_median.json")
    return SpreadTable.from_dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True, slots=True)
class CostConfig:
    spread_enabled: bool = True  # off: no spread; commission/slippage remain independent
    commission_enabled: bool = True  # off: no commission
    swap_enabled: bool = True  # off: swap_r is 0
    symbols: Mapping[str, SymbolCosts] = field(default_factory=lambda: DEFAULT_SYMBOL_COSTS)
    # cost filter: orders with spread + commission above this many R are not filled; 0 = off
    max_cost_r: float = 0.0
    funding_enabled: bool = True  # off: funding_r is 0
    # funding rates by symbol; None: read data/cache/binance_funding/<SYM>.csv when needed
    funding: Mapping[str, FundingSeries] | None = None
    # spread by year and hour of day (ROADMAP 6.7); default the FTMO median table (rule set
    # by the user, 2026-10-26); None: the fixed `SymbolCosts.spread`
    spread_table: SpreadTable | None = field(default_factory=default_spread_table)
    # fixed spread x (fill price / SymbolCosts.reference_price) (rule set by the user,
    # 2026-10-16); False: the plain fixed spread of every year (reproduces old results)
    spread_price_scaling: bool = True
    # TP and limit-entry penetration as a multiple of the trade's spread (0: touch fills)
    tp_penetration: float = 0.5  # default set by the user 2026-10-23
    # Short TP needs ask <= target minus penetration; fills at target without extra spread
    short_tp_on_ask: bool = True  # default set by the user 2026-10-23
    # Round order levels conservatively to the symbol tick (default set by the user 2026-10-26)
    round_to_tick: bool = True

    def __post_init__(self) -> None:
        if not math.isfinite(self.tp_penetration) or self.tp_penetration < 0:
            raise ValueError("tp_penetration must be finite and >= 0")
        if self.max_cost_r < 0:
            raise ValueError("max_cost_r must be >= 0 (0 = off)")

    def for_symbol(self, symbol: str) -> SymbolCosts:
        try:
            return self.symbols[symbol]
        except KeyError:
            raise KeyError(f"no cost settings for {symbol}; add it to CostConfig.symbols") from None

    def spread(self, symbol: str, at: datetime | None = None, price: float = 0.0) -> float:
        """Spread applied to fills (0 when switched off). With a `spread_table` and a time
        `at` it is the table's spread of that time (never scaled); where the table has no
        value (or no time is given) it is the fixed `SymbolCosts.spread`, scaled by
        `price / reference_price` when a `price` > 0 is given, `spread_price_scaling` is on
        and the symbol has a reference price."""
        if not self.spread_enabled:
            return 0.0
        if self.spread_table is not None and at is not None:
            value = self.spread_table.spread_at(symbol, at)
            if value is not None:
                return value
        costs = self.for_symbol(symbol)
        if self.spread_price_scaling and costs.reference_price and price > 0:
            return costs.spread * price / costs.reference_price
        return costs.spread

    def spread_r(
        self, symbol: str, risk: float, at: datetime | None = None, price: float = 0.0
    ) -> float:
        return self.spread(symbol, at, price) / risk

    def slippage(self, symbol: str, price: float = 0.0) -> float:
        """Market-fill slippage, scaled at entry like the fixed spread.

        Spec: risk-management.md > Costs (B4, user, 2026-10-22). Independent of the
        spread switch/table; a synthetic symbol without cost settings has no slippage.
        """
        costs = self.symbols.get(symbol)
        if costs is None:
            return 0.0
        if self.spread_price_scaling and costs.reference_price and price > 0:
            return costs.slippage * price / costs.reference_price
        return costs.slippage

    def commission_price(self, symbol: str, price: float = 0.0) -> float:
        """Round-turn commission as a price distance per lot (0 when switched off). A
        percentage commission needs the `price` (both sides at it)."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        fixed = costs.commission_per_lot / costs.value_per_price_unit
        return fixed + self._pct_price(costs, price, price)

    @staticmethod
    def _pct_price(costs: SymbolCosts, entry: float, exit_price: float) -> float:
        if not costs.commission_pct_per_side:
            return 0.0
        if entry <= 0:
            raise ValueError("a percentage commission needs the entry price")
        return costs.commission_pct_per_side * (entry + exit_price)

    def break_even_offset(
        self,
        symbol: str,
        at: datetime | None = None,
        price: float = 0.0,
        direction: Direction = Direction.BULLISH,
        entry_fill: float | None = None,
    ) -> float:
        """Directional chart distance to a stop that nets zero on the remaining share.

        Spec: risk-management.md > Costs (B6, user, 2026-10-22). Solve
        sign * (exit_fill - entry_fill) = fixed + pct * (entry_fill + exit_fill).
        Swap/funding are excluded; a gap through the stop can still lose money.
        `entry_fill` supplies the actual fill, including a limit entry's zero slippage.
        """
        sign = 1 if direction is Direction.BULLISH else -1
        spread = self.spread(symbol, at, price)
        slip = self.slippage(symbol, price)
        if entry_fill is None:
            entry_fill = price + (spread if sign > 0 else 0.0) + sign * slip
        fixed, pct = 0.0, 0.0
        if self.commission_enabled:
            costs = self.for_symbol(symbol)
            fixed = costs.commission_per_lot / costs.value_per_price_unit
            pct = costs.commission_pct_per_side
            if pct and entry_fill <= 0:
                raise ValueError("a percentage commission needs the entry price")
            if pct >= 1:
                raise ValueError("break-even needs commission_pct_per_side < 1")
        # Solve the distance rather than subtracting nearly equal fill prices.
        fill_distance = (fixed + 2 * pct * entry_fill) / (1 - sign * pct)
        return sign * (entry_fill - price) + fill_distance + slip + (spread if sign < 0 else 0)

    def commission_r(
        self,
        symbol: str,
        risk: float,
        entry: float = 0.0,
        exits: Iterable[tuple[float, float]] | None = None,
    ) -> float:
        """Commission in R for an SL distance of `risk` (price units). `entry` and `exits`
        ((share, fill price) per closed part) are the actual fill notionals of a percentage
        commission; without `exits` the exit notional is taken at the entry price."""
        if not self.commission_enabled:
            return 0.0
        costs = self.for_symbol(symbol)
        fixed = costs.commission_per_lot / costs.value_per_price_unit
        exit_notional = entry if exits is None else sum(share * px for share, px in exits)
        return (fixed + self._pct_price(costs, entry, exit_notional)) / risk

    def too_expensive(
        self,
        symbol: str,
        risk: float,
        at: datetime | None = None,
        entry: float = 0.0,
        entry_fill: float | None = None,
    ) -> bool:
        """Spread + estimated round-turn commission above `max_cost_r` (0: off).

        Spec: risk-management.md > Costs. Estimate both commission notionals at the
        actual entry fill when supplied; spread scaling still uses the chart entry.
        """
        if not self.max_cost_r:
            return False
        notional = entry if entry_fill is None else entry_fill
        cost = self.spread_r(symbol, risk, at, entry) + self.commission_r(symbol, risk, notional)
        return cost > self.max_cost_r + COST_FILTER_TOLERANCE

    def swap_r(
        self,
        symbol: str,
        direction: Direction,
        risk: float,
        entry_time: datetime,
        exits: Iterable[tuple[float, datetime]],
        entry: float = 0.0,
    ) -> float:
        """Swap in R (negative = cost, positive = credit), added to net R only.

        `exits` = (share, exit_time) of each closed part: every part pays the nights between
        the trade's entry and ITS OWN exit time, for its own share of the position. A symbol
        without cost settings has no swap (the spread would already have failed the run).
        A percentage swap (per year, per night) uses the notional at the `entry` price.
        """
        costs = self.symbols.get(symbol)
        if not self.swap_enabled or costs is None:
            return 0.0
        nights = sum(
            share * rollover_nights(entry_time, at, costs.swap_triple_weekday)
            for share, at in exits
        )
        return self.swap_r_nights(symbol, direction, risk, nights, entry)

    def swap_r_nights(
        self, symbol: str, direction: Direction, risk: float, nights: float, entry: float = 0.0
    ) -> float:
        """Swap in R for `nights` (share-weighted, triple nights already counted); linear in
        `nights`, so `swap_r_nights(.., 1.0)` is the swap of one night. `swap_r` calls this."""
        costs = self.symbols.get(symbol)
        if not self.swap_enabled or costs is None:
            return 0.0
        long = direction is Direction.BULLISH
        rate = costs.swap_long_per_lot if long else costs.swap_short_per_lot
        pct = costs.swap_long_pct_year if long else costs.swap_short_pct_year
        usd = nights * rate / (risk * costs.value_per_price_unit)
        if not pct:
            return usd
        if entry <= 0:
            raise ValueError("a percentage swap needs the entry price")
        return usd + nights * pct / DAYS_PER_YEAR * entry / risk

    def funding_series(self, symbol: str) -> FundingSeries | None:
        """Funding rates of `symbol`; None for symbols without funding."""
        costs = self.symbols.get(symbol)
        if not self.funding_enabled or costs is None or not costs.funding:
            return None
        if self.funding is not None and symbol in self.funding:
            return self.funding[symbol]
        path = FUNDING_DIR / f"{symbol}.csv"
        if not path.is_file():
            raise FileNotFoundError(
                f"no funding rates for {symbol}: {path} (download Binance data)"
            )
        return load_funding(path)

    def funding_r(
        self,
        symbol: str,
        direction: Direction,
        risk: float,
        entry_time: datetime,
        exits: Sequence[tuple[float, datetime]],
        entry: float,
    ) -> float:
        """Funding in R (negative = paid), added to net R only. Every part pays the funding
        timestamps between the trade's entry and ITS OWN exit, for its share; longs pay a
        positive rate, shorts receive it; notional approximated at the entry price."""
        series = self.funding_series(symbol)
        if series is None:
            return 0.0
        sign = 1 if direction is Direction.BULLISH else -1
        rates = sum(share * series.rate_sum(entry_time, at) for share, at in exits)
        return -sign * rates * entry / risk
