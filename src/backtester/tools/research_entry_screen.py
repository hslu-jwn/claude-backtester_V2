"""Chosen-development screen. Spec: research-runner.md > Runner checks (V2.4c)."""

from dataclasses import asdict, replace

from backtester.analytics.entry_screen import EntryScreenConfig, ScreenTrade, judge, screen_variant
from backtester.analytics.records import read_trades
from backtester.core.models import Direction
from backtester.data.sources import UnmappedSymbolError
from backtester.strategy.registry import make_strategy


def calculate(folder, spec, variant_id, start, end, settings, sources) -> dict:
    from backtester.tools.entry_screen import load_m1

    trades = read_trades(folder / "variants" / variant_id)
    symbols = sorted({t.symbol for t in trades})
    try:
        m1s = {s: load_m1(s, sources, start, end) for s in symbols}
    except (SystemExit, FileNotFoundError, UnmappedSymbolError) as error:
        return {"error": str(error)}
    bar_minutes = make_strategy(spec.symbols[0], settings.strategy).base_timeframe.value
    screen_trades = [
        replace(
            ScreenTrade.from_trade(t),
            direction=Direction.BULLISH if t.direction == "long" else Direction.BEARISH,
        )
        for t in trades
    ]
    screen = screen_variant(
        screen_trades,
        m1s,
        bar_minutes,
        settings.engine.costs,
        EntryScreenConfig(),
        variant_id,
        (start, end),
    )
    verdict = judge([screen])
    return dict(
        variant_id=variant_id,
        start=str(start),
        end=str(end),
        bar_minutes=bar_minutes,
        **{**asdict(verdict), "reasons": list(verdict.reasons)},
        trades=screen.trades,
        skipped=screen.skipped,
        flags=[] if verdict.passed else ["entry_screen_failed"],
    )


def markdown(result):
    if result is None:
        return []
    lines = ["", "## Entry screen (chosen development variant)", ""]
    if "error" in result:
        return [*lines, f"Error: {result['error']}"]
    return [
        *lines,
        f"Passed: {result['passed']}",
        (
            f"Cells positive: {result['cells_positive']}/{result['cells']} "
            f"(share {result['cell_share']:.3f}); bracket win rate: {result['bracket_win_rate']:.3f}; "
            f"random percentile: {result['random_percentile']:.3f}."
        ),
        *[f"- {reason}" for reason in result["reasons"]],
    ]
