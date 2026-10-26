"""Spec: ARCHITECTURE.md > Intrabar resolution (V2.4c T-03).

Test-case list, written before production changes:
- Long/short TP-first and SL-first minutes; both in one minute remain SL-first.
- Stop gap fills at minute open, TP gap at target; M1 exit times and callbacks.
- Two/three partial targets; TP1 then BE on k+1, never on TP1's own minute.
- Limit fill: ignore pre-fill TP/SL; filling minute SL only; later minute TP.
- Replayed limit entry time is the filling M1 close; base entry candle and callbacks stay.
- Limit penetration uses the placed level and fixed spread; gap entry pricing stays.
- Missing/partial/duplicate/unordered M1 -> atomic fallback; no future replay.
- TP penetration and short ask triggering determine ambiguity and every M1 fill.
- sl_first ignores source and matches legacy; M1-base and unambiguous bars need none.
- Per-trade diagnostics, combined summary, CSV, settings/panel/grid round trips.
- Adapter day cache is bounded, reuses reads, clips output, handles missing cache.
- Golden checker accepts only neutral added resolution metadata on old references.
- Measurement covers seven golden setups and two modes, unchanged costs and deltas.
"""

import json
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest
from conftest import DEFAULT_START, build_candles, build_series

from backtester.analytics.metrics import summarize
from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason
from backtester.runner import trade_rows
from backtester.settings import form_values, leaves, settings_from_values
from backtester.strategy.base import Order, Strategy
from backtester.tools.golden import compare_trades, serialize_trade

ENTRY = (100, 100, 100, 100)
START = DEFAULT_START + Timeframe.M5.duration
TP_FIRST = [(100, 112, 99, 111), (111, 111, 89, 95)] + [(95, 95, 95, 95)] * 3
SL_FIRST = [(100, 101, 89, 95), (95, 112, 95, 111)] + [(111, 111, 111, 111)] * 3


def mirror(rows, sign):
    return rows if sign > 0 else [(200 - o, 200 - lo, 200 - h, 200 - c) for o, h, lo, c in rows]


class Scripted(Strategy):
    timeframes = (Timeframe.M5,)
    base_timeframe = Timeframe.M5
    uses_session_break_even = False

    def __init__(self, order, limit=False):
        self.order = order
        self.limit = limit
        self.closed = []
        self.closed_at = []
        self.now = None

    def on_candle(self, now, views):
        self.now = now
        i = views[self.base_timeframe].cursor
        return [self.order] if i == int(self.limit) else []

    def pending_limit_orders(self):
        return [self.order] if self.limit else []

    def on_trade_closed(self, ref, result):
        self.closed.append(result)
        self.closed_at.append(self.now)


def execute(
    minutes=TP_FIRST,
    *,
    sign=1,
    mode="m1",
    source=None,
    base=None,
    limit=False,
    tf=Timeframe.M5,
    cost=None,
    **kwargs,
):
    cfg = cost or CostConfig(symbols={"TEST": SymbolCosts(0, 0, 1)}, tp_penetration=0)
    order = Order(
        Direction.BULLISH if sign > 0 else Direction.BEARISH,
        100,
        100 - sign * 10,
        100 + sign * 10,
        limit_fill=limit,
        **kwargs,
    )
    strategy = Scripted(order, limit)
    strategy.base_timeframe = tf
    strategy.timeframes = (tf,)
    raw = build_candles(mirror(minutes, sign), Timeframe.M1, DEFAULT_START + tf.duration)
    calls = []

    def get(symbol, start, end):
        calls.append((symbol, start, end))
        # Existing trades resolve before on_candle; limit fills resolve after it.
        assert strategy.now == DEFAULT_START + tf.duration * (2 if limit else 1)
        return raw if source is None else source(symbol, start, end)

    if base is None:
        base = (
            minutes[0][0],
            max(c[1] for c in minutes),
            min(c[2] for c in minutes),
            minutes[-1][3],
        )
    trades = run_backtest(
        strategy,
        [build_series(mirror([ENTRY, base], sign), tf)],
        EngineConfig(costs=cfg, intrabar=mode),
        intrabar_source=get,
    )
    return trades[0], calls, strategy


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize(
    "minutes,reason,tag,offset",
    [
        (TP_FIRST, ExitReason.TAKE_PROFIT, "tp_first", 1),
        (SL_FIRST, ExitReason.STOP_LOSS, "sl_first", 1),
        ([(100, 112, 89, 100)] + [ENTRY] * 4, ExitReason.STOP_LOSS, "sl_first", 1),
    ],
)
def test_first_event_and_m1_times(sign, minutes, reason, tag, offset):
    t, calls, strategy = execute(minutes, sign=sign)
    assert t.exit_reason is reason and t.intrabar == tag
    assert t.exit_time == START + timedelta(minutes=offset)
    assert t.exit_candle == START
    assert calls == [("TEST", START, START + Timeframe.M5.duration)]
    assert strategy.closed == [t]
    assert t.intrabar_ambiguous == 1
    assert t.intrabar_tp_first == int(tag == "tp_first")
    assert t.intrabar_sl_first == int(tag == "sl_first")
    if tag == "tp_first":
        assert t.mae_r == pytest.approx(-0.1)  # no later SL minute's excursion


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize(
    "gap,price,reason",
    [
        ((85, 112, 84, 100), 85, ExitReason.STOP_LOSS),
        ((115, 116, 114, 115), 110, ExitReason.TAKE_PROFIT),
    ],
)
def test_m1_gaps_keep_fill_prices(sign, gap, price, reason):
    minutes = [gap, (100, 112, 89, 100)] + [ENTRY] * 3
    t, _, _ = execute(minutes, sign=sign)
    assert t.exit_reason is reason
    assert t.exit_price == 100 + sign * (price - 100)


