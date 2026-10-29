"""Chosen-development diagnostic only. Spec: risk-management.md > Matched monkeys."""

from backtester.analytics.monkeys import MonkeyConfig, matched_monkeys
from backtester.analytics.records import read_trades


def calculate(folder, spec, variant_id, start, end, settings, sources, *, workers=None):
    from backtester.tools.entry_screen import load_m1

    trades = read_trades(folder / "variants" / variant_id)
    symbols = sorted({t.symbol for t in trades})
    m1s = {s: load_m1(s, sources, start, end) for s in symbols}
    result = matched_monkeys(trades, m1s, settings.engine.costs, MonkeyConfig(runs=200), workers)
    return dict(variant_id=variant_id, start=str(start), end=str(end), **result)
