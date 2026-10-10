"""Each branch of the strategy-2 setup state machine (setup.py), on a PM 5m / 1m long.
Spec: strategy-ny-indices.md › PM Session, › Rules (user's answers 2026-10-11).

Real 1m candles (and the 5m candles built from them) drive taps, validation and moves;
the BoS events and zones of each timeframe are injected at chosen times, so every branch
is tested on its own. The day: PM window 2026-09-02 (17:30-20:00 UTC); t0 = 17:40.
  minute 0   low 98.0: the sweep extreme (swing low 99.0 taken)
  t0+5       5m bullish BoS (5m candle 0, high 100.4)
  FVG A      5m, 98.8-99.2, formed in the move (candle 0, exists from t0+5)
  minute 7   low 99.1: taps A (closes t0+8)
  t0+10      1m bullish BoS (minute 9), entry FVG 99.7-99.9 formed in its move
  minute 10  low 99.8, green close 100.2: confirms the entry FVG -> ENTRY at t0+11
"""

from __future__ import annotations

from bisect import bisect_right
from datetime import UTC, date, datetime, timedelta

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.bos import BreakOfStructure
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import Zone
from backtester.strategy.ny_index_sweep.setup import Context, Route, Setup, Step
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep, WindowState
from backtester.strategy.ny_index_sweep.windows import Window, window_on

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M1, M5, M15 = Timeframe.M1, Timeframe.M5, Timeframe.M15
T0 = datetime(2026, 9, 2, 17, 40, tzinfo=UTC)
WINDOW = window_on(date(2026, 9, 2), Window.PM)
ROUTE = Route((M5,), M5, M1, M5, 10)
NO_EQ = NyIndexSweepConfig(
    confluence_kinds=frozenset({ZoneKind.FVG, ZoneKind.ORDER_BLOCK, ZoneKind.BREAKER})
)
DOJI = 0.1767  # NAS100


def minute(i: int) -> datetime:
    return T0 + timedelta(minutes=i)


def candles(overrides: dict[int, tuple], n: int = 140) -> list[Candle]:
    """1m candles from t0; quiet (99.5-100.5) unless overridden by (o, h, l, c)."""
    return [Candle(minute(i), *overrides.get(i, (100.0, 100.5, 99.5, 100.1))) for i in range(n)]


def five(m1: list[Candle]) -> list[Candle]:
    out = []
    for k in range(0, len(m1) - 4, 5):
        cs = m1[k : k + 5]
        out.append(
            Candle(
                cs[0].ts, cs[0].open, max(c.high for c in cs), min(c.low for c in cs), cs[-1].close
            )
        )
    return out


class Frame:
    """Stands in for frames.Frame: real candles, injected BoS events and zones."""

    def __init__(self, tf: Timeframe, cs: list[Candle]):
        self.tf, self.series = tf, CandleSeries("NAS100", tf, cs)
        self._closes = [c.ts + tf.duration for c in cs]
        self.events: dict[datetime, list[BreakOfStructure]] = {}
        self.zones: list[Zone] = []
        self.view, self.closed, self.breaks, self.recent = None, False, [], []

    def step(self, now: datetime) -> None:
        n = bisect_right(self._closes, now)
        self.view = self.series.view(n - 1) if n else None
        self.closed = n > 0 and self._closes[n - 1] == now
        self.breaks = self.events.get(now, [])
        self.recent = [z for z in self.zones if z.box.created_at <= now]

    @property
    def current(self):
        return self.view.current if self.closed else None

    def invalidated(self, zone, until=None) -> bool:
        return False

    def index_at(self, t: datetime) -> int:
        return max(0, bisect_right([c.ts for c in self.series._candles], t) - 1)


def swing(kind, price, index, at) -> SwingPoint:
    return SwingPoint(index, at, kind, price, index, at, index)


def bos(direction, price, index, at, swing_index=0) -> BreakOfStructure:
    kind = SwingKind.HIGH if direction is LONG else SwingKind.LOW
    return BreakOfStructure(index, at, direction, swing(kind, price, swing_index, at), price + 0.1)


def zone(tf, top, bottom, start_index, created_index, created_at, start_ts, kind=ZoneKind.FVG):
    box = ZoneBox(kind, LONG, top, bottom, start_index, created_index, created_at)
    return Zone(box, tf, start_ts)


BASE = {0: (99.5, 99.6, 98.0, 99.4), 7: (100.0, 100.1, 99.1, 99.6), 10: (100.0, 100.4, 99.8, 100.2)}
FVG_A = zone(M5, 99.2, 98.8, 0, 0, minute(5), minute(0))
ENTRY_FVG = zone(M1, 99.9, 99.7, 8, 9, minute(10), minute(8))


def harness(
    overrides=BASE, setup_events=None, entry_events=None, zones=(FVG_A,), entry_zones=(ENTRY_FVG,)
):
    m1 = candles(overrides)
    frames = {M1: Frame(M1, m1), M5: Frame(M5, five(m1))}
    frames[M5].events = (
        setup_events if setup_events is not None else {minute(5): [bos(LONG, 100.3, 0, minute(5))]}
    )
    frames[M1].events = (
        entry_events
        if entry_events is not None
        else {minute(10): [bos(LONG, 100.2, 9, minute(10), 6)]}
    )
    frames[M5].zones, frames[M1].zones = list(zones), list(entry_zones)
    setup = Setup(WINDOW, LONG, ROUTE, (swing(SwingKind.LOW, 99.0, 0, T0),), M5, 98.0, minute(0))
    return m1, frames, setup


