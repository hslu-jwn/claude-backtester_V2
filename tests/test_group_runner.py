"""Synthetic cache acceptance for grouped runs; no real market data."""

import csv
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest
from m1_frames import m1

from backtester import group_runner
from backtester.analytics.records import TradeRecord, read_trades
from backtester.core.market import ReferenceInput
from backtester.core.models import Direction, Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.engine.costs import CostConfig, FundingSeries, SymbolCosts
from backtester.engine.group_backtest import GroupRunResult, OpenGroupLeg, UnresolvedGroup
from backtester.engine.group_trade import LegFill, group_result
from backtester.engine.trade import ExitReason
from backtester.runner import TRADE_COLUMNS, NoDataError
from backtester.strategy.group import EntryPolicy, ExitPolicy, GroupLeg, GroupOrder, GroupStrategy
from backtester.tools.alternating_path_gates import components, trade_net
from backtester.tools.timed_hold_gates import variant_report

DAY = date(2026, 1, 5)
START = datetime(2026, 1, 5, 10, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


def at(m):
    return START + m * MINUTE


def intent(day=DAY, first=Direction.BULLISH):
    return GroupOrder(str(day), (GroupLeg("A", first, 1, 2),
                                GroupLeg("B", Direction.BEARISH, 1, 1)),
                      datetime.combine(day, START.timetz()) + MINUTE,
                      EntryPolicy.NEXT_OPEN_ALL_OR_NONE,
                      ExitPolicy.ALL_LEGS_NEXT_OPEN_AFTER_STOP, 3)


class Toy(GroupStrategy):
    legs = ("A", "B")
    references = (ReferenceInput("REF", "observation", (Timeframe.M1, Timeframe.M5),
                                 timedelta(minutes=5), required=False),)

    def __init__(self):
        self.seen = []

    def on_group_candle(self, now, market):
        self.seen.append(now)
        return [intent(now.date())] if (now.hour, now.minute) == (10, 1) else []

    def group_exits(self, now, market, open_groups):
        return [g.group_id for g in open_groups] if now.minute == 3 else []


def costs():
    return CostConfig(symbols={s: SymbolCosts(.125, .25, 1, slippage=.0625)
                               for s in ("A", "B")}, conversion_adjustment=0)


def cache(root, symbol, day=DAY, minutes=range(6)):
    path = cache_path(root, symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in minutes:
        price = 102 if symbol == "A" and i >= 3 else 100
        rows.append((f"10:{i:02}", price, price + .125, price - .125, price, 1, 0))
    m1(*rows, day=day.isoformat()).to_parquet(path, index=False)


@pytest.fixture
def sources(tmp_path):
    for symbol in ("A", "B", "REF"):
        cache(tmp_path / symbol, symbol)
        cache(tmp_path / symbol, symbol, DAY + timedelta(days=1))
    return SymbolSources({s: tmp_path / s for s in ("A", "B", "REF")})


def test_run_loads_bounded_bundle_and_matches_hand_accounting(sources, monkeypatch):
    calls = []
    fetch = CacheAdapter.fetch_frame

    def bounded(self, symbol, tf, start, end, **kwargs):
        calls.append((symbol, tf, start, end))
        assert end <= at(5)
        return fetch(self, symbol, tf, start, end, **kwargs)

    monkeypatch.setattr(CacheAdapter, "fetch_frame", bounded)
    bundle = group_runner.load_group_inputs(Toy(), START, at(5), sources, warmup_days=0)
    assert set(bundle) == {"A", "B", "REF"}
    assert {s.timeframe for s in bundle["REF"]} == {Timeframe.M1, Timeframe.M5}
    assert all(c.ts + s.timeframe.duration <= at(5)
               for many in bundle.values() for s in many for c in s._candles)
    result = group_runner.run_group(Toy(), START, at(5), sources, costs(), values=(1, 1))
    assert isinstance(result, GroupRunResult)
    fills = (LegFill(100.1875, 101.9375, at(1), at(3), ExitReason.SIGNAL, 1, 1, 100, 102),
             LegFill(99.9375, 100.1875, at(1), at(3), ExitReason.SIGNAL, 1, 1, 100, 100))
    expected = group_result(intent(), fills, costs(), (1, 1))
    assert result.closed == (expected,)
    assert expected.r_gross == 2 / 3
    assert expected.r_net == 1 / 3  # (2 - .25 spread - .25 slippage - .5 fees) / D=3
    assert result.fills[str(DAY)] == fills
    assert {c[:2] for c in calls} >= {("A", Timeframe.M1), ("B", Timeframe.M1)}


def test_rows_roundtrip_every_record_field_and_count_groups(sources, tmp_path):
    result = group_runner.run_group(Toy(), DAY, DAY, sources, costs())
    rows = group_runner.group_trade_rows(result)
    assert len(rows) == len(result.closed) == 1
    row = rows[0]
    assert tuple(row) == TRADE_COLUMNS
    assert row["symbol"] == "A/B" and row["direction"] == "long"
    assert row["entry_time"] == row["entry_candle"] == at(1).isoformat()
    assert row["exit_time"] == at(3).isoformat()
    assert abs(row["entry"] - row["initial_stop"]) == 1
    folder = group_runner.write_group_results(result, tmp_path / "out", "r", {"label": "test"})
    assert read_trades(folder) == [TradeRecord.from_row(row)]
    record, = read_trades(folder)
    assert components(record) == pytest.approx((.25 / 3, .5 / 3, .25 / 3))
    assert trade_net(record, "all") == pytest.approx(0)  # (2 - twice 1) / 3
    report = variant_report([record], DAY, DAY)
    assert report["trades"] == 1
    assert report["net_r"]["all"] == pytest.approx(0)


def test_signed_financing_and_short_synthetic_risk():
    order = replace(intent(first=Direction.BEARISH), group_id="costed")
    exit_at = at(3) + timedelta(days=1)
    cfg = CostConfig(swap_credit=True,
                     symbols={s: SymbolCosts(.125, .25, 1, swap_short_per_lot=.5,
                                             funding=True) for s in ("A", "B")})
    # Inject funding observations, never load a real funding file.
    series = FundingSeries((at(2),), (.001,))
    from unittest.mock import patch

    fills = tuple(LegFill(100, 99.25, at(1), exit_at, ExitReason.SIGNAL,
                          1, 1, 100, 99) for _ in order.legs)
    with patch.object(CostConfig, "funding_series", return_value=series):
        closed = group_result(order, fills, cfg, (1, 1))
    result = GroupRunResult((closed,), (), (), (), {"costed": fills})
    row, = group_runner.group_trade_rows(result)
    record = TradeRecord.from_row(row)
    assert record.direction == "short" and record.initial_stop - record.entry == 1
    assert record.swap_r == pytest.approx(1 / 3)
    assert record.funding_r == pytest.approx(.2 / 3)
    assert record.conversion_r == 0
    assert components(record) == pytest.approx((.25 / 3, .5 / 3, .25 / 3))
    assert trade_net(record, "all") == pytest.approx((2 - 2 * 1 + 1 + .2) / 3)


def test_artifacts_metadata_leg_attribution_and_residual(sources, tmp_path):
    result = group_runner.run_group(Toy(), DAY, DAY, sources, costs(), values={"A": 2, "B": 1})
    residual = UnresolvedGroup("residual", (OpenGroupLeg(
        "B", Direction.BEARISH, 1, at(1), 100, 99.9375, 101, 100, at(2)),))
    result = replace(result, unresolved=(residual,))
    folder = group_runner.write_group_results(result, tmp_path / "out", "r", {})
    assert {p.name for p in folder.iterdir()} == {
        "trades.csv", "group_legs.csv", "rejected.csv", "unresolved.json", "settings.json"}
    settings = json.loads((folder / "settings.json").read_text(encoding="utf-8"))
    assert settings["strategy"]["name"] == "Toy"
    assert settings["run"]["cache_dirs"] == {s: str(sources.cache_dir(s)) for s in sources.symbols}
    assert settings["run"]["legs"] == ["A", "B"]
    assert settings["run"]["start"] == settings["run"]["end"] == str(DAY)
    assert settings["values"] == {"A": 2, "B": 1}
    assert settings["costs"]["spread_enabled"] is True
    assert "D" in settings["normalization"]
    with (folder / "group_legs.csv").open(newline="", encoding="utf-8") as stream:
        legs = list(csv.DictReader(stream))
    assert len(legs) == 2
    assert [r["symbol"] for r in legs] == ["A", "B"]
    assert all(r["group_id"] == str(DAY) for r in legs)
    assert sum(float(r["net_r"]) for r in legs) == pytest.approx(result.closed[0].r_net)
    assert sum(float(r["weight"]) for r in legs) == 1
    unresolved = json.loads((folder / "unresolved.json").read_text(encoding="utf-8"))
    assert unresolved[0]["open_legs"][0]["mark_time"] == at(2).isoformat()
    assert unresolved[0]["open_legs"][0]["mark"] == 100


def test_actual_end_of_data_residual_is_not_a_closed_trade(sources, tmp_path):
    result = group_runner.run_group(Toy(), START, at(3), sources, costs())
    assert not result.closed and len(result.unresolved) == 1
    assert len(result.unresolved[0].open_legs) == 2
    assert group_runner.group_trade_rows(result) == []
    first = group_runner.write_group_results(result, tmp_path / "out", None, {})
    second = group_runner.write_group_results(result, tmp_path / "out", None, {})
    assert first != second and "_A-B" in first.name
    assert read_trades(first) == []


def test_missing_leg_names_symbol_even_if_warmup_exists(sources):
    missing = SymbolSources({**sources.cache_dirs, "B": sources.cache_dir("B") / "missing"})
    cache(missing.cache_dir("B"), "B", DAY - timedelta(days=1))
    with pytest.raises(NoDataError, match="B"):
        group_runner.run_group(Toy(), DAY, DAY, missing, costs())


def test_warmup_updates_strategy_but_does_not_create_positions(sources):
    previous = DAY - timedelta(days=1)
    for s in sources.symbols:
        cache(sources.cache_dir(s), s, previous)
    strategy = Toy()
    result = group_runner.run_group(strategy, DAY, DAY, sources, costs())
    assert min(strategy.seen).date() == previous
    assert [g.group_id for g in result.closed] == [str(DAY)]
    assert set(result.fills) == {str(DAY)}
    assert not result.unresolved


@pytest.mark.parametrize("warmup", [-1, 1.5])
def test_invalid_warmup(sources, warmup):
    with pytest.raises(ValueError, match="warmup"):
        group_runner.load_group_inputs(Toy(), DAY, DAY, sources, warmup_days=warmup)


def test_invalid_range_and_non_utc_rejected_before_loading(sources):
    with pytest.raises(ValueError, match="end"):
        group_runner.run_group(Toy(), at(5), START, sources)
    with pytest.raises(ValueError, match="UTC"):
        group_runner.run_group(Toy(), START.replace(tzinfo=None), at(5), sources)


def test_missing_reference_and_gaps_are_not_fabricated(sources):
    strategy = Toy()
    strategy.references = (*strategy.references, ReferenceInput(
        "EMPTY", "observation", (Timeframe.M1,), MINUTE, required=False))
    sources = SymbolSources({**sources.cache_dirs, "EMPTY": sources.cache_dir("A")})
    after_gap = DAY + timedelta(days=3)
    for s in strategy.legs:
        cache(sources.cache_dir(s), s, after_gap)
    bundle = group_runner.load_group_inputs(strategy, DAY, after_gap, sources)
    assert len(bundle["EMPTY"][0]) == 0
    assert {c.ts.date() for c in bundle["A"][0]._candles} == {
        DAY, DAY + timedelta(days=1), after_gap}


def test_rejection_written_and_existing_run_preserved(sources, tmp_path):
    cfg = replace(costs(), max_cost_r=.0001)
    result = group_runner.run_group(Toy(), DAY, DAY, sources, cfg)
    assert not result.closed and len(result.rejected) == 1
    folder = group_runner.write_group_results(result, tmp_path, "r", {})
    with (folder / "rejected.csv").open(newline="", encoding="utf-8") as stream:
        row, = list(csv.DictReader(stream))
    assert row["group_id"] == str(DAY) and "cost limit" in row["reason"]
    with pytest.raises(FileExistsError):
        group_runner.write_group_results(result, tmp_path, "r", {})
    assert (folder / "settings.json").is_file()


def test_last_exit_and_mixed_reasons_stay_one_group():
    fills = (LegFill(100, 98, at(1), at(2), ExitReason.STOP_LOSS, 1, 1, 100, 98),
             LegFill(100, 100, at(1), at(4), ExitReason.SIGNAL, 1, 1, 100, 100))
    cfg = replace(costs(), spread_enabled=False, commission_enabled=False, swap_enabled=False)
    closed = group_result(intent(), fills, cfg, (1, 1))
    result = GroupRunResult((closed,), (), (), (), {str(DAY): fills})
    row, = group_runner.group_trade_rows(result)
    assert row["exit_time"] == at(4).isoformat()
    assert row["exit_reason"] == "group" and row["r_gross"] == -2 / 3


def test_real_residual_keeps_stale_peer_mark(sources, tmp_path):
    # B closes for the day after entry; A subsequently stops at its own fresh candle.
    cache(sources.cache_dir("B"), "B", minutes=range(2))
    path = cache_path(sources.cache_dir("A"), "A", DAY)
    m1(("10:00", 100, 100.125, 99.875, 100, 1, 0),
       ("10:01", 100, 100.125, 99.875, 100, 1, 0),
       ("10:02", 100, 100.125, 97, 99, 1, 0),
       ("10:04", 99, 99.125, 98.875, 99, 1, 0),
       day=str(DAY)).to_parquet(path, index=False)
    result = group_runner.run_group(Toy(), START, at(5), sources, costs())
    assert not result.closed
    residual, = result.unresolved
    peer, = residual.open_legs
    assert peer.symbol == "B" and peer.mark_time == at(2)
    assert result.fills[str(DAY)][0].exit_reason is ExitReason.STOP_LOSS
    assert result.fills[str(DAY)][1] is None
    folder = group_runner.write_group_results(result, tmp_path / "out", "r", {})
    saved = json.loads((folder / "unresolved.json").read_text(encoding="utf-8"))
    assert saved[0]["open_legs"][0]["mark_time"] == at(2).isoformat()
