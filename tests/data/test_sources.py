"""Per-symbol data sources. Spec: ARCHITECTURE.md › Data sources."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from m1_frames import m1

from backtester.data.cache import cache_path
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.ui.pages.chart import base_payload


def write_day(cache_dir: Path, symbol: str, day: str, price: float) -> None:
    path = cache_path(cache_dir, symbol, date.fromisoformat(day))
    path.parent.mkdir(parents=True, exist_ok=True)
    m1(("10:00", price, price + 1, price - 1, price, 1.0, 0.1), day=day).to_parquet(path)


@pytest.fixture
def sources(tmp_path):
    """Gold in one folder, GBPUSD in another; GBPJPY mapped but nothing cached."""
    gold, fx = tmp_path / "dukascopy", tmp_path / "histdata"
    write_day(gold, "XAUUSD", "2026-09-01", 4400.0)
    write_day(fx, "GBPUSD", "2026-09-02", 1.3)
    write_day(gold, "GBPUSD", "2026-09-01", 99.0)  # wrong source: must never be read
    return SymbolSources({"XAUUSD": gold, "GBPUSD": fx, "GBPJPY": fx})


def test_default_reads_gold_from_dukascopy_and_gbp_pairs_from_histdata():
    assert DEFAULT_SOURCES.cache_dir("XAUUSD") == Path("data/cache/histdata")
    assert DEFAULT_SOURCES.cache_dir("GBPUSD") == Path("data/cache/histdata")
    assert DEFAULT_SOURCES.cache_dir("GBPJPY") == Path("data/cache/histdata")
    assert DEFAULT_SOURCES.cache_dir("NAS100") == Path("data/cache/histdata")
    assert DEFAULT_SOURCES.cache_dir("US500") == Path("data/cache/histdata")


def test_symbols_with_cached_days_each_from_its_own_folder(sources):
    assert sources.available_symbols() == ["GBPUSD", "XAUUSD"]
    assert sources.cached_days("GBPUSD") == [date(2026, 9, 2)]


def test_unmapped_symbol_says_where_to_add_it(sources):
    with pytest.raises(KeyError, match="EURUSD.*data/sources.py"):
        sources.cache_dir("EURUSD")


def test_equal_sources_hash_equal_for_the_page_cache(tmp_path):
    a = SymbolSources({"XAUUSD": tmp_path, "GBPUSD": str(tmp_path)})
    b = SymbolSources({"GBPUSD": tmp_path, "XAUUSD": tmp_path})
    assert a == b and hash(a) == hash(b)


def test_single_folder_override(tmp_path):
    s = SymbolSources.single(tmp_path, ["XAUUSD", "GBPUSD"])
    assert s.cache_dir("GBPUSD") == s.cache_dir("XAUUSD") == tmp_path


def test_chart_shows_each_symbol_from_its_source(sources):
    gold, _ = base_payload(sources, "XAUUSD", "M5", "2026-09-01", "2026-09-01")
    fx, message = base_payload(sources, "GBPUSD", "M5", "2026-09-02", "2026-09-02")
    assert gold["candles"]["h"] == [4401.0]
    assert fx["candles"]["h"] == [1.3 + 1] and "1 M5 candles" in message


def test_cached_block_is_the_run_of_consecutive_cached_days():
    from datetime import date, timedelta

    from backtester.data.sources import cached_block

    d = date(2026, 9, 1)
    cached = {d + timedelta(days=i) for i in (0, 1, 2, 4, 5)}
    assert cached_block(cached, d + timedelta(days=1)) == (d, d + timedelta(days=2))
    assert cached_block(cached, d + timedelta(days=5)) == (
        d + timedelta(days=4),
        d + timedelta(days=5),
    )
    with pytest.raises(KeyError):
        cached_block(cached, d + timedelta(days=3))


# --- ROADMAP 11.8 / 11.9: more symbols -------------------------------------------------

HISTDATA_NAMES = [
    "EURUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "NZDUSD",
    "EURJPY",
    "EURGBP",
    "XAGUSD",
    "GER40",
    "UK100",
    "JP225",
    "EU50",
    "USOIL",
    "UKOIL",
    "DXY",
]
MT5_ONLY_NAMES = ["US30", "US2000", "NATGAS", "BTCUSD", "ETHUSD"]
BINANCE_NAMES = ["BTCUSDT", "ETHUSDT"]


@pytest.mark.parametrize("symbol", HISTDATA_NAMES)
def test_new_histdata_symbols_default_to_histdata(symbol):
    assert DEFAULT_SOURCES.cache_dir(symbol) == Path("data/cache/histdata")


@pytest.mark.parametrize("symbol", MT5_ONLY_NAMES)
def test_symbols_only_on_ftmo_default_to_the_mt5_cache(symbol):
    assert DEFAULT_SOURCES.cache_dir(symbol) == Path("data/cache/mt5")


@pytest.mark.parametrize("symbol", BINANCE_NAMES)
def test_binance_symbols_default_to_the_binance_cache(symbol):
    assert DEFAULT_SOURCES.cache_dir(symbol) == Path("data/cache/binance")


def test_every_default_symbol_has_price_digits_and_costs():
    from backtester.data.sources import PRICE_DIGITS
    from backtester.engine.costs import DEFAULT_SYMBOL_COSTS

    assert set(DEFAULT_SOURCES.symbols) == set(PRICE_DIGITS) == set(DEFAULT_SYMBOL_COSTS)
    assert len(PRICE_DIGITS) == 5 + 16 + 5 + 2


def test_the_original_five_symbols_keep_their_digits():
    from backtester.data.sources import PRICE_DIGITS

    original = {"XAUUSD": 3, "GBPUSD": 5, "GBPJPY": 3, "NAS100": 2, "US500": 2}
    assert {s: PRICE_DIGITS[s] for s in original} == original


@pytest.mark.parametrize(
    ("symbol", "digits"),
    [("EURUSD", 5), ("USDJPY", 3), ("XAGUSD", 3), ("GER40", 2), ("USOIL", 3), ("DXY", 3),
     ("NATGAS", 3), ("BTCUSD", 2), ("BTCUSDT", 2)],
)  # fmt: skip
def test_new_price_digits(symbol, digits):
    from backtester.data.sources import PRICE_DIGITS

    assert PRICE_DIGITS[symbol] == digits
