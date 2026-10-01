"""Strategy 1: Session Zone Sweep (XAUUSD, GBPJPY, GBPUSD).

Spec: docs/strategy-session-zones.md.
Modules:
  config.py   all tunable parameters (backtest options list)
  zones.py    session high/low zones on 30m
  setup.py    entry sequence state machine (sweep -> 30m reaction -> 5m BOS -> confluence)
  targets.py  stop loss and take profit (zone target, 3R cap, 1h obstacles, 1.2R minimum)
  strategy.py ties it together as a Strategy
"""
