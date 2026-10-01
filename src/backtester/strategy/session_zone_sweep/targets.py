"""Stop loss and take profit for strategy 1.

Spec: strategy-session-zones.md › Stop loss, Take profit.
SL: below the entry confluence's low + buffer; if the confluence is small, below the BOS
leg's low. TP: lowest point of the resistance zone, capped at 3R; fallback 1.2-2R at 1h
highs/lows/confluences when price is already beyond the zone; pass at most N major 1h
obstacles that existed before entry (clustered within 0.2R); skip the trade if TP < 1.2R.
Break-even move at the next session start is handled by the engine via a trade rule.
TODO: implement.
"""
