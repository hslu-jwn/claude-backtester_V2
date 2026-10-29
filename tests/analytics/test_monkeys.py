"""Spec: risk-management.md > Matched monkeys.

Test-case list (written before implementation):
- Per-symbol count, long count, paired stop/hold permutations (1), independent holds (2/3).
- Uniform candidate sampling stays inside the observed NY window, close fills, later exits.
- Seed reproducibility; ties half credit; DD exit ordering and initial zero peak.
- Perfect foresight beats random entries; seeded random source is near the middle.
- Hand-calculated costs and gap stop; reuse entry-screen replay.
- Empty / invalid input and missing data explicit; CLI period guard, workers, runner opt-out.
- MC verdict uses monkey 1 except existing kind B precedence; runner diagnostics never select.
"""

from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from backtester.analytics.entry_screen import M1Data, ScreenTrade, _window_candidates
from backtester.analytics.monkeys import (
    MonkeyConfig,
    draw_run,
    matched_monkeys,
    replay,
    statistics,
)
from backtester.core.models import Candle, Direction
from backtester.engine.costs import CostConfig, SymbolCosts

AT = datetime(2020, 1, 6, 14, tzinfo=UTC)
MIN = timedelta(minutes=1)
FREE = CostConfig(symbols={"X": SymbolCosts(0, 0, 1), "Y": SymbolCosts(0, 0, 1)})


def data(prices=None):
    prices = prices if prices is not None else [100.0] * 90
    return M1Data.from_candles([Candle(AT + i * MIN, p, p, p, p) for i, p in enumerate(prices)])


def trades(symbol="X"):
    return [
        ScreenTrade(
            symbol,
            Direction.BULLISH if i % 3 else Direction.BEARISH,
            AT + (i + 1) * MIN,
            100.0,
            100.0 - (1 if i % 3 else -1) * (i + 1),
            AT + (2 * i + 2) * MIN,
            0.0,
        )
        for i in range(8)
    ]


@pytest.mark.parametrize("kind", [1, 2, 3])
def test_exact_per_symbol_marginals_and_windows(kind):
    original = trades() + trades("Y")
    m1s = {"X": data(), "Y": data()}
    drawn = draw_run(original, m1s, kind, np.random.default_rng(42), MonkeyConfig())
    for symbol, m1 in m1s.items():
        real = [t for t in original if t.symbol == symbol]
        fake = [t for t in drawn if t.symbol == symbol]
        assert len(fake) == len(real)
        assert Counter(t.direction for t in fake) == Counter(t.direction for t in real)
        pair = lambda t: (t.risk, (t.exit_time - t.entry_time).total_seconds())
        assert Counter(t.risk for t in fake) == Counter(t.risk for t in real)
        assert Counter(pair(t)[1] for t in fake) == Counter(pair(t)[1] for t in real)
        if kind == 1:
            assert Counter(map(pair, fake)) == Counter(map(pair, real))
        else:
            assert list(map(pair, fake)) != list(map(pair, real))
        if kind == 2:
            assert [(t.entry_time, t.entry, t.initial_stop) for t in fake] == [
                (t.entry_time, t.entry, t.initial_stop) for t in real
            ]
        else:
            allowed = set(m1.close_s[_window_candidates(m1, [t.entry_time for t in real], 15)])
            assert all(t.entry_time.timestamp() in allowed for t in fake)
            assert all(t.entry == 100.0 for t in fake)
        assert all(r.exit_time > t.entry_time for t, r in zip(fake, replay(fake, m1s, FREE)))


def test_seed_and_ties():
    cfg = MonkeyConfig(runs=20)
    a = matched_monkeys(trades(), {"X": data()}, FREE, cfg)
    assert a == matched_monkeys(trades(), {"X": data()}, FREE, cfg)
    for kind in a["kinds"]:
        assert kind["net_r"]["percentile"] == 50
        assert kind["max_dd_r"]["percentile"] == 50
        assert not kind["passed"]


