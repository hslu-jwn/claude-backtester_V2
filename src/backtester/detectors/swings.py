"""Swing high / low detector.

Spec: confluences.md › Swing high / low.
- High: green followed by red; price = highest wick of the two.
- Low: red followed by green; price = lowest wick of the two.
- Doji/thin candles are skipped and don't break the pattern.
Emits a SwingPoint when the reversing candle closes (that candle confirms it).
TODO: implement. Doji threshold must be a config parameter.
"""
