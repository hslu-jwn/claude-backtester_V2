"""Break of structure (BOS).

Spec: confluences.md › Break of structure.
Uptrend: a CLOSE below the most recent prior swing low (wick never counts); downtrend
mirrored. The trend label flips immediately and the broken level becomes the new reference.
Note: strategy 1 also uses a local "5m BOS" = close above the high right beforehand
(strategy-session-zones.md › Entry sequence step 3).
TODO: implement.
"""
