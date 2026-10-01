"""Fair value gap detector.

Spec: confluences.md › Fair value gap.
3-candle pattern; gap between the wicks of candle 1 and candle 3 (candle 2's wick ignored).
Bullish in an uptrend, bearish in a downtrend. Optional strong-move filter.
Confirmed at the close of candle 3. Validation via zone.Zone.
TODO: implement.
"""
