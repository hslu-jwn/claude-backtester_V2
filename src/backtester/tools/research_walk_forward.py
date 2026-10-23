"""Saved-trade walk-forward diagnostic. Spec: research-runner.md > Walk-forward."""

from datetime import date
from statistics import mean

from backtester.analytics.records import read_trades
from backtester.analytics.scorecard import scorecard
from backtester.analytics.walk_forward import WalkForwardConfig, walk_forward

COLUMNS = (
    "test_year",
    "picked_variant",
    "train_years",
    "train_net_r",
    "net_r",
    "chosen_variant",
    "chosen_net_r",
    "trades",
)


def summarize_walk_forward(variants, chosen, start, end, mode, train_years):
    """Use development entries only; training outcomes must be closed at selection."""
    development = {
        name: [t for t in trades if start <= t.entry_time.date() <= end]
        for name, trades in variants.items()
    }
    result = walk_forward(
        development,
        WalkForwardConfig(mode=mode, train_years=train_years),
        first_year=start.year,
        last_year=end.year,
    )
    rows = []
    for pick in result.picks:
        rows.append(
            {
                "test_year": pick.year,
                "picked_variant": pick.variant,
                "train_years": ",".join(map(str, pick.train_years)),
                "train_net_r": pick.train_net,
                "net_r": sum(t.r_net for t in pick.test_trades),
                "chosen_variant": chosen,
                "chosen_net_r": sum(
                    t.r_net for t in development[chosen] if t.entry_time.year == pick.year
                )
                if chosen
                else None,
                "trades": len(pick.test_trades),
            }
        )
    oos_start = date(result.picks[0].year, 1, 1) if result.picks else start
    card = scorecard(result.chained, start=oos_start, end=end)
    annual_train = mean(p.train_net / len(p.train_years) for p in result.picks) if rows else None
    efficiency = (
        card["net_r"] / len(rows) / annual_train
        if annual_train is not None and annual_train > 0
        else None
    )
    return rows, {
        "mode": mode,
        "train_years": train_years,
        "years": len(rows),
        "mean_train_net_r_per_year": annual_train,
        "efficiency": efficiency,
        "scorecard": card,
    }


def from_saved(folder, variants, chosen, start, end, mode, train_years):
    """Read persisted runs in original variant order, including on resume."""
    trades = {v.id: read_trades(folder / "variants" / v.id) for v in variants}
    return summarize_walk_forward(trades, chosen, start, end, mode, train_years)


def report(info):
    if info is None:
        return []
    lines = ["", "## Walk-forward", "", f"Mode: {info['mode']}; OOS years: {info['years']}."]
    if not info["years"]:
        return lines + ["No yearly OOS windows (at least two development years needed)."]
    efficiency = info["efficiency"]
    lines += [
        "Walk-forward efficiency: "
        + (
            f"{efficiency:.3f}"
            if efficiency is not None
            else "n/a (nonpositive annual training net R)."
        ),
        "",
        "Chained development OOS scorecard:",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    lines += [
        f"| {key} | {value if value is not None else 'n/a'} |"
        for key, value in info["scorecard"].items()
    ]
    return lines
