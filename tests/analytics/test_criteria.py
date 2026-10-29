"""Criteria input calculations from saved development trades."""

from datetime import UTC, datetime
from types import SimpleNamespace

from backtester.analytics.criteria import criteria_inputs
from backtester.analytics.robustness import stressed_net


def test_criteria_inputs_from_trades():
    def trade(symbol, gross, net, day, tags, reason):
        time = datetime(2020, 1, day, tzinfo=UTC)
        return SimpleNamespace(
            symbol=symbol,
            r_gross=gross,
            r_net=net,
            entry_time=time,
            exit_time=time,
            tags=tags,
            exit_reason=reason,
        )

    trades = [trade("A", 3, 2, 1, {"month_end"}, "stop_loss"), trade("B", -1, -2, 2, set(), "time")]
    result = criteria_inputs(trades, [1, -2], 2020, 1.5)
    assert result["variants_positive_net"] == 1
    assert result["variants"] == 2
    assert result["gross_by_symbol"] == {"A": 3, "B": -1}
    assert result["symbols_positive_gross"] == 1
    assert result["net_r"] == 0 and result["gross_r"] == 2
    assert result["net_r_costs_x2"] == stressed_net(trades, 2.0)
    assert result["net_r_without_best_days"] == {"1": -2, "5": 0, "10": 0}
    assert result["stop_share"] == 0.5
    assert result["trade_tags"] == {"month_end": {"count": 1, "net_r": 2}}


def test_halves_match_scorecard_and_stop_reason_values():
    from backtester.analytics.records import TradeRecord
    from backtester.analytics.robustness import RobustnessConfig, trade_robustness
    from backtester.core.models import Direction
    from backtester.engine.trade import ExitReason, TradeResult

    at = datetime(2020, 1, 1, tzinfo=UTC)
    engine_trade = TradeResult(
        symbol="A",
        direction=Direction.BULLISH,
        entry_time=at,
        entry_candle=at,
        entry=100,
        entry_fill=100,
        initial_stop=99,
        take_profit=None,
        exit_time=at,
        exit_candle=at,
        exit_price=99,
        exit_fill=99,
        exit_reason=ExitReason.STOP_LOSS,
        r_gross=2,
        r_net=2,
        spread_r=0,
        commission_r=0,
        break_even_time=None,
        break_even_stop=None,
        mae_r=0,
        mfe_r=0,
    )
    record = TradeRecord.from_row(
        {
            "id": 1,
            "symbol": "A",
            "direction": "long",
            "entry_time": datetime(2022, 1, 1, tzinfo=UTC),
            "entry_candle": at,
            "entry": 100,
            "initial_stop": 99,
            "exit_time": datetime(2022, 1, 1, tzinfo=UTC),
            "exit_price": 99,
            "exit_reason": "stop_loss",
            "r_gross": -1,
            "r_net": -1,
        }
    )
    trades = [engine_trade, record]
    cfg = RobustnessConfig(first_half_end_year=2020)
    result = criteria_inputs(trades, [1], 2020, 1.5)
    row = trade_robustness(trades, cfg)
    assert result["half_first_net_r"] == row["half_first_net_r"]
    assert result["half_second_net_r"] == row["half_second_net_r"]
    assert result["stop_share"] == 1.0
