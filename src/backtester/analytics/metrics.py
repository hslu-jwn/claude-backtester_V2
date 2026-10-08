"""Metrics on lists of closed trades (R multiples). Spec: ROADMAP.md › 3.4.

`summarize` gives the short summary of a backtest run:
- trades; wins / losses / break-evens and the win rate, by the net result (after costs):
  win r_net > 0, loss r_net < 0, break-even |r_net| < `BREAK_EVEN_TOL` (a SL moved to
  break-even with costs ends at 0R net);
- net R gross (chart prices, no costs) and net (after spread and commission), and the
  average R per trade (expectancy), net;
- average R:R: the planned R if every TP is hit (`TradeResult.planned_r`, share-weighted);
- max drawdown in R, gross and net: the deepest fall of the cumulative R from its peak
  (starting at 0), with trades counted when they close (exit time order).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from backtester.engine.trade import TradeResult

BREAK_EVEN_TOL = 1e-9


def max_drawdown(results: Iterable[float]) -> float:
    """Deepest drop of the running sum below its peak (peak starts at 0), as a value >= 0."""
    equity = peak = worst = 0.0
    for r in results:
        equity += r
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def summarize(trades: Sequence[TradeResult]) -> dict:
    n = len(trades)
    wins = sum(t.r_net > BREAK_EVEN_TOL for t in trades)
    losses = sum(t.r_net < -BREAK_EVEN_TOL for t in trades)
    by_exit = sorted(trades, key=lambda t: (t.exit_time, t.entry_time, t.symbol))
    net_gross = sum(t.r_gross for t in trades)
    net = sum(t.r_net for t in trades)
    return {
        "trades": n,
        "wins": wins,
        "losses": losses,
        "break_even": n - wins - losses,
        "win_rate": wins / n if n else None,
        "net_r_gross": net_gross,
        "net_r_net": net,
        "avg_r_net": net / n if n else None,
        "avg_rr": sum(t.planned_r for t in trades) / n if n else None,
        "max_drawdown_r_gross": max_drawdown(t.r_gross for t in by_exit),
        "max_drawdown_r_net": max_drawdown(t.r_net for t in by_exit),
    }