def drive(m1, frames, setup, config=NO_EQ, until=None, on_signal=None, after=None):
    """Advance the setup over the 1m candles closing after `after` (None: from the first)
    up to `until`; returns the signals."""
    signals = []
    for candle in m1:
        now = candle.ts + M1.duration
        if after is not None and now <= after:
            continue
        if until is not None and now > until:
            break
        for f in frames.values():
            f.step(now)
        s = setup.advance(Context(now, candle, frames, config, DOJI))
        if s is not None:
            signals.append(s)
            if on_signal:
                on_signal(s, now)
    return signals


def test_the_whole_funnel_enters_at_the_entry_confluence_confirmation():
    m1, frames, setup = harness()
    [s] = drive(m1, frames, setup)
    assert (s.at, s.close) == (minute(11), 100.2)
    assert s.z3 == FVG_A and s.entry_zone == ENTRY_FVG
    assert (s.bos.confirmed_at, s.tap_at, s.entry_bos.confirmed_at) == (
        minute(5),
        minute(8),
        minute(10),
    )
    assert setup.bos_high == 100.5  # the 5m BoS candle's high
    assert s.deepest == 99.1  # minute 7's wick (minute 0's 98.0 is before the BoS)
    assert setup.step is Step.IN_TRADE


def test_entry_tf_confluence_off_enters_at_the_entry_bos_close():
    m1, frames, setup = harness()
    off = NyIndexSweepConfig(confluence_kinds=NO_EQ.confluence_kinds, entry_tf_confluence=False)
    [s] = drive(m1, frames, setup, off)
    assert (s.at, s.entry_zone) == (minute(10), None)


def test_no_setup_tf_bos_within_x_sweep_tf_candles_ends_it():
    # deadline: close of the extreme's 5m candle (t0+5) + 10 x 5m = t0+55
    m1, frames, setup = harness(setup_events={})
    drive(m1, frames, setup, until=minute(54))
    assert setup.step is Step.SWEEP
    drive_rest = drive(m1, frames, setup, until=minute(55), after=minute(54))
    assert drive_rest == [] and (setup.step, setup.ended) == (Step.DONE, "no setup-TF BoS in time")


def test_a_late_bos_after_the_limit_is_ignored():
    late = {minute(60): [bos(LONG, 100.3, 11, minute(60))]}
    m1, frames, setup = harness(setup_events=late)
    assert drive(m1, frames, setup) == [] and setup.ended == "no setup-TF BoS in time"


def test_close_beyond_the_swept_level_cancels_only_with_the_setting_off():
    below = {**BASE, 4: (99.0, 99.1, 98.6, 98.9)}  # 5m candle 0 closes 98.9 < 99.0
    m1, frames, setup = harness(below, setup_events={})
    off = NyIndexSweepConfig(
        confluence_kinds=NO_EQ.confluence_kinds, sweep_close_beyond_counts=False
    )
    drive(m1, frames, setup, off, until=minute(5))
    assert setup.ended == "sweep-TF close beyond the swept level"
    m1, frames, setup = harness(below, setup_events={})
    drive(m1, frames, setup, until=minute(5))
    assert setup.step is Step.SWEEP  # default: a close beyond still counts


def test_a_deeper_wick_moves_the_extreme_and_restarts_the_count():
    deeper = {**BASE, 30: (99.0, 99.1, 97.5, 99.0)}  # minute 30: new extreme 97.5
    m1, frames, setup = harness(deeper, setup_events={})
    drive(m1, frames, setup, until=minute(60))
    assert (setup.extreme, setup.extreme_ts) == (97.5, minute(30))
    assert setup.step is Step.SWEEP  # new deadline: t0+35 + 50 min = t0+85


def test_opposite_setup_tf_bos_after_ours_cancels():
    events = {
        minute(5): [bos(LONG, 100.3, 0, minute(5))],
        minute(10): [bos(SHORT, 98.5, 1, minute(10))],
    }
    no_tap = {0: BASE[0]}
    m1, frames, setup = harness(no_tap, setup_events=events)
    assert drive(m1, frames, setup) == [] and setup.ended == "opposite setup-TF BoS"


def test_no_tap_within_25_setup_tf_candles_ends_it():
    # BoS close t0+5, timeout t0+5 + 25 x 5m = t0+130
    m1, frames, setup = harness({0: BASE[0]})
    drive(m1, frames, setup, until=minute(129))
    assert setup.step is Step.BOS
    drive(m1, frames, setup, until=minute(130), after=minute(129))
    assert setup.ended == "3rd confluence not tapped in time"


