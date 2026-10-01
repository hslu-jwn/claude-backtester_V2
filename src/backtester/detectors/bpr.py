"""Balanced price range detector.

Spec: confluences.md › Balanced price range.
Overlap of a bullish and a bearish FVG; if one was invalidated as the other formed, use its
stored range. Staleness rule is decided in the strategy layer. Validation via zone.Zone.
TODO: implement; consumes fvg events.
"""
