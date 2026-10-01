"""Trend state from swing points.

Spec: confluences.md › Trend.
Uptrend: 2 consecutive HH + HL. Downtrend: 2 consecutive LH + LL. Otherwise sideways.
TODO: implement; consumes SwingPoint events from swings.py.
"""
