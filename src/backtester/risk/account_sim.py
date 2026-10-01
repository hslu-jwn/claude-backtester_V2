"""Account simulator: replays trades in time order, candle by candle.
Equity includes floating P/L at the worst point of each candle (no lookahead), handles the
daily reset with open trades, applies personal rules, reports pass/fail + reason + day.
TODO: implement.
"""