def test_a_tap_counts_only_after_the_bos_candle():
    # minute 3 dips into A (98.9) before the BoS closes at t0+5: no tap; nothing later
    early = {0: BASE[0], 3: (99.5, 99.6, 98.9, 99.4)}
    m1, frames, setup = harness(early)
    drive(m1, frames, setup, until=minute(20))
    assert setup.step is Step.BOS and setup.z3 is None


def test_no_3rd_confluence_in_the_move_ends_it():
    old = zone(M5, 99.2, 98.8, 0, 0, minute(5), minute(-5))  # starts before the extreme's candle
    after = zone(M5, 99.2, 98.8, 1, 1, minute(10), minute(5))  # formed after the BoS candle
    m1, frames, setup = harness(zones=(old, after))
    assert drive(m1, frames, setup) == [] and setup.ended == "no 3rd confluence in the BoS move"


def test_zones_created_by_the_bos_count_even_with_older_candles():
    breaker = zone(M5, 99.2, 98.8, 0, 0, minute(5), minute(-10), ZoneKind.BREAKER)
    m1, frames, setup = harness(zones=(breaker,))
    [s] = drive(m1, frames, setup)
    assert s.z3 == breaker


def test_the_3rd_confluence_closed_through_moves_to_the_next_one():
    # tap A at minute 7; the 5m candle t0+10..15 closes 98.75 < A's bottom 98.8: back to
    # waiting for a tap; B (98.3-98.7) is tapped at minute 16
    b = zone(M5, 98.7, 98.3, 0, 0, minute(5), minute(0))
    overrides = {**BASE, 10: (100.0, 100.1, 99.6, 99.9), 14: (99.0, 99.1, 98.72, 98.75),
                 16: (98.9, 99.0, 98.6, 98.9)}  # fmt: skip
    m1, frames, setup = harness(overrides, zones=(FVG_A, b), entry_events={})
    drive(m1, frames, setup, until=minute(14))
    assert setup.z3 == FVG_A
    drive(m1, frames, setup, until=minute(15), after=minute(14))
    assert (setup.step, setup.z3, setup.candidates) == (Step.BOS, None, [b])
    drive(m1, frames, setup, until=minute(17), after=minute(15))
    assert (setup.step, setup.z3) == (Step.TAPPED, b)


def test_entry_bos_must_close_at_or_after_the_tap():
    early = {minute(7): [bos(LONG, 100.2, 6, minute(7), 3)]}  # before the tap (t0+8)
    m1, frames, setup = harness(entry_events=early)
    assert drive(m1, frames, setup) == [] and setup.step is Step.TAPPED


def test_opposite_entry_tf_bos_goes_back_to_waiting_for_an_entry_bos():
    events = {
        minute(10): [bos(LONG, 100.2, 9, minute(10), 6)],
        minute(11): [bos(SHORT, 99.5, 10, minute(11), 8)],
    }
    no_confirm = {**BASE, 10: (100.0, 100.1, 99.95, 100.0)}  # no tap of the entry FVG
    m1, frames, setup = harness(no_confirm, entry_events=events)
    drive(m1, frames, setup, until=minute(11))
    assert setup.step is Step.TAPPED and setup.entry_bos is None


def test_after_the_trade_closes_a_new_entry_bos_re_enters_with_the_same_3rd_confluence():
    events = {
        minute(10): [bos(LONG, 100.2, 9, minute(10), 6)],
        minute(30): [bos(LONG, 100.2, 29, minute(30), 25)],
    }
    again = zone(M1, 99.9, 99.7, 28, 29, minute(30), minute(28))
    overrides = {**BASE, 30: (100.0, 100.4, 99.8, 100.2)}
    m1, frames, setup = harness(overrides, entry_events=events, entry_zones=(ENTRY_FVG, again))
    closed = []
    signals = drive(m1, frames, setup, on_signal=lambda s, now: closed.append(now))
    assert [s.at for s in signals] == [minute(11)]  # in the trade: no second entry
    m1, frames, setup = harness(overrides, entry_events=events, entry_zones=(ENTRY_FVG, again))

    def close_it(signal, now):
        signal.setup.trade_closed(minute(20))  # the trade ends at t0+20

    signals = drive(m1, frames, setup, on_signal=close_it)
    assert [s.at for s in signals] == [minute(11), minute(31)]
    assert signals[1].z3 == FVG_A and signals[1].entry_zone == again and setup.trades == 2


def test_pm_15m_bos_replaces_the_5m_setup_of_the_same_sweep():
    strategy = NyIndexSweep("NAS100")
    r5, r15 = Route((M5,), M5, M1, M5, 10), Route((M15,), M15, M1, M5, 10)
    s5 = Setup(WINDOW, LONG, r5, (), M5, 98.0, minute(2))
    s15 = Setup(WINDOW, LONG, r15, (), M15, 98.0, minute(2))
    other = Setup(WINDOW, LONG, r5, (), M5, 98.1, minute(2))  # another extreme price
    s15.step = Step.BOS
    ws = WindowState(WINDOW, LONG, (r5, r15), [s5, s15, other])
    strategy._replace_5m_setups(ws, s15)
    assert s5.ended == "replaced by the 15m setup of the same sweep"
    assert other.step is Step.SWEEP and s15.step is Step.BOS
