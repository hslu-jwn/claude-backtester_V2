"""Research CLI integration, forward immutability and cached-data golden check."""

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest
from m1_frames import m1

from backtester.data.cache import cache_path, write_atomic
from backtester.data.sources import BINANCE_CACHE_DIR, SymbolSources
from backtester.engine.costs import funding_from_rows
from backtester.strategy.crypto_carry.book import CryptoCarryConfig
from backtester.tools import crypto_carry as tool


def test_forward_append_only(tmp_path):
    path = tmp_path / "forward.csv"
    row = dict(
        zip(
            tool.TRADE_COLUMNS,
            [
                "2026-11-16T00:01:00+00:00",
                "2026-11-22T23:59:00+00:00",
                0.1,
                0.08,
                100.0,
                0.0,
                20.0,
                80.0,
                "A",
                "B",
                1,
                1,
            ],
        )
    )
    tool.append_forward(path, [row])
    original = path.read_bytes()
    tool.append_forward(path, [dict(row, net_bp=80.0 + 1e-10)])
    assert path.read_bytes() == original
    new = dict(row, entry_time="2026-11-23T00:01:00+00:00", exit_time="2026-11-29T23:59:00+00:00")
    tool.append_forward(path, [row, new])
    assert path.read_bytes().startswith(original)
    existing = path.read_bytes()
    with pytest.raises(ValueError, match="2026-11-16"):
        tool.append_forward(path, [dict(row, r_net=0.09), new])
    assert path.read_bytes() == existing


def test_weeks_cache_and_completion(tmp_path):
    monday = datetime(2026, 1, 5, tzinfo=UTC)
    exit_ = monday + timedelta(days=7, minutes=-1)
    symbols = tuple(str(i) for i in range(9))
    funding = {}
    for i, sym in enumerate(symbols):
        for day, hhmm, price in [
            (monday.date(), "00:00", 100.0),
            (exit_.date(), "23:58", 101.0 + i),
        ]:
            write_atomic(
                m1((hhmm, price, price, price, price, 1.0, 0.0), day=str(day)),
                cache_path(tmp_path, sym, day),
            )
        funding[sym] = funding_from_rows(
            [(monday - timedelta(hours=h), i * 0.0001) for h in range(0, 31 * 24 + 1, 8)]
            + [(exit_, i * 0.0001)]
        )
    sources = SymbolSources.single(tmp_path, symbols)
    trades, legs, skipped = tool.compute_weeks(
        funding, sources, date(2026, 1, 1), date(2026, 1, 11)
    )
    assert len(trades) == 1
    assert len(legs) == 8
    assert skipped == []
    assert trades[0]["price_bp"] == pytest.approx(-500.0)
    assert tool.compute_weeks(funding, sources, date(2026, 1, 6), date(2026, 1, 11))[0] == []
    assert tool.compute_weeks(funding, sources, date(2026, 1, 1), date(2026, 1, 10))[0] == []
    # Default end requires coverage through exit for every eligible symbol, even unpicked 4.
    funding["4"] = funding_from_rows(
        [(monday - timedelta(hours=h), 0.0) for h in range(0, 31 * 24 + 1, 8)]
    )
    assert tool.compute_weeks(funding, sources, date(2026, 1, 1))[0] == []


@pytest.mark.parametrize(
    "start,end,count,mean,t",
    [
        (date(2020, 2, 17), date(2021, 9, 12), 82, 138.0, None),
        (date(2021, 9, 20), date(2026, 10, 25), 266, 112.0, 2.93),
    ],
)
def test_golden(start, end, count, mean, t):
    if not (BINANCE_CACHE_DIR / "XTZUSDT").is_dir():
        pytest.skip("crypto carry golden requires data/cache/binance/XTZUSDT")
    cfg = CryptoCarryConfig()
    funding = tool.read_funding(cfg.symbols)
    trades, _, skipped = tool.compute_weeks(
        funding, SymbolSources.single(BINANCE_CACHE_DIR, cfg.symbols), start, end
    )
    net = np.array([r["net_bp"] for r in trades])
    actual_t = net.mean() / net.std(ddof=1) * np.sqrt(len(net))
    print(f"golden {start}..{end}: n={len(net)} mean={net.mean():.8f} t={actual_t:.8f}")
    assert skipped == []
    assert len(net) == count
    assert abs(net.mean() - mean) < 0.05
    if t is not None:
        assert abs(actual_t - t) < 0.005


