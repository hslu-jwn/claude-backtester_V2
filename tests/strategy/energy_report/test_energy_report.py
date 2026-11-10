"""Hand-built M1 fixtures; finished NY D1 ranges are 10, hence ATR = 10."""
import tomllib
from datetime import UTC, date, datetime, time, timedelta
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.base import UnsupportedSymbolError
from backtester.strategy.energy_report.calendar import ReportCalendar
from backtester.strategy.energy_report.config import EnergyReportConfig
from backtester.strategy.energy_report.strategy import EnergyReport

NY = ZoneInfo("America/New_York")
M1 = Timeframe.M1
DAY = date(2019, 3, 13)  # Wednesday after US DST, before EU DST
# Test exact strategy arithmetic independently of the engine's instrument tick rounding.
FREE = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False,
                                   round_to_tick=False))


def at(day, clock):
    return datetime.combine(day, time.fromisoformat(clock), NY).astimezone(UTC)


def bar(day, clock, price=105., high=None, low=None):
    return Candle(at(day, clock) - M1.duration, price,
                  price if high is None else high, price if low is None else low, price)


def warm(day=DAY, count=14):
    days = []
    d = day - timedelta(days=1)
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return [c for d in reversed(days) for c in
            (bar(d, "10:00", high=110., low=100.), bar(d, "17:00"))]


def event(day=DAY, move=1.5):
    return [bar(day, "10:29"), bar(day, "10:44", 105. + move),
            bar(day, "10:45", 105. + move), bar(day, "12:59", 106.),
            bar(day, "13:00", 106.), bar(day, "14:29", 107.),
            bar(day, "14:30", 107.)]


def run(candles=None, symbol="USOIL", **cfg):
    return run_backtest(EnergyReport(symbol, EnergyReportConfig(**cfg)),
                        [CandleSeries(symbol, M1, warm() + event() if candles is None
                                      else candles)], FREE)


@pytest.mark.parametrize("day,report,control", [
    ("2019-03-13", True, False), ("2019-03-12", False, True),
    ("2019-03-14", False, True), ("2019-03-15", False, False),
    ("2019-01-23", False, False),  # MLK Monday
    ("2019-02-20", False, False),  # Presidents Monday
    ("2019-05-29", False, False), ("2019-09-04", False, False),
    ("2019-10-16", False, False),  # Columbus: federal, NYSE open
    ("2019-11-13", False, False),  # Veterans: federal, NYSE open
    ("2017-07-05", False, False), ("2018-07-04", False, False),
    ("2021-07-07", False, False),  # observed July 4 Monday
    ("2018-12-05", False, False),  # NYSE Bush funeral
    ("2019-04-17", True, False),  # Good Friday is outside Mon-Wed
    ("2019-11-27", True, False),  # Thanksgiving Thursday outside Mon-Wed
    ("2018-07-03", False, True),  # early close is not a full closure
    ("2018-12-25", False, False), ("2019-11-28", False, False),
    ("2019-01-22", False, True),  # control skips its own full closure only
    ("2022-06-22", False, False), ("2020-06-24", True, False),
])
def test_calendar(day, report, control):
    cal = ReportCalendar()
    d = date.fromisoformat(day)
    assert cal.qualifies(d, "report") is report
    assert cal.qualifies(d, "control") is control


@pytest.mark.parametrize("family,move,side,exit_clock", [
    ("F", 1.5, Direction.BULLISH, "14:30"),
    ("F", -1.5, Direction.BEARISH, "14:30"),
    ("V", 1.5, Direction.BEARISH, "13:00"),
    ("V", -1.5, Direction.BULLISH, "13:00"),
])
def test_direction_stop_and_exact_exit(family, move, side, exit_clock):
    [trade] = run(warm() + event(move=move), family=family)
    assert trade.direction is side
    assert trade.entry_time == at(DAY, "10:45")
    assert trade.entry == 105. + move
    sign = 1 if side is Direction.BULLISH else -1
    assert trade.initial_stop == trade.entry - sign * 10.
    assert trade.take_profit is None
    assert trade.exit_time == at(DAY, exit_clock)
    assert trade.exit_reason is ExitReason.SIGNAL
    assert trade.swap_r == 0


