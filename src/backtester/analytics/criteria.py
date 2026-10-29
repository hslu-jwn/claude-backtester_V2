"""Development criteria inputs from persisted trades. Spec: research-runner.md > Fast loop."""

from collections import defaultdict
from datetime import UTC

from backtester.analytics.robustness import RobustnessConfig, stressed_net, trade_robustness


def criteria_inputs(trades, variant_nets, middle_year, stress_factor):
    """Build development inputs. Spec: research-runner.md > Fast loop (V2.6k)."""
    gross = defaultdict(float)
    days = defaultdict(float)
    tags = {}
    for trade in trades:
        gross[trade.symbol] += trade.r_gross
        days[trade.exit_time.astimezone(UTC).date()] += trade.r_net
        for tag in trade.tags:
            entry = tags.setdefault(tag, {"count": 0, "net_r": 0.0})
            entry["count"] += 1
            entry["net_r"] += trade.r_net
    ordered = sorted(days.values(), reverse=True)
    halves = trade_robustness(trades, RobustnessConfig(first_half_end_year=middle_year))
    return {
        "variants_positive_net": sum(n > 0 for n in variant_nets),
        "variants": len(variant_nets),
        "net_r": sum(t.r_net for t in trades),
        "gross_r": sum(t.r_gross for t in trades),
        "gross_by_symbol": dict(gross),
        "symbols_positive_gross": sum(n > 0 for n in gross.values()),
        "net_r_costs_x2": stressed_net(trades, 2.0),
        "costs_x2_factor": 2.0,
        "net_r_costs_stress": stressed_net(trades, stress_factor),
        "costs_stress_factor": stress_factor,
        "half_first_net_r": halves["half_first_net_r"],
        "half_second_net_r": halves["half_second_net_r"],
        "net_r_without_best_days": {str(k): sum(ordered[k:]) for k in (1, 5, 10)},
        "stop_share": sum(
            getattr(t.exit_reason, "value", t.exit_reason) == "stop_loss" for t in trades
        )
        / len(trades)
        if trades
        else 0.0,
        "trade_tags": tags,
    }
