"""Run summary on R trade lists. Spec: ROADMAP.md › 3.4 (analytics/metrics.py)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backtester.analytics.metrics import max_drawdown, summarize
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