@pytest.mark.parametrize("move,k,expected", [(1.499, .15, 0), (1.5, .15, 1),
    (-1.5, .15, 1), (2.99, .30, 0), (3., .30, 1), (0., .15, 0)])
def test_inclusive_price_threshold(move, k, expected):
    assert len(run(warm() + event(move=move), k=k)) == expected


def test_stop_engine_hit_and_half_atr_distance():
    candles = warm() + event()[:3] + [
        Candle(at(DAY, "10:46") - M1.duration, 106.5, 107., 99., 100.)]
    [trade] = run(candles, stop_atr=.5)
    assert trade.initial_stop == 101.5
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.r_gross == -1.


def test_gap_through_stop_uses_engine_open_price():
    candles = warm() + event()[:3] + [bar(DAY, "10:46", 100., high=107., low=99.)]
    [trade] = run(candles, stop_atr=.5)
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.exit_price == 100.
    assert trade.r_gross == -1.3


@pytest.mark.parametrize("missing", ["10:29", "10:45"])
def test_missing_endpoint_means_no_entry(missing):
    assert run(warm() + [c for c in event() if c.ts + M1.duration != at(DAY, missing)]) == []


def test_baseline_cannot_leak_from_previous_date():
    assert run(warm() + [bar(DAY - timedelta(days=1), "17:01")]
               + event()[1:]) == []


def test_control_tuesday_and_thursday_and_no_report_overlap():
    for day in (date(2019, 3, 12), date(2019, 3, 14)):
        candles = warm(day) + event(day)
        assert len(run(candles, days="control")) == 1
        assert run(candles) == []
    assert run(days="control") == []


@pytest.mark.parametrize("day", [date(2019, 1, 9), DAY, date(2019, 7, 10)])
def test_ny_dst_clock(day):
    [trade] = run(warm(day) + event(day))
    assert trade.entry_time == at(day, "10:45")
    assert trade.exit_time == at(day, "14:30")


def test_atr_requires_fourteen_finished_regular_days():
    assert run(warm(count=13) + event()) == []
    # A huge current-day range is unfinished and cannot change today's ATR stop.
    [trade] = run(warm() + [bar(DAY, "09:00", high=1000., low=1.)] + event())
    assert trade.initial_stop == 96.5


def test_weekend_stubs_and_missing_daily_close_do_not_seed_atr():
    candles = warm(count=13)
    saturday = date(2019, 3, 9)
    candles += [bar(saturday, "12:00", high=500., low=1.), bar(saturday, "17:00")]
    candles.sort(key=lambda c: c.ts)
    assert run(candles + event()) == []
    candles = warm()
    candles = [c for c in candles if c.ts + M1.duration != at(date(2019, 3, 12), "17:00")]
    assert run(candles + event()) == []


def test_daily_session_includes_previous_evening_and_wilder_update():
    # Thirteenth day range 10; fourteenth ranges 20 including prior 18:00.
    candles = warm()
    candles += [bar(date(2019, 3, 11), "18:00", high=120., low=100.)]
    candles.sort(key=lambda c: c.ts)
    [trade] = run(candles + event(move=3.))
    assert trade.entry - trade.initial_stop == pytest.approx(150. / 14)
    # Fifteen regular days: last TR=20 updates the seeded ATR=10 with Wilder smoothing.
    candles = warm(count=15)
    candles += [bar(date(2019, 3, 11), "18:00", high=120., low=100.)]
    candles.sort(key=lambda c: c.ts)
    [trade] = run(candles + event(move=3.))
    assert trade.entry - trade.initial_stop == pytest.approx((10. * 13 + 20.) / 14)


def replay(candles):
    strategy = EnergyReport("USOIL")
    series = CandleSeries("USOIL", M1, candles)
    out = []
    for i, c in enumerate(candles):
        now = c.ts + M1.duration
        out.extend((now, order) for order in strategy.on_candle(now, {M1: series.view(i)}))
    return out


def test_no_early_signal_and_appending_future_never_changes_orders():
    prefix = warm() + event()[:2]
    assert replay(prefix) == []
    prefix += event()[2:3]
    earlier = replay(prefix)
    assert len(earlier) == 1 and earlier[0][0] == at(DAY, "10:45")
    future = event()[3:] + [bar(DAY + timedelta(days=1), "17:00", 9999.)]
    assert replay(prefix + future)[:len(earlier)] == earlier