def test_exit_order_and_zero_peak():
    assert statistics([2, -3, 2], [3, 1, 2]) == (1.0, 3.0)
    assert statistics([2, -3, 2], [1, 2, 3]) == (1.0, 3.0)
    assert statistics([-2, 3], [1, 2]) == (1.0, 2.0)
    assert statistics([3, -2], [1, 2]) == (1.0, 2.0)
    assert statistics([-2, 3, -2], [1, 2, 3]) == (-1.0, 2.0)
    assert statistics([-2, 3, -2], [1, 3, 2]) == (-1.0, 4.0)


def test_hand_computed_costs_gap_and_no_entry_bar_exit():
    # Entry bar low is 100; later candle opens at 97, beyond stop 98.
    m1 = data([100, 97, 97])
    t = ScreenTrade("X", Direction.BULLISH, AT + MIN, 100, 98, AT + 2 * MIN, 0)
    costs = CostConfig(symbols={"X": SymbolCosts(0.2, 0.1, 1)})
    result = replay([t], {"X": m1}, costs)[0]
    assert result.exit_time == AT + 2 * MIN
    assert result.exit_price == 97
    assert result.r_net == pytest.approx((-3 - 0.2 - 0.1) / 2)


def test_swap_commission_and_slippage_hand_computed():
    # Cross Monday's NY 17:00 rollover, +1 gross R, spread .2, two slips .1 each,
    # fixed commission .1, one night swap -.4 price units; initial risk = 2.
    stamps = np.array([AT.timestamp(), (AT + timedelta(hours=9)).timestamp()])
    prices = np.array([100.0, 102.0])
    m1 = M1Data(stamps, prices, prices, prices, prices)
    t = ScreenTrade("X", Direction.BULLISH, AT + MIN, 100, 98, AT + timedelta(hours=10), 0)
    costs = CostConfig(
        symbols={"X": SymbolCosts(0.2, 0.1, 1, slippage=0.1, swap_long_per_lot=-0.4)}
    )
    result = replay([t], {"X": m1}, costs)[0]
    assert result.swap_r == pytest.approx(-0.2)
    assert result.r_net == pytest.approx((2 - 0.2 - 0.2 - 0.1 - 0.4) / 2)