@pytest.mark.parametrize("sign", [1, -1])
def test_two_tps_and_be_from_next_minute(sign):
    # TP1 minute closes below BE, but BE may only hit from the following minute.
    minutes = [(100, 111, 99, 99), (99, 121, 98, 119)] + [(119, 119, 119, 119)] * 3
    t, _, _ = execute(
        minutes, sign=sign, take_profit_2=100 + sign * 20, tp1_share=0.5, break_even_after_tp1=True
    )
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT, ExitReason.BREAK_EVEN]
    assert [p.time for p in t.parts] == [START + timedelta(minutes=i) for i in (1, 2)]
    assert t.break_even_time == START + timedelta(minutes=1)
    assert t.parts[1].price == 100 - sign  # gap through the new BE stop
    assert t.intrabar == "tp_first"


@pytest.mark.parametrize("sign", [1, -1])
def test_be_does_not_exit_on_tp1_minute_close(sign):
    minutes = [(100, 111, 99, 99)] + [(105, 121, 104, 120)] * 4
    t, _, _ = execute(
        minutes, sign=sign, take_profit_2=100 + sign * 20, tp1_share=0.5, break_even_after_tp1=True
    )
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT] * 2
    assert t.r_gross == 1.5


@pytest.mark.parametrize("sign", [1, -1])
def test_three_partial_tps_before_stop(sign):
    minutes = [
        (100, 111, 99, 110),
        (110, 121, 109, 120),
        (120, 131, 119, 130),
        (130, 130, 89, 95),
        (95, 95, 95, 95),
    ]
    t, _, _ = execute(
        minutes,
        sign=sign,
        take_profit_2=100 + sign * 20,
        take_profit_3=100 + sign * 30,
        tp1_share=0.3,
        tp2_share=0.3,
    )
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT] * 3
    assert t.r_gross == pytest.approx(2.1)


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_only_sl_on_fill_minute_then_tp(sign):
    # First minute's TP precedes entry; second fills and hits TP (ignored); third exits.
    minutes = [
        (105, 112, 104, 110),
        (110, 112, 99, 105),
        (105, 112, 104, 110),
        (110, 110, 89, 95),
        (95, 95, 95, 95),
    ]
    t, _, strategy = execute(minutes, sign=sign, limit=True)
    assert t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.exit_time == START + timedelta(minutes=3)
    assert t.entry_time == START + timedelta(minutes=2)
    assert t.entry_candle == START
    assert strategy.closed_at == [START + Timeframe.M5.duration]
    assert t.entry == 100 and t.intrabar == "tp_first"


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_sl_on_filling_minute_wins(sign):
    t, _, _ = execute([(100, 112, 89, 100)] + [ENTRY] * 4, sign=sign, limit=True)
    assert t.exit_reason is ExitReason.STOP_LOSS and t.intrabar == "sl_first"
    assert t.entry_time == t.exit_time == START + timedelta(minutes=1)
    assert t.entry_candle == START


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_penetration_defers_fill_and_excludes_filling_minute_tp(sign):
    cost = CostConfig(symbols={"TEST": SymbolCosts(2, 0, 1)}, tp_penetration=1)
    minutes = [
        (105, 115, 99, 110),  # touch, insufficient penetration: no entry
        (110, 115, 98, 105),  # fill, TP ignored
        (105, 115, 104, 110),  # first eligible TP
        (110, 110, 89, 95),
        (95, 95, 95, 95),
    ]
    t, _, _ = execute(minutes, sign=sign, limit=True, cost=cost)
    assert t.entry_time == START + timedelta(minutes=2)
    assert t.exit_time == START + timedelta(minutes=3)
    assert t.exit_reason is ExitReason.TAKE_PROFIT


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_replay_without_exit_still_records_entry_time(sign):
    minutes = [(105, 112, 104, 110), (110, 112, 99, 105)] + [(105, 105, 104, 105)] * 3
    t, _, _ = execute(minutes, sign=sign, limit=True)
    assert t.entry_time == START + timedelta(minutes=2)
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert t.intrabar_ambiguous == 1
    assert t.intrabar == "" and t.intrabar_tp_first == t.intrabar_sl_first == 0


