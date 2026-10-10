"""Trading costs in R: a fixed spread per symbol and a commission per lot.

Spec: ROADMAP.md › 3.1, risk-management.md › Costs. Candles are bid prices (histdata.com
has no asks, so the spread is always this fixed setting). Longs enter at ask (bid + spread) and exit
at bid; shorts enter at bid and exit at ask, so every round trip pays one spread. The
commission is a dollar amount per lot (round turn), so in R it depends on the SL distance:

    commission_R = commission per lot / (SL distance x value of a 1.0 price move per lot)

The values are rough estimates (FTMO publishes no fixed spreads); both costs can be
switched off so backtests can compare gross and net results.

Slippage and swap are stored per symbol here (risk-management.md › Costs) but not yet
applied: the account simulator (`risk/`, Phase 5) will use them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


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
        # matters for the commission; check it with `data.mt5_info` before Phase 5.
        "NAS100": SymbolCosts(spread=1.0, commission_per_lot=0.0, contract_size=1, slippage=1.0),
        "US500": SymbolCosts(spread=0.5, commission_per_lot=0.0, contract_size=1, slippage=0.25),
    }
)


@dataclass(frozen=True, slots=True)
class CostConfig:
    spread_enabled: bool = True  # off: no spread on fills (gross = net apart from commission)
    commission_enabled: bool = True  # off: no commission
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
