"""Session high/low zones on 30m.

Spec: strategy-session-zones.md › Session zones.
- Per session: the single most extreme CONFIRMED swing high and low; if the absolute extreme
  is unconfirmed, use the most extreme confirmed one.
- A swing confirmed by the first candle of the next session doesn't count.
- High zone: highest wick to lowest body top of its swing candles; low zone mirrored.
- Valid only during the next session (London->NY, NY->Tokyo, Tokyo->London);
  Friday NY carries into Monday Tokyo (config flag).
- Zone flips and the second-break kill rule are tracked here per zone.
TODO: implement.
"""
