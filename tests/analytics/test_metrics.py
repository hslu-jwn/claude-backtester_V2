"""Run summary on R trade lists. Spec: ROADMAP.md › 3.4 (analytics/metrics.py)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from backtester.analytics.metrics import (
    SPLITS,
    by_confluence,
    by_direction,
    by_session,
    by_symbol,
    by_tag,
    equity_curve,
    longest_streak,
    max_drawdown,
    r_histogram,
    split,
    summarize,
    tp_outcome,
)
from backtester.analytics.records import TradeRecord, confluence_from_reason
from backtester.core.models import Direction
from backtester.engine.trade import ExitReason, TradeResult

T0 = datetime(2026, 9, 2, 8, tzinfo=UTC)


def trade(r_gross, r_net, entry_h, exit_h, tp=102.0, symbol="XAUUSD"):
    """A long from 100 with SL 99 (1R = 1.0), TP `tp`."""
    return TradeResult(
        symbol=symbol,
        direction=Direction.BULLISH,
        entry_time=T0 + timedelta(hours=entry_h),
        entry_candle=T0 + timedelta(hours=entry_h, minutes=-5),
        entry=100.0,
        entry_fill=100.0,
        initial_stop=99.0,
        take_profit=tp,
        exit_time=T0 + timedelta(hours=exit_h),
        exit_candle=T0 + timedelta(hours=exit_h, minutes=-5),
        exit_price=100.0 + r_gross,
        exit_fill=100.0 + r_gross,
        exit_reason=ExitReason.TAKE_PROFIT,
        r_gross=r_gross,
        r_net=r_net,
        spread_r=0.0,
        commission_r=r_gross - r_net,
        break_even_time=None,
        break_even_stop=None,
        mae_r=0.0,
        mfe_r=0.0,
    )


def test_max_drawdown_from_the_running_peak_starting_at_zero():
    assert max_drawdown([]) == 0
    assert max_drawdown([2, -1, -1.5, 3, -0.5]) == pytest.approx(2.5)
    assert max_drawdown([-1, -1, 2]) == pytest.approx(2)  # below the start counts


def test_summary_counts_wins_losses_and_break_evens_by_net_r():
    trades = [trade(2.0, 1.8, 0, 1), trade(-1.0, -1.1, 2, 3), trade(0.1, 0.0, 4, 5, tp=101.5)]
    s = summarize(trades)
    assert (s["trades"], s["wins"], s["losses"], s["break_even"]) == (3, 1, 1, 1)
    assert s["win_rate"] == pytest.approx(1 / 3)
    assert s["net_r_gross"] == pytest.approx(1.1) and s["net_r_net"] == pytest.approx(0.7)
    assert s["avg_r_net"] == pytest.approx(0.7 / 3)
    assert s["avg_rr"] == pytest.approx((2 + 2 + 1.5) / 3)  # planned R:R


def test_drawdown_uses_exit_time_order():
    # entered first but closed last: the two losses come before the win
    trades = [trade(3.0, 3.0, 0, 10), trade(-1.0, -1.0, 1, 2), trade(-1.0, -1.0, 3, 4)]
    s = summarize(trades)
    assert s["max_drawdown_r_gross"] == pytest.approx(2.0)
    assert s["max_drawdown_r_net"] == pytest.approx(2.0)


def test_empty_summary():
    s = summarize([])
    assert s["trades"] == 0 and s["win_rate"] is None and s["avg_rr"] is None
    assert s["max_drawdown_r_net"] == 0


# --- 3.6: results page metrics ---------------------------------------------------------


def test_average_win_loss_profit_factor_and_expectancy_use_net_r():
    trades = [
        trade(2.0, 1.8, 0, 1),
        trade(-1.0, -1.1, 2, 3),
        trade(3.0, 2.9, 4, 5),
        trade(-1.0, -1.2, 6, 7),
        trade(0.1, 0.0, 8, 9),  # break-even: neither win nor loss
    ]
    s = summarize(trades)
    assert s["avg_win_r"] == pytest.approx((1.8 + 2.9) / 2)
    assert s["avg_loss_r"] == pytest.approx((-1.1 - 1.2) / 2)
    assert s["profit_factor"] == pytest.approx(4.7 / 2.3)
    assert s["expectancy_r"] == pytest.approx((1.8 - 1.1 + 2.9 - 1.2) / 5)
    assert s["avg_r_gross"] == pytest.approx((2 - 1 + 3 - 1 + 0.1) / 5)


def test_no_loss_means_no_profit_factor():
    s = summarize([trade(2.0, 1.8, 0, 1)])
    assert s["profit_factor"] is None and s["avg_loss_r"] is None
    assert s["longest_losing_streak"] == 0 and s["longest_winning_streak"] == 1


def test_longest_streaks_in_exit_order_and_a_break_even_ends_one():
    assert longest_streak([-1, -1, 1, -1, -1, -1, 0.5], -1) == 3
    assert longest_streak([-1, -1, 0.0, -1], -1) == 2  # break-even ends the streak
    # entered in order win, loss, loss, loss; the win closes last -> 3 losses in a row first
    trades = [trade(3.0, 3.0, 0, 10), trade(-1, -1, 1, 2), trade(-1, -1, 3, 4)]
    trades.append(trade(-1, -1, 5, 6))
    assert summarize(trades)["longest_losing_streak"] == 3


def test_equity_curve_starts_at_zero_and_merges_trades_closing_together():
    trades = [trade(2.0, 1.8, 0, 2), trade(-1.0, -1.1, 1, 2), trade(-1.0, -1.1, 3, 4)]
    curve = equity_curve(trades)
    assert [p["time"] for p in curve] == [T0, T0 + timedelta(hours=2), T0 + timedelta(hours=4)]
    assert curve[0] == {"time": T0, "gross": 0.0, "net": 0.0, "drawdown": 0.0}
    assert curve[1]["gross"] == pytest.approx(1.0) and curve[1]["net"] == pytest.approx(0.7)
    assert curve[1]["drawdown"] == pytest.approx(0.0)  # a new peak
    assert curve[2]["net"] == pytest.approx(-0.4) and curve[2]["drawdown"] == pytest.approx(-1.1)
    assert equity_curve([]) == []


def test_r_histogram_bins_are_aligned_and_include_empty_ones():
    bins = r_histogram([-1.0, -1.05, 0.0, 1.2, 1.4], width=0.5)
    assert [(b["lo"], b["count"]) for b in bins] == [
        (-1.5, 1),  # -1.05
        (-1.0, 1),  # -1.0 sits at the start of its bin
        (-0.5, 0),
        (0.0, 1),
        (0.5, 0),
        (1.0, 2),
    ]
    assert r_histogram([]) == []


def record(**kw):
    row = {
        "id": 1, "symbol": "XAUUSD", "direction": "long", "session": "london 2026-09-02",
        "entry_time": "2026-09-02T08:00:00+00:00", "entry_candle": "2026-09-02T07:55:00+00:00",
        "entry": "100", "initial_stop": "99", "take_profit": "101.2", "take_profit_2": "",
        "tp1_share": "1.0", "planned_rr": "1.2", "exit_time": "2026-09-02T09:00:00+00:00",
        "exit_price": "101.2", "exit_reason": "take_profit", "r_gross": "1.2", "r_net": "1.1",
        "spread_r": "0.05", "commission_r": "0.05", "tags": "", "confluence": "fvg",
        "reason": "", "parts": json.dumps([{"share": 1.0, "reason": "take_profit"}]),
    }  # fmt: skip
    row.update(kw)
    return TradeRecord.from_row(row)


def tp_parts(*reasons):
    return json.dumps([{"share": 0.5, "reason": r} for r in reasons])


def test_tp_outcomes():
    assert tp_outcome(record()) == "TP (one target)"
    assert tp_outcome(record(parts=tp_parts("stop_loss"))) == "no TP"
    two = {"take_profit_2": "103", "tp1_share": "0.5"}
    assert tp_outcome(record(**two, parts=tp_parts("take_profit", "take_profit"))) == "TP1 + TP2"
    assert tp_outcome(record(**two, parts=tp_parts("take_profit", "break_even"))) == (
        "TP1, rest out"
    )
    assert tp_outcome(record(**two, parts=tp_parts("stop_loss"))) == "no TP"


def test_splits_group_and_summarize_in_first_seen_order():
    trades = [
        record(id=1, symbol="GBPUSD", session="tokyo 2026-09-02", tags="last_90m"),
        record(id=2, direction="short", confluence="order_block", r_net="-1", r_gross="-1"),
        record(id=3, session="", confluence=""),
    ]
    assert list(split(trades, by_symbol)) == ["GBPUSD", "XAUUSD"]
    assert split(trades, by_symbol)["XAUUSD"]["trades"] == 2
    assert list(split(trades, by_session)) == ["tokyo", "london", "none"]
    assert list(split(trades, by_direction)) == ["long", "short"]
    assert list(split(trades, by_tag)) == ["last 1.5h", "other"]
    assert set(SPLITS) == {"Symbol", "Session", "Long / short", "Confluence", "TP outcome", "Tag"}


def test_old_files_without_a_confluence_column_take_it_from_the_reason():
    reason = "tokyo low zone, 30m reaction 07:00, 5m BOS 07:35, equilibrium, TP1 min R"
    assert by_confluence(record(confluence="", reason=reason)) == "equilibrium"
    assert confluence_from_reason("no targets here") == ""


def test_trades_closing_at_the_same_time_are_one_drawdown_step():
    # a win and a loss closing in the same candle: no peak in between, like the curve
    trades = [trade(2.0, 2.0, 0, 2), trade(-1.0, -1.0, 1, 2), trade(-1.0, -1.0, 3, 4)]
    assert summarize(trades)["max_drawdown_r_net"] == pytest.approx(1.0)
    assert min(p["drawdown"] for p in equity_curve(trades)) == pytest.approx(-1.0)
