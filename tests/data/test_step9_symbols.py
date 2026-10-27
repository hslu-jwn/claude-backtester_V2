"""V2.6 step 9: the eight symbols picked by the user on 2026-10-27 (AUDJPY, CADJPY, NZDJPY,
CHFJPY, EURAUD, GBPAUD, AUS200, HK50). FTMO specs read with `tools.mt5_info` the same day
(docs/review/symbol-proposal-2026-10-27.md)."""

import pytest

FX = ["AUDJPY", "CADJPY", "NZDJPY", "CHFJPY", "EURAUD", "GBPAUD"]
INDICES = ["AUS200", "HK50"]
NEW = FX + INDICES


def test_histdata_index_files_map_to_our_names():
    from backtester.data.histdata import SYMBOL_NAMES

    assert SYMBOL_NAMES["AUXAUD"] == "AUS200"
    assert SYMBOL_NAMES["HKXHKD"] == "HK50"


def test_histdata_download_includes_the_new_pairs():
    from backtester.tools.histdata_download import DEFAULT_PAIRS

    assert set(FX + ["AUXAUD", "HKXHKD"]) <= set(DEFAULT_PAIRS)


def test_ftmo_names_of_the_new_indices():
    from backtester.data.mt5_download import DEFAULT_NAMES

    assert DEFAULT_NAMES["AUS200"] == "AUS200.cash"
    assert DEFAULT_NAMES["HK50"] == "HK50.cash"
    assert all(s not in DEFAULT_NAMES for s in FX)  # same name on FTMO


@pytest.mark.parametrize(
    ("symbol", "digits"),
    [("AUDJPY", 3), ("CADJPY", 3), ("NZDJPY", 3), ("CHFJPY", 3), ("EURAUD", 5), ("GBPAUD", 5),
     ("AUS200", 2), ("HK50", 2)],
)  # fmt: skip
def test_price_digits_are_ftmos(symbol, digits):
    from backtester.data.sources import PRICE_DIGITS

    assert PRICE_DIGITS[symbol] == digits


@pytest.mark.parametrize("symbol", NEW)
def test_histdata_first_and_mt5_preferred_day_by_day(symbol):
    from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR
    from backtester.data.sources import DEFAULT_SOURCES

    assert DEFAULT_SOURCES.cache_dir(symbol) == DEFAULT_CACHE_DIR
    assert DEFAULT_SOURCES.preferred_dirs[symbol] == MT5_CACHE_DIR


# --- costs: FTMO symbol_info 2026-10-27; spread / reference price = median M1 bar spread / bid
# close of the last 60 calendar days of data/cache/mt5 (2026-08-28..2026-10-26), the method of
# risk-management.md > Costs (reproduces the stored EURJPY / GBPJPY / AUDUSD values) ----------

COSTS = [  # symbol, spread, commission, contract, quote_to_usd, swap long, swap short, triple
    ("AUDJPY", 0.009, 5.0, 100_000, 0.00634111, 2.24475, -8.44636, 2),
    ("CADJPY", 0.007, 5.0, 100_000, 0.00634111, 0.317056, -3.62077, 2),
    ("NZDJPY", 0.009, 5.0, 100_000, 0.00634111, 0.488265, -3.45590, 2),
    ("CHFJPY", 0.015, 5.0, 100_000, 0.00634111, -7.57129, 1.13506, 2),
    ("EURAUD", 0.00006, 5.0, 100_000, 0.70261, -9.52739, 1.27875, 2),
    ("GBPAUD", 0.00011, 5.0, 100_000, 0.70261, -9.41497, -0.878263, 2),
    ("AUS200", 1.0, 0.0, 1, 0.70261, -1.27025, -0.351586, 4),
    # HK50: the terminal had no HKD rate (tick value 0): the USD peg's midpoint 1 / 7.80
    ("HK50", 6.24, 0.0, 1, 1 / 7.80, -0.611700, -0.021090, 4),
]


@pytest.mark.parametrize(
    ("symbol", "spread", "commission", "contract", "quote", "long", "short", "triple"), COSTS
)
def test_ftmo_costs(symbol, spread, commission, contract, quote, long, short, triple):
    from backtester.engine.costs import DEFAULT_SYMBOL_COSTS

    c = DEFAULT_SYMBOL_COSTS[symbol]
    assert c.spread == pytest.approx(spread)
    assert c.slippage == pytest.approx(spread / 2)  # half the spread, like the others
    assert c.commission_per_lot == commission and c.contract_size == contract
    assert c.quote_to_usd == pytest.approx(quote, rel=1e-4)
    assert c.swap_long_per_lot == pytest.approx(long, abs=1e-4)
    assert c.swap_short_per_lot == pytest.approx(short, abs=1e-4)
    assert c.swap_triple_weekday == triple


@pytest.mark.parametrize(
    ("symbol", "reference", "tick"),
    [("AUDJPY", 110.57, 0.001), ("CADJPY", 111.527, 0.001), ("NZDJPY", 89.395, 0.001),
     ("CHFJPY", 190.36, 0.001), ("EURAUD", 1.61278, 0.00001), ("GBPAUD", 1.8914, 0.00001),
     ("AUS200", 8755.7, 0.01), ("HK50", 24605.0, 0.01)],
)  # fmt: skip
def test_reference_price_and_tick_size(symbol, reference, tick):
    from backtester.engine.costs import DEFAULT_SYMBOL_COSTS

    c = DEFAULT_SYMBOL_COSTS[symbol]
    assert c.reference_price == pytest.approx(reference) and c.tick_size == pytest.approx(tick)


def test_the_new_symbols_have_no_spread_table_rows():
    # the default median table is not re-measured (that would change the 26 others' costs):
    # the new symbols use the fixed spread, scaled with the price
    from backtester.engine.costs import CostConfig

    table = CostConfig().spread_table
    from datetime import UTC, datetime

    at = datetime(2026, 10, 1, 15, tzinfo=UTC)
    assert all(table.spread_at(s, at) is None for s in NEW)


# --- classes, sessions, news ----------------------------------------------------------------


def test_market_classes():
    from backtester.analytics.market_classes import MARKET_CLASSES

    assert all(MARKET_CLASSES[s] == "FX" for s in FX)
    assert MARKET_CLASSES["AUS200"] == MARKET_CLASSES["HK50"] == "AU/HK indices"


def test_opening_range_trades_the_crosses_in_the_fx_sessions():
    # spec strategy-opening-range.md > Sessions: "FX, XAUUSD, XAGUSD"
    from backtester.strategy.opening_range.config import SYMBOL_CLASS

    assert all(SYMBOL_CLASS[s] == "fx_metal" for s in FX)
    assert "AUS200" not in SYMBOL_CLASS and "HK50" not in SYMBOL_CLASS  # sessions: the user's call


def test_news_currencies():
    from backtester.data.news import NewsConfig

    news = NewsConfig().instruments
    assert news["EURAUD"].currencies == "EUR,AUD" and news["EURAUD"].countries == "EU,AU"
    assert news["GBPAUD"].currencies == "GBP,AUD" and news["NZDJPY"].countries == "NZ,JP"
    assert news["AUS200"].currencies == "AUD" and news["AUS200"].countries == "AU"
    assert "HK50" not in news  # no HKD / HK in the calendar's countries yet
