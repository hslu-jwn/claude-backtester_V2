"""Breaker block detector.

Spec: confluences.md › Breaker block.
An OB invalidated by a later BOS through the level it defended becomes a breaker with the
same range and OPPOSITE bias. Exists from the BOS candle. Validation via zone.Zone.
TODO: implement; consumes order_block + bos events.
"""
