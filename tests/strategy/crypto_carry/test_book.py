"""Hand-calculated weekly carry books, including settlement boundaries."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from backtester.engine.costs import funding_from_rows
from backtester.strategy.crypto_carry.book import (
    CryptoCarryConfig,
    pick_legs,
    signal,
    week_result,
)

MONDAY = datetime(2026, 1, 5, tzinfo=UTC)
EXIT = MONDAY + timedelta(days=7, minutes=-1)


def history(rate=0.0001, hours=8):
    return [(MONDAY - timedelta(hours=i), rate) for i in range(0, 31 * 24 + 1, hours)]


def book_fixture():
    signals = {str(i): float(i) for i in range(9)}
    # Long returns 1,2,3,4%; short returns 6,7,8,9%: price = -500 bp.
    prices = {s: {MONDAY: 100.0, EXIT - timedelta(minutes=1): 101.0 + int(s)} for s in signals}
    funding = {
        s: funding_from_rows(
            [
                (MONDAY, 10.0),  # excluded: before entry
                (MONDAY + timedelta(minutes=1), 10.0),  # excluded: exactly entry
                (MONDAY + timedelta(hours=8), (int(s) + 1) * 0.0001),
                (MONDAY + timedelta(days=6, hours=16), (int(s) + 1) * 0.0001),
                (MONDAY + timedelta(days=7), 10.0),  # excluded: after exit
            ]
        )
        for s in signals
    }
    return signals, prices, funding


def test_config_frozen():
    cfg = CryptoCarryConfig()
    assert (cfg.n_leg, cfg.lookback_days, cfg.min_history_days, cfg.min_rates, cfg.r_bp) == (
        4,
        7,
        30,
        21,
        1000.0,
    )
    assert len(cfg.symbols) == 17
    assert cfg.symbols[:3] == ("BTCUSDT", "ETHUSDT", "BCHUSDT")
    with pytest.raises(FrozenInstanceError):
        cfg.n_leg = 3


@pytest.mark.parametrize("hours,count", [(8, 21), (4, 42)])
def test_signal_window(hours, count):
    rows = history(hours=hours)
    assert signal(funding_from_rows(rows), MONDAY) == pytest.approx(count * 0.0001)
    rows += [(MONDAY + timedelta(seconds=1), 999.0)]
    assert signal(funding_from_rows(rows), MONDAY) == pytest.approx(count * 0.0001)


def test_signal_eligibility():
    assert signal(funding_from_rows(history()[:21]), MONDAY) is None
    assert signal(funding_from_rows(history()[::5][:20]), MONDAY) is None
    assert signal(funding_from_rows([]), MONDAY) is None
    rows = [(MONDAY - timedelta(days=30), 0.0)] + history()[:20]
    assert signal(funding_from_rows(rows), MONDAY) is not None


def test_pick_legs():
    assert pick_legs({str(i): float(i) for i in reversed(range(9))}) == (
        ["0", "1", "2", "3"],
        ["5", "6", "7", "8"],
    )
    # ties keep the input (universe) order, as in the tested screen (spec A5)
    assert pick_legs({s: 0.0 for s in reversed("abcdefghi")}) == (list("ihgf"), list("dcba"))
    tied = {
        "z": 1.0,
        "a": 1.0,
        "m": 1.0,
        "b": 0.0,
        "c": 0.0,
        "d": 0.0,
        "e": 0.0,
        "f": 2.0,
        "g": 3.0,
    }
    assert pick_legs(tied) == (["b", "c", "d", "e"], ["a", "m", "f", "g"])
    assert pick_legs({str(i): float(i) for i in range(7)}) is None


def test_exact_week():
    signals, prices, funding = book_fixture()
    result = week_result(MONDAY, signals, prices, funding)
    trade = result.trade
    assert trade["entry_time"] == MONDAY + timedelta(minutes=1)
    assert trade["exit_time"] == EXIT
    # Funding: short mean 15 bp minus long mean 5 bp = +10 bp.
    for key, value in {
        "price_bp": -500.0,
        "funding_bp": 10.0,
        "cost_bp": 20.0,
        "net_bp": -510.0,
        "r_gross": -0.49,
        "r_net": -0.51,
        "n_long": 4,
        "n_short": 4,
    }.items():
        assert trade[key] == pytest.approx(value)
    assert trade["longs"] == "0 1 2 3"
    assert trade["shorts"] == "5 6 7 8"
    short = next(row for row in result.legs if row["symbol"] == "8")
    assert short["funding_bp"] == pytest.approx(18.0)
    long = next(row for row in result.legs if row["symbol"] == "0")
    assert long["funding_bp"] == pytest.approx(-2.0)


@pytest.mark.parametrize("missing", [MONDAY, EXIT - timedelta(minutes=1)])
def test_missing_bar_drops_member(missing):
    signals, prices, funding = book_fixture()
    del prices["0"][missing]
    result = week_result(MONDAY, signals, prices, funding)
    assert result.trade["n_long"] == 3
    assert result.trade["longs"] == "1 2 3"
    assert result.trade["price_bp"] == pytest.approx(-450.0)
    assert next(r for r in result.legs if r["symbol"] == "0")["dropped"]
    for s in "123":
        prices[s] = {}
    result = week_result(MONDAY, signals, prices, funding)
    assert result.trade is None
    assert "empty" in result.skipped


def test_future_data_does_not_change_week():
    signals, prices, funding = book_fixture()
    before = week_result(MONDAY, signals, prices, funding)
    for s in prices:
        prices[s][MONDAY + timedelta(days=8)] = 999999.0
        funding[s] = funding_from_rows(
            list(zip(funding[s].times, funding[s].rates)) + [(MONDAY + timedelta(days=8), 999.0)]
        )
    assert week_result(MONDAY, signals, prices, funding) == before
