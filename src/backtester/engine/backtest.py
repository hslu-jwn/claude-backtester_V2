"""The backtest loop. See docs/ARCHITECTURE.md › How a backtest steps through time.

Per base candle: update open trades (SL before TP when both are inside one candle),
update detectors for timeframes whose candle just closed, call the strategy, fill new
orders at the close. Apply the session-start break-even rule to open trades.
Output: list of closed Trades (results in R).
TODO: implement.
"""
