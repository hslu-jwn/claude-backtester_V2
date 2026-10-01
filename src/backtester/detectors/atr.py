"""ATR and the strong-move filter.

Spec: confluences.md › Strong-move filter.
A candle is a strong move if its range >= k * ATR(n). Defaults: k = 2.0, n tunable.
TODO: implement incremental ATR (Wilder) and `is_strong_move(candle, atr, k)`.
"""
