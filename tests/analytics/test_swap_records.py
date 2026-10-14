"""swap_r in the results files: written to trades.csv, read back, 0 for old files."""

from __future__ import annotations

from backtester.analytics.records import TradeRecord
from backtester.runner import TRADE_COLUMNS

ROW = {
    "id": "1", "symbol": "XAUUSD", "direction": "long",
    "entry_time": "2026-01-05T10:00:00+00:00", "entry_candle": "2026-01-05T09:55:00+00:00",
    "entry": "100", "initial_stop": "98", "exit_time": "2026-01-06T10:00:00+00:00",
    "exit_price": "104", "exit_reason": "take_profit", "r_gross": "2", "r_net": "1.9",
}  # fmt: skip


def test_trades_csv_has_swap_r_next_to_the_other_costs():
    assert TRADE_COLUMNS.index("swap_r") == TRADE_COLUMNS.index("commission_r") + 1


def test_record_reads_swap_r_and_missing_or_empty_is_zero():
    assert TradeRecord.from_row({**ROW, "swap_r": "-0.035"}).swap_r == -0.035
    assert TradeRecord.from_row(ROW).swap_r == 0.0  # old result folder
    assert TradeRecord.from_row({**ROW, "swap_r": ""}).swap_r == 0.0
