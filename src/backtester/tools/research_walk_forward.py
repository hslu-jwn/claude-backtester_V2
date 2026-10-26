"""Saved-trade walk-forward diagnostic. Spec: research-runner.md > Walk-forward."""

from datetime import UTC, date, datetime, time, timedelta
from statistics import mean

from backtester.analytics.records import read_trades
from backtester.analytics.scorecard import scorecard
from backtester.analytics.walk_forward import WalkForwardConfig, walk_forward

LEGACY_COLUMNS = (
    "test_year",
    "picked_variant",
    "train_years",
    "train_net_r",
    "net_r",
    "chosen_variant",
    "chosen_net_r",
    "trades",
)
COLUMNS = (
    "window",
    "train_start",
    "train_end",
    "test_start",
    "test_end",
    "picked_variant",
    "train_net_r",
    "train_net_r_per_month",
    "net_r",
    "test_net_r_per_month",
    "wfe",
    "trades",
    "max_dd_r",
    "chosen_variant",
    "chosen_net_r",
)
STUDY_COLUMNS = (
    "train_months",
    "test_months",
    "windows",
    "efficiency",
    "chained_net_r_per_month",
    "positive_window_share",
    "reason",
)


def _summarize_yearly(variants, chosen, start, end, mode, train_years):
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


def summarize_walk_forward(
    variants,
    chosen,
    start,
    end,
    mode,
    train_years=None,
    *,
    train_months=24,
    test_months=6,
    step_months=None,
):
    """Spec: research-runner.md > Walk-forward; public dates are inclusive UTC days."""
    if train_years is not None:
        return _summarize_yearly(variants, chosen, start, end, mode, train_years)
    left = datetime.combine(start, time(), UTC)
    right = datetime.combine(end + timedelta(days=1), time(), UTC)
    development = {
        name: [t for t in ts if left <= t.entry_time < right] for name, ts in variants.items()
    }
    cfg = WalkForwardConfig(
        mode=mode, train_months=train_months, test_months=test_months, step_months=step_months
    )
    result = walk_forward(development, cfg, start=left, end=right)
    rows = []
    for p in result.picks:
        card = scorecard(
            p.test_trades,
            start=p.test_start.date(),
            end=(p.test_end - timedelta(microseconds=1)).date(),
        )
        train_rate = p.train_net / p.train_months
        test_rate = card["net_r"] / p.test_months
        rows.append(
            {
                "window": p.window,
                "train_start": p.train_start.isoformat(),
                "train_end": p.train_end.isoformat(),
                "test_start": p.test_start.isoformat(),
                "test_end": p.test_end.isoformat(),
                "picked_variant": p.variant,
                "train_net_r": p.train_net,
                "train_net_r_per_month": train_rate,
                "net_r": card["net_r"],
                "test_net_r_per_month": test_rate,
                "wfe": test_rate / train_rate if train_rate > 0 else None,
                "trades": card["trades"],
                "max_dd_r": card["max_dd_r"],
                "chosen_variant": chosen,
                "chosen_net_r": sum(
                    t.r_net
                    for t in development[chosen]
                    if p.test_start <= t.entry_time < p.test_end
                )
                if chosen
                else None,
            }
        )
    eligible = [r for r in rows if r["train_net_r"] > 0]
    train_rate = mean(r["train_net_r_per_month"] for r in eligible) if eligible else None
    test_rate = mean(r["test_net_r_per_month"] for r in eligible) if eligible else None
    card = scorecard(
        result.chained, start=result.picks[0].test_start.date() if rows else start, end=end
    )
    months = sum(p.test_months for p in result.picks)
    changes = sum(a.variant != b.variant for a, b in zip(result.picks, result.picks[1:]))
    return rows, {
        "mode": mode,
        "train_months": train_months,
        "test_months": test_months,
        "step_months": cfg.step_months,
        "windows": len(rows),
        "reason": result.reason,
        "mean_train_net_r_per_month": train_rate,
        "mean_test_net_r_per_month": test_rate,
        "efficiency": test_rate / train_rate if eligible else None,
        "positive_window_share": sum(r["net_r"] > 0 for r in rows) / len(rows) if rows else None,
        "pick_changes": changes,
        "pick_change_share": changes / (len(rows) - 1) if len(rows) > 1 else None,
        "chained_net_r_per_month": card["net_r"] / months if months else None,
        "scorecard": card,
        "rows": rows,
    }


def window_study(trades, chosen, start, end, mode):
    """Nine fixed lengths, saved trades only. Spec: research-runner.md > Walk-forward."""
    rows = []
    for train in (12, 24, 36):
        for test in (3, 6, 12):
            _, info = summarize_walk_forward(
                trades, chosen, start, end, mode, train_months=train, test_months=test
            )
            rows.append({key: info[key] for key in STUDY_COLUMNS})
    return rows


def from_saved(
    folder,
    variants,
    chosen,
    start,
    end,
    mode,
    train_years=None,
    *,
    train_months=24,
    test_months=6,
    step_months=None,
    study=False,
):
    """Read persisted runs in original variant order, including on resume."""
    trades = {v.id: read_trades(folder / "variants" / v.id) for v in variants}
    rows, info = summarize_walk_forward(
        trades,
        chosen,
        start,
        end,
        mode,
        train_years,
        train_months=train_months,
        test_months=test_months,
        step_months=step_months,
    )
    if study:
        info["study"] = window_study(trades, chosen, start, end, mode)
    return rows, info


def report(info):
    if info is None:
        return []
    lines = _month_report(info) if "windows" in info else _yearly_report(info)
    if "study" in info:
        lines += ["", "### Window length study", ""] + _table(STUDY_COLUMNS, info["study"])
    return lines


def _yearly_report(info):
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


def _cell(value) -> str:
    """Report cell: n/a for None, floats to 2 decimals, a midnight timestamp as its date."""
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.2f}"
    text = str(value)
    return text[:10] if text.endswith("T00:00:00+00:00") else text


def _table(columns, rows):
    return ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)] + [
        "| " + " | ".join(_cell(row[k]) for k in columns) + " |" for row in rows
    ]


def _month_report(info):
    lines = [
        "",
        "## Walk-forward",
        "",
        (
            f"Mode: {info['mode']}; train/test/step months: {info['train_months']}/"
            f"{info['test_months']}/{info['step_months']}; OOS windows: {info['windows']}."
        ),
        "Training uses only exits strictly before its end. Test entries keep later exits.",
        "WFE excludes nonpositive-training windows from both means; all windows enter the scorecard.",
        "",
    ]
    if not info["windows"]:
        lines += [info["reason"], ""]
    else:
        lines += _table(COLUMNS, info["rows"]) + [""]
    lines += _table(
        ("metric", "value"),
        [
            {"metric": key, "value": info[key]}
            for key in (
                "efficiency",
                "chained_net_r_per_month",
                "positive_window_share",
                "pick_changes",
                "pick_change_share",
            )
        ],
    )
    lines += ["", "Chained development OOS scorecard:", ""]
    lines += _table(
        ("metric", "value"),
        [{"metric": key, "value": value} for key, value in info["scorecard"].items()],
    )
    return lines
