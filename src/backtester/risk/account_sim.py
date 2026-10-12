"""Account simulator: replays the R trades in time order, candle by candle, no lookahead.
Balance (closed trades) and equity incl. floating P/L at each candle's worst point; costs,
personal daily stop, max open risk with correlation groups, drawdown scaling; skipped trades
listed with their reason. Spec: risk-management.md › Account simulator. TODO: implement.
"""