@pytest.mark.parametrize("sign", [1, -1])
def test_gapped_limit_keeps_base_fill_price_and_placed_penetration(sign):
    placed = Order(
        Direction.BULLISH if sign > 0 else Direction.BEARISH,
        100,
        100 - sign * 20,
        100 - sign * 2,
        limit_fill=True,
    )

    class GapLimit(Scripted):
        def on_candle(self, now, views):
            return [replace(self.order, entry=100 - sign * 5)] if views[Timeframe.M5].cursor else []

    minutes = [(95, 96, 95, 96), (96, 99, 95, 98)] + [(98, 98, 98, 98)] * 3
    strategy = GapLimit(placed, limit=True)
    [t] = run_backtest(
        strategy,
        [build_series(mirror([ENTRY, (95, 99, 95, 98)], sign))],
        EngineConfig(
            costs=CostConfig(
                symbols={"TEST": SymbolCosts(1, 0, 1)}, tp_penetration=1, short_tp_on_ask=False
            ),
            intrabar="m1",
        ),
        intrabar_source=lambda *_: build_candles(mirror(minutes, sign), Timeframe.M1, START),
    )
    assert t.entry == 100 - sign * 5
    assert t.entry_time == START + timedelta(minutes=1)
    assert t.exit_time == START + timedelta(minutes=2)
    assert t.exit_reason is ExitReason.TAKE_PROFIT


def test_missing_limit_minutes_preserve_base_entry_time():
    t, _, _ = execute(limit=True, source=lambda *_: [])
    assert t.entry_time == t.exit_time == START + Timeframe.M5.duration
    assert t.intrabar == "fallback" and t.exit_reason is ExitReason.STOP_LOSS


@pytest.mark.parametrize("bad", ["empty", "partial", "duplicate", "reversed", "future"])
def test_missing_or_invalid_coverage_falls_back_atomically(bad):
    raw = build_candles(TP_FIRST, Timeframe.M1, START)
    data = {
        "empty": [],
        "partial": raw[:-1],
        "duplicate": [raw[0], *raw[:-1]],
        "reversed": raw[::-1],
        "future": [replace(c, ts=c.ts + timedelta(days=1)) for c in raw],
    }
    t, _, _ = execute(source=lambda *_: data[bad])
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert t.exit_time == START + Timeframe.M5.duration
    assert t.intrabar == "fallback" and t.intrabar_fallbacks == 1
    assert t.intrabar_tp_first == t.intrabar_sl_first == 0
    assert len(t.parts) == 1


def test_future_candles_cannot_change_resolved_trade():
    raw = build_candles(TP_FIRST, Timeframe.M1, START)
    t, _, _ = execute(source=lambda *_: raw)
    future = build_candles([(100, 1000, 1, 100)], Timeframe.M1, START + timedelta(days=1))
    t2, _, _ = execute(source=lambda *_: raw + future)
    assert t2 == t


