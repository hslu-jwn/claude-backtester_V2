"""Entry sequence state machine (one instance per zone and direction).

Spec: strategy-session-zones.md › Entry sequence, Invalidation & reset, Zone flips.
States (long): WAIT_SWEEP -> WAIT_30M_REACTION -> WAIT_5M_BOS -> WAIT_CONFLUENCE -> ENTER
- Sweep: wick into the support zone.
- 30m reaction: green 30m close above the zone (red never counts).
- 5m BOS: close above the high right beforehand, during that 30m candle or after.
- Confluence (FVG/OB/breaker/BPR) tapped, then a green 5m close above it -> enter at that close.
Resets: confluence close-through invalidates it; bearish BOS after the bullish BOS -> restart;
next session start kills untriggered setups. A red 30m close below support flips to a short
setup starting at WAIT_5M_BOS.
TODO: implement.
"""