def test_standalone_writes_report_and_one_source_trial(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    from backtester.analytics.trial_log import family_trials
    from backtester.tools import monkeys

    monkeypatch.setattr(monkeys, "load_m1", lambda *a: data())
    monkeypatch.setattr(monkeys, "run_period", lambda *a: SimpleNamespace(trades=trades("XAUUSD")))
    assert (
        monkeys.main(
            [
                "--strategy",
                "trend_following",
                "--symbols",
                "XAUUSD",
                "--runs",
                "3",
                "--out",
                str(tmp_path),
            ]
        )
        == 0
    )
    [folder] = list(tmp_path.glob("trend_following_*"))
    summary = json.loads((folder / "summary.json").read_text())
    assert len(summary["variants"][0]["kinds"]) == 3
    assert "Favorable percentile" in (folder / "report.md").read_text()
    assert len(family_trials("monkeys_trend_following")) == 1


def test_planted_foresight_and_random_source():
    rng = np.random.default_rng(21)
    prices = 100 + np.cumsum(rng.choice([-1.0, 1.0], 2000))
    m1 = data(prices)
    # Equal one-minute holds, stops too wide to hit. Foresight picks the next move.
    original = []
    for i in range(1, 1800, 10):
        sign = 1 if prices[i + 1] > prices[i] else -1
        original.append(
            ScreenTrade(
                "X",
                Direction.BULLISH if sign > 0 else Direction.BEARISH,
                AT + (i + 1) * MIN,
                prices[i],
                prices[i] - sign * 100,
                AT + (i + 2) * MIN,
                0.01,
            )
        )
    cfg = MonkeyConfig(runs=100)
    result = matched_monkeys(original, {"X": m1}, FREE, cfg)
    assert result["kinds"][0]["net_r"]["percentile"] >= 99
    random_source = draw_run(original, {"X": m1}, 1, np.random.default_rng(17), cfg)
    random_source = [
        replace(t, r_net=r.r_net, exit_time=r.exit_time)
        for t, r in zip(random_source, replay(random_source, {"X": m1}, FREE))
    ]
    result = matched_monkeys(random_source, {"X": m1}, FREE, cfg)
    assert 10 < result["kinds"][0]["net_r"]["percentile"] < 90


def test_empty_and_invalid():
    assert not matched_monkeys([], {}, FREE, MonkeyConfig(runs=2))["available"]
    with pytest.raises(ValueError, match="X"):
        matched_monkeys(trades(), {}, FREE)
    with pytest.raises(ValueError):
        matched_monkeys([replace(trades()[0], initial_stop=100)], {"X": data()}, FREE)
    with pytest.raises(ValueError):
        MonkeyConfig(runs=0)


def test_cli_guard_and_sequential_default():
    from backtester.tools.monkeys import main, parse_args

    assert parse_args(["--strategy", "trend_following"]).workers == 1
    with pytest.raises(SystemExit, match="test period"):
        main(["--strategy", "trend_following", "--end", "2021-09-14"])


def test_grid_option_and_identity(tmp_path):
    from backtester.tools.research_grid import GridError, expand, grid_id, load_grid

    path = tmp_path / "grid.toml"
    path.write_text('strategy = "trend_following"\nsymbols = ["XAUUSD"]\n')
    enabled = load_grid(path)
    assert enabled.monkeys
    path.write_text(path.read_text() + "monkeys = false\n")
    disabled = load_grid(path)
    assert not disabled.monkeys
    assert grid_id(enabled, expand(enabled)[0]) == grid_id(disabled, expand(disabled)[0])
    path.write_text(path.read_text().replace("false", '"false"'))
    with pytest.raises(GridError, match="monkeys"):
        load_grid(path)


def test_verdict_precedence():
    from types import SimpleNamespace

    from backtester.analytics.verdict import random_entry_percentile

    monkey = {"available": True, "kinds": [{"net_r": {"percentile": 91.0}}]}
    baseline = SimpleNamespace(percentile=97.0)
    assert random_entry_percentile("gap_fade", baseline, monkey) == 97
    assert random_entry_percentile("trend_following", None, monkey) == 91
    assert random_entry_percentile("gap_momentum", baseline, monkey) == 91
    assert random_entry_percentile("gap_fade", None, monkey) == 91
    assert random_entry_percentile("trend_following", None, None) is None


def test_parallel_monkeys_match_serial():
    cfg = MonkeyConfig(runs=12)
    assert matched_monkeys(trades(), {"X": data()}, FREE, cfg, workers=1) == matched_monkeys(
        trades(), {"X": data()}, FREE, cfg, workers=3
    )


def test_serial_monkeys_do_not_create_pool(monkeypatch):
    import backtester.analytics.monkeys as module

    def forbidden(*args, **kwargs):
        pytest.fail("serial execution must not create a pool")

    monkeypatch.setattr(module, "ProcessPoolExecutor", forbidden)
    matched_monkeys(trades(), {"X": data()}, FREE, MonkeyConfig(runs=2), workers=1)


def test_monkey_worker_exception_propagates(monkeypatch):
    import backtester.analytics.monkeys as module

    class Future:
        def result(self):
            raise RuntimeError("worker failed")

    class Pool:
        def __init__(self, *args, **kwargs):
            pass

        def submit(self, *args, **kwargs):
            return Future()

        def shutdown(self, **kwargs):
            pass

    monkeypatch.setattr(module, "ProcessPoolExecutor", Pool)
    with pytest.raises(RuntimeError, match="worker failed"):
        matched_monkeys(trades(), {"X": data()}, FREE, MonkeyConfig(runs=2), workers=2)