def test_skipped_or_stopped_order_has_no_pending_time_exit():
    candles = warm() + event()[:3]
    strategy = EnergyReport("USOIL")
    series = CandleSeries("USOIL", M1, candles + event()[3:])
    orders = []
    for i, c in enumerate(candles):
        orders += strategy.on_candle(c.ts + M1.duration, {M1: series.view(i)})
    [order] = orders
    strategy.on_order_skipped(order.ref, at(DAY, "10:45"))
    for i in range(len(candles), len(series)):
        strategy.on_candle(series.view(i).current.ts + M1.duration, {M1: series.view(i)})
        assert strategy.exits() == []


def test_missing_exit_uses_existing_timed_exit_fallback_and_is_flagged():
    strategy = EnergyReport("USOIL")
    candles = warm() + event()[:-1] + [bar(DAY, "14:31", 107.)]
    series = CandleSeries("USOIL", M1, candles)
    [trade] = run_backtest(strategy, [series], FREE)
    assert trade.exit_time == at(DAY, "14:31")
    [record] = strategy.session_records()
    assert "missing_exit" in record["defects"]


@pytest.mark.parametrize("last_clock,defects", [
    ("12:00", {"missing_exit"}),
    ("17:01", {"missing_exit", "unexpected_rollover"}),
])
def test_truncation_and_unexpected_rollover_fail_integrity(last_clock, defects):
    strategy = EnergyReport("USOIL")
    candles = warm() + event()[:3] + [bar(DAY, last_clock, 107.)]
    run_backtest(strategy, [CandleSeries("USOIL", M1, candles)], FREE)
    [record] = strategy.session_records()
    assert set(record["defects"]) == defects
    assert record["integrity_failed"] is True


def test_stop_cancels_pending_time_exit():
    strategy = EnergyReport("USOIL")
    candles = warm() + event()[:3] + [bar(DAY, "10:46", 90.), bar(DAY, "14:30", 107.)]
    [trade] = run_backtest(strategy, [CandleSeries("USOIL", M1, candles)], FREE)
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert strategy.exits() == []
    assert strategy.session_records()[0]["defects"] == []


def test_zero_atr_and_nonfinite_candles_cannot_trade():
    candles = [Candle(c.ts, 105., 105., 105., 105.) for c in warm()]
    assert run(candles + event()) == []
    with pytest.raises(ValueError, match="finite"):
        bar(DAY, "10:45", float("nan"))


@pytest.mark.parametrize("cfg", [{"family": "bad"}, {"days": "all"}, {"k": 0.},
    {"k": float("nan")}, {"stop_atr": float("inf")}, {"stop_atr": -1.},
    {"atr_period": 0}, {"atr_period": 1.5}, {"atr_period": True}])
def test_invalid_config(cfg):
    with pytest.raises(ValueError):
        EnergyReportConfig(**cfg)


def test_supported_symbols_and_frozen_defaults():
    assert len(run(symbol="UKOIL")) == 1
    with pytest.raises(UnsupportedSymbolError):
        EnergyReport("EURUSD")
    with pytest.raises(AttributeError):
        EnergyReportConfig().k = .3


def test_preregistered_grid_all_cells_and_diagnostics_off():
    root = Path(__file__).resolve().parents[3]
    grid = tomllib.loads((root / "research/grids/energy_report.toml").read_text())
    assert grid["symbols"] == ["USOIL", "UKOIL"]
    assert grid["strategy"] == "energy_report"
    assert all(grid[k] is False for k in ("monkeys", "sensitivity", "entry_screen"))
    cells = grid["grid"]
    assert set(product(cells["family"], cells["k"], cells["stop_atr"], cells["days"])) == set(
        product(("F", "V"), (.15, .30), (.5, 1.), ("report", "control")))

@pytest.mark.parametrize("clock", ["10:29", "10:45"])
def test_invalid_signal_candle_records_defect_and_never_trades(clock):
    candles = warm() + [bar(DAY, clock, 0.) if c.ts + M1.duration == at(DAY, clock) else c
                        for c in event()]
    strategy = EnergyReport("USOIL")
    assert run_backtest(strategy, [CandleSeries("USOIL", M1, candles)], FREE) == []
    assert any("invalid_signal_candle" in r["defects"] for r in strategy.session_records())