def test_empty_cached_day_is_missing_bar(tmp_path):
    from backtester.data.cache import empty_cache_frame

    monday = datetime(2026, 1, 5, tzinfo=UTC)
    symbols = tuple(str(i) for i in range(8))
    funds = {
        s: funding_from_rows(
            [(monday - timedelta(hours=h), int(s) * 0.0001) for h in range(0, 31 * 24 + 1, 8)]
        )
        for s in symbols
    }
    for s in symbols:
        write_atomic(empty_cache_frame(), cache_path(tmp_path, s, monday.date()))
    trades, legs, skipped = tool.compute_weeks(
        funds, SymbolSources.single(tmp_path, symbols), monday.date(), date(2026, 1, 11)
    )
    assert trades == []
    assert len(legs) == 8
    assert all(r["dropped"] for r in legs)
    assert "empty leg" in skipped[0][1]


def test_invalid_price_and_signal():
    from backtester.strategy.crypto_carry.book import pick_legs, week_result

    with pytest.raises(ValueError, match="non-finite"):
        pick_legs({"A": float("nan")})
    monday = datetime(2026, 1, 5, tzinfo=UTC)
    syms = {str(i): float(i) for i in range(8)}
    prices = {s: {monday: 0.0, monday + timedelta(days=7, minutes=-2): 100.0} for s in syms}
    funds = {s: funding_from_rows([]) for s in syms}
    with pytest.raises(ValueError, match="positive"):
        week_result(monday, syms, prices, funds)


def test_delisted_symbol_does_not_stall_the_forward_log(tmp_path):
    """A symbol whose funding stopped more than 7 days before Monday (delisted) stays in the frozen
    ranking (signal 0, dropped for missing bars) but must not hold back the completeness check."""
    monday = datetime(2026, 1, 5, tzinfo=UTC)
    exit_ = monday + timedelta(days=7, minutes=-1)
    symbols = tuple(str(i) for i in range(10))
    funding = {}
    for i, sym in enumerate(symbols):
        if sym != "9":
            for day, hhmm, price in [
                (monday.date(), "00:00", 100.0),
                (exit_.date(), "23:58", 101.0),
            ]:
                write_atomic(
                    m1((hhmm, price, price, price, price, 1.0, 0.0), day=str(day)),
                    cache_path(tmp_path, sym, day),
                )
        last = monday - timedelta(days=8) if sym == "9" else exit_
        funding[sym] = funding_from_rows(
            [
                (monday - timedelta(hours=h), (i + 1) * 0.0001)
                for h in range(0, 40 * 24 + 1, 8)
                if monday - timedelta(hours=h) <= last
            ]
            + ([(exit_, (i + 1) * 0.0001)] if sym != "9" else [])
        )
    trades, _, skipped = tool.compute_weeks(
        funding, SymbolSources.single(tmp_path, symbols), monday.date()
    )
    assert len(trades) == 1 and skipped == []
    # A feed that lags for every symbol (no rate after the exit anywhere) holds later weeks back.
    later = tool.compute_weeks(funding, SymbolSources.single(tmp_path, symbols), monday.date())
    assert len(later[0]) == 1 and later[2] == []
    lagging = {
        s: funding_from_rows(list(zip(f.times[:-30], f.rates[:-30], strict=True)))
        for s, f in funding.items()
    }
    held = tool.compute_weeks(lagging, SymbolSources.single(tmp_path, symbols), monday.date())
    assert held[0] == [] and held[2] == []


def test_cost_matches_the_engine_fee():
    from backtester.engine.costs import BINANCE_TAKER_FEE
    from backtester.strategy.crypto_carry.book import DEFAULT

    assert DEFAULT.cost_bp == pytest.approx(2 * 2 * BINANCE_TAKER_FEE * 1e4)