@pytest.mark.parametrize("sign", [1, -1])
def test_thresholds_control_ambiguity_and_m1_fill(sign):
    cost = CostConfig(
        symbols={"TEST": SymbolCosts(2, 0, 1)}, tp_penetration=1, short_tp_on_ask=True
    )
    # Long threshold 112, short mirror threshold 114 (spread + penetration).
    t, calls, _ = execute([(100, 111, 89, 100)] + [ENTRY] * 4, sign=sign, cost=cost)
    assert not calls and t.intrabar_ambiguous == 0
    threshold = 112 if sign > 0 else 114
    minutes = [(100, threshold - 0.1, 99, 105), (105, threshold, 104, 110), (110, 110, 89, 100)] + [
        ENTRY
    ] * 2
    t, calls, _ = execute(minutes, sign=sign, cost=cost)
    assert calls and t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.exit_time == START + timedelta(minutes=2)
    assert t.exit_fill == 100 + sign * 10


def test_default_never_calls_source_and_keeps_legacy():
    t, calls, _ = execute(mode="sl_first")
    assert not calls and t.intrabar == ""
    assert t.exit_reason is ExitReason.STOP_LOSS and t.r_gross == -1
    assert t.exit_time == START + Timeframe.M5.duration
    assert t.intrabar_ambiguous == 1
    t, calls, _ = execute(mode="sl_first", limit=True, minutes=TP_FIRST, base=(100, 112, 99, 110))
    assert not calls and t.exit_reason is ExitReason.END_OF_DATA


def test_one_minute_base_and_unambiguous_need_no_source():
    t, calls, _ = execute([(100, 112, 89, 100)], tf=Timeframe.M1)
    assert not calls and t.intrabar == "" and t.intrabar_ambiguous == 0
    t, calls, _ = execute([(100, 112, 99, 110)] * 5)
    assert not calls and t.exit_reason is ExitReason.TAKE_PROFIT


def test_no_source_falls_back():
    strategy = Scripted(Order(Direction.BULLISH, 100, 90, 110))
    [t] = run_backtest(
        strategy,
        [build_series([ENTRY, (100, 112, 89, 95)])],
        EngineConfig(costs=CostConfig(symbols={"TEST": SymbolCosts(0, 0, 1)}), intrabar="m1"),
    )
    assert t.intrabar == "fallback" and t.intrabar_fallbacks == 1
    assert t.exit_reason is ExitReason.STOP_LOSS


@pytest.mark.parametrize("tf", [Timeframe.M15, Timeframe.H1])
def test_larger_base_intervals_are_bounded(tf):
    minutes = TP_FIRST + [(95, 95, 95, 95)] * (tf.value - 5)
    t, calls, _ = execute(minutes, tf=tf)
    assert calls == [("TEST", DEFAULT_START + tf.duration, DEFAULT_START + 2 * tf.duration)]
    assert t.exit_time == DEFAULT_START + tf.duration + timedelta(minutes=1)


def test_future_base_candles_do_not_change_closed_trade():
    order = Order(Direction.BULLISH, 100, 90, 110)
    config = EngineConfig(costs=CostConfig(symbols={"TEST": SymbolCosts(0, 0, 1)}), intrabar="m1")
    source = lambda *_: build_candles(TP_FIRST, Timeframe.M1, START)
    rows = [ENTRY, (100, 112, 89, 95)]
    first = run_backtest(Scripted(order), [build_series(rows)], config, intrabar_source=source)
    later = run_backtest(
        Scripted(order), [build_series(rows + [(95, 1000, 1, 100)])], config, intrabar_source=source
    )
    assert first == later


def test_diagnostics_csv_summary_and_golden():
    from backtester.analytics.records import TradeRecord

    t, _, _ = execute()
    summary = summarize([t])
    assert summary["intrabar_ambiguous"] == summary["intrabar_tp_first"] == 1
    assert summary["intrabar_sl_first"] == summary["intrabar_fallbacks"] == 0
    row = trade_rows(SimpleNamespace(trades=[t], runs={"TEST": SimpleNamespace(sessions=[])}))[0]
    assert row["intrabar"] == "tp_first"
    restored = TradeRecord.from_row(row)
    assert restored.intrabar == "tp_first"
    assert summarize([restored]) == summary
    default, _, _ = execute(mode="sl_first")
    new = json.loads(serialize_trade(default))
    old = {k: v for k, v in new.items() if not k.startswith("intrabar")}
    assert compare_trades([old], [new]) is None
    assert compare_trades([old], [{**new, "intrabar": "tp_first"}]) is not None


