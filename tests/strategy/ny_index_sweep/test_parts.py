"""Pieces of strategy 2: candle alignment, ranking, SL and TP rules.
Spec: strategy-ny-indices.md › General, › Stop Loss, › Take Profit.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from backtester.core.models import Direction, Timeframe
from backtester.detectors.equilibrium import equilibrium_box
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.strategy.ny_index_sweep.config import AthMode, NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import Zone, candle_open
from backtester.strategy.ny_index_sweep.setup import Route, Setup, Signal, best
from backtester.strategy.ny_index_sweep.strategy import _inside
from backtester.strategy.ny_index_sweep.targets import (
    FIB,
    FIXED,
    SWING,
    Level,
    cluster,
    fallback_levels,
    stop_loss,
)
from backtester.strategy.ny_index_sweep.windows import Window, window_on

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M1, M5, M15, H1, H4 = Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4
T = datetime(2026, 9, 2, 14, 0, tzinfo=UTC)


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_candle_open_is_utc_aligned_except_new_york_4h():
    assert candle_open(M5, utc("2026-09-02 13:07")) == utc("2026-09-02 13:05")
    assert candle_open(M15, utc("2026-09-02 13:59")) == utc("2026-09-02 13:45")
    assert candle_open(H1, utc("2026-09-02 13:59")) == utc("2026-09-02 13:00")
    # 4h New York: EDT, 10:00-14:00 ET = 14:00-18:00 UTC; EST one hour later
    assert candle_open(H4, utc("2026-09-02 13:59")) == utc("2026-09-02 10:00")
    assert candle_open(H4, utc("2026-09-02 14:00")) == utc("2026-09-02 14:00")
    assert candle_open(H4, utc("2026-01-14 14:59")) == utc("2026-01-14 11:00")
    assert candle_open(H4, utc("2026-09-02 23:30")) == utc("2026-09-02 22:00")  # 18:00 ET


def test_the_5m_sweeping_candle_inside_the_15m_one():
    assert _inside(utc("2026-09-02 13:52"), M5, utc("2026-09-02 13:48"), M15)
    assert not _inside(utc("2026-09-02 14:01"), M5, utc("2026-09-02 13:48"), M15)


def zone(kind, top, bottom, direction=LONG, tf=M5) -> Zone:
    return Zone(ZoneBox(kind, direction, top, bottom, 0, 1, T), tf, T)


def test_ranking_ob_breaker_bpr_fvg_eq_then_the_one_price_reaches_first():
    zones = [
        zone(ZoneKind.FVG, 105, 104),
        zone(ZoneKind.EQUILIBRIUM, 106, 100),
        zone(ZoneKind.BREAKER, 103, 102),
        zone(ZoneKind.ORDER_BLOCK, 101, 100),
    ]
    assert best(zones, LONG).box.kind is ZoneKind.ORDER_BLOCK
    two_fvgs = [zone(ZoneKind.FVG, 103, 102), zone(ZoneKind.FVG, 105, 104)]
    assert best(two_fvgs, LONG).box.top == 105  # a long comes from above
    shorts = [zone(ZoneKind.FVG, 103, 102, SHORT), zone(ZoneKind.FVG, 105, 104, SHORT)]
    assert best(shorts, SHORT).box.bottom == 102


def signal(z3: Zone, close=110.0, deepest=103.0, extreme=99.0, bos_high=108.0, kind=Window.PM):
    window = window_on(date(2026, 9, 2), kind)
    route = Route((M5,), M5, M1, M5, 10)
    setup = Setup(window, LONG, route, (), M5, extreme, T)
    setup.bos_high = bos_high
    return Signal(setup, LONG, T, close, z3, None, deepest)


def test_sl_below_the_3rd_confluence_with_10_percent_of_its_height():
    z3 = zone(ZoneKind.FVG, 105.0, 103.0)
    assert stop_loss(signal(z3), {}, NyIndexSweepConfig()) == (
        pytest.approx(102.8),
        "3rd confluence",
    )
    no_buffer = NyIndexSweepConfig(sl_buffer=0.0)
    assert stop_loss(signal(z3), {}, no_buffer)[0] == 103.0


def test_sl_with_an_eq_as_3rd_confluence_uses_the_eq_rule():
    # spec example: swing low 100, BoS high 200, EQ 150, deepest wick 140 -> SL 96
    box = equilibrium_box(LONG, 0, 100.0, 1, 200.0, T)
    z3 = Zone(box, M5, T)
    sl, source = stop_loss(signal(z3, close=160.0, deepest=140.0), {}, NyIndexSweepConfig())
    assert (sl, source) == (pytest.approx(96.0), "equilibrium")


def test_narrow_3rd_confluence_moves_the_sl_below_the_sweep_extreme():
    class Atr:
        def atr(self):
            return 10.0

    z3 = zone(ZoneKind.FVG, 105.0, 103.0)  # 2 high, ATR 10
    cfg = NyIndexSweepConfig(narrow_confluence_atr_mult=0.5)
    sl, source = stop_loss(signal(z3, extreme=99.0), {M5: Atr()}, cfg)
    assert (sl, source) == (pytest.approx(98.8), "sweep extreme")
    wide = NyIndexSweepConfig(narrow_confluence_atr_mult=0.1)  # threshold 1 < 2
    assert stop_loss(signal(z3), {M5: Atr()}, wide)[1] == "3rd confluence"


def test_clusters_take_the_higher_timeframe_level_then_the_nearest():
    entry, risk = 100.0, 10.0

    def r(p):
        return (p - entry) / risk

    levels = [
        Level(112.0, M15, SWING),  # 1.2R
        Level(113.0, H4, SWING),  # 1.3R, within 0.2R: same cluster, 4h wins
        Level(114.5, H1, SWING),  # 1.45R: chained (0.15R from 113)
        Level(120.0, H1, SWING),  # 2.0R: own cluster
        Level(121.0, H1, SWING),  # 2.1R: same cluster, same TF -> the nearest (120)
    ]
    assert [lv.price for lv in cluster(levels, r, 0.2, 1)] == [113.0, 120.0]


def test_fallback_levels_fib_extension_of_the_bos_leg_or_fixed_r():
    s = signal(zone(ZoneKind.FVG, 105, 103), extreme=100.0, bos_high=110.0)
    fib = fallback_levels(s, 108.0, 2.0, NyIndexSweepConfig())
    assert fib == [
        (pytest.approx(113.82), FIB),
        (115.0, FIB),
        (pytest.approx(116.18), FIB),
        (120.0, FIB),
    ]
    fixed = fallback_levels(s, 108.0, 2.0, NyIndexSweepConfig(ath_mode=AthMode.FIXED_R))
    assert fixed == [(pytest.approx(110.4), FIXED), (111.0, FIXED), (111.6, FIXED)]
