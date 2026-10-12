"""Builder for hand-written M1 cache frames (same columns as a cached day, `data/cache.py`)."""

from __future__ import annotations

import pandas as pd

DAY = "2026-09-02"
_FIELDS = ("open", "high", "low", "close")


def m1(*rows: tuple[str, float, float, float, float, float, float], day: str = DAY) -> pd.DataFrame:
    """rows: (HH:MM, bid open, high, low, close, bid volume, spread). Ask = bid + spread,
    ask volume = bid volume, like a real cache file."""
    records = [
        {
            "ts": pd.Timestamp(f"{day} {hhmm}", tz="UTC"),
            **{f"bid_{k}": v for k, v in zip(_FIELDS, (o, h, lo, c))},
            "bid_volume": vol,
            **{f"ask_{k}": v + spread for k, v in zip(_FIELDS, (o, h, lo, c))},
            "ask_volume": vol,
        }
        for hhmm, o, h, lo, c, vol, spread in rows
    ]
    return pd.DataFrame(records)
