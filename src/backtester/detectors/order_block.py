"""Order block detector.

Spec: confluences.md › Order block.
Range = the whole consecutive same-color leg from the prior swing point to the swing extreme,
lowest wick to highest wick. Green leg = bearish OB, red leg = bullish OB. Dojis inside the
leg are ignored; an opposite-color candle ends the leg and its wick is excluded.
Exists from the candle that confirms the swing extreme. Validation via zone.Zone.
TODO: implement.
"""
