"""Incremental, timeframe-agnostic pattern detectors.

Spec: docs/confluences.md. Every detector receives a SeriesView once per closed
candle and emits events stamped with the candle that confirmed them.
"""