def test_setting_roundtrips_and_panel(tmp_path):
    from backtester.tools.research_grid import expand, load_grid, variant_settings
    from backtester.ui.settings_panel import group_of, label_of

    assert EngineConfig().intrabar == "m1"  # default set by the user 2026-10-24
    with pytest.raises(ValueError, match="intrabar"):
        EngineConfig(intrabar="unknown")
    found = {leaf.path: leaf for leaf in leaves()}
    assert found["engine.intrabar"].default == "m1"
    values = form_values()
    values["engine.intrabar"] = "sl_first"
    assert settings_from_values(values).engine.intrabar == "sl_first"
    assert group_of("engine.intrabar") == "Backtest"
    assert "intrabar" in label_of("engine.intrabar").lower()
    path = tmp_path / "grid.toml"
    path.write_text(
        'strategy = "no_wick"\nsymbols = ["TEST"]\n'
        '[grid]\n"engine.intrabar" = ["sl_first", "m1"]\n',
        encoding="utf-8",
    )
    spec = load_grid(path)
    variants, _, _ = expand(spec)
    assert {variant_settings(spec, v).engine.intrabar for v in variants} == {"sl_first", "m1"}


def test_adapter_source_caches_one_day_and_clips():
    from backtester.runner import IntrabarSource

    calls = []

    class Adapter:
        def fetch(self, symbol, tf, start, end):
            calls.append((symbol, tf, start, end))
            return build_candles([ENTRY] * 1440, Timeframe.M1, start)

    source = IntrabarSource(Adapter())
    assert len(source("TEST", START, START + timedelta(minutes=5))) == 5
    assert len(source("TEST", START + timedelta(minutes=5), START + timedelta(minutes=10))) == 5
    assert len(calls) == 1 and calls[0][1] is Timeframe.M1
    tomorrow = START + timedelta(days=1)
    assert len(source("TEST", tomorrow, tomorrow + timedelta(minutes=5))) == 5
    source("TEST", START, START + timedelta(minutes=5))
    assert len(calls) == 3  # only one day retained


def test_missing_adapter_day_returns_no_minutes():
    from backtester.data.adapters.cache_adapter import MissingCacheError
    from backtester.runner import IntrabarSource

    class Adapter:
        def fetch(self, *args):
            raise MissingCacheError("missing day")

    assert IntrabarSource(Adapter())("TEST", START, START + timedelta(minutes=5)) == []


def test_runner_job_supplies_symbol_adapter_and_counts(monkeypatch):
    from backtester import runner

    minutes = build_candles(TP_FIRST, Timeframe.M1, START)
    reads = []

    class Adapter:
        def fetch(self, symbol, tf, start, end):
            reads.append((symbol, tf))
            return minutes

    sources = SimpleNamespace(adapter=lambda symbol: Adapter())
    monkeypatch.setattr(
        runner, "make_strategy", lambda *args: Scripted(Order(Direction.BULLISH, 100, 90, 110))
    )
    settings = runner.RunSettings(
        engine=EngineConfig(intrabar="m1", costs=CostConfig(symbols={"TEST": SymbolCosts(0, 0, 1)}))
    )
    job = runner._Job(
        "TEST",
        START.date(),
        START.date(),
        START.date(),
        (build_series([ENTRY, (100, 112, 89, 95)]),),
        settings,
        (),
        sources,
    )
    result = runner._run_job(job)
    assert result.trades[0].intrabar == "tp_first"
    assert reads == [("TEST", Timeframe.M1)]


def test_strategy_one_overlay_passes_source(monkeypatch):
    from backtester.runner import RunSettings
    from backtester.ui import trades_overlay

    class Adapter:
        def fetch_frame(self, symbol, tf, start, end):
            return None

        def fetch(self, symbol, tf, start, end):
            return build_candles(TP_FIRST, Timeframe.M1, START)

    monkeypatch.setattr(trades_overlay, "candles_from_frame", lambda frame: build_candles([ENTRY]))
    captured = []

    def run(strategy, series, engine, *, intrabar_source):
        captured.extend(intrabar_source("TEST", START, START + timedelta(minutes=5)))
        return []

    monkeypatch.setattr(trades_overlay, "run_backtest", run)
    sources = SimpleNamespace(adapter=lambda symbol: Adapter())
    trades_overlay.run_strategy(
        sources,
        "XAUUSD",
        START.date(),
        START.date(),
        RunSettings(engine=EngineConfig(intrabar="m1")),
    )
    assert len(captured) == 5
