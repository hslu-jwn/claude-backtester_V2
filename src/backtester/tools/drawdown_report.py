"""Bounds IO and report text. Spec: risk-management.md > Monte Carlo report."""

import csv
import json

import numpy as np

from backtester.analytics.daily import daily_net_r, weekdays
from backtester.risk.drawdown_bounds import drawdown_bounds


def calculate(trades, start, end, folder=None, config=None) -> dict:
    """Prefer the complete saved MTM series; otherwise use exit-booked daily R."""
    values, source = None, "exit_booked"
    path = folder / "daily.csv" if folder is not None else None
    if path is not None and path.is_file():
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames or []
            column = "net_r_mtm" if "net_r_mtm" in fields else "net_r_exit_booked"
            if column not in fields:
                raise ValueError("daily.csv needs net_r_mtm or net_r_exit_booked")
            rows = list(reader)
            if [r.get("date") for r in rows] != [d.isoformat() for d in weekdays(start, end)]:
                raise ValueError("daily.csv dates must match the complete run period in order")
            try:
                values = np.array([float(r[column]) for r in rows])
            except (TypeError, ValueError):
                raise ValueError("daily.csv R values must be numeric and complete") from None
            if not np.isfinite(values).all():
                raise ValueError("daily.csv R values must be finite")
            source = "marked_to_market" if column == "net_r_mtm" else "exit_booked"
    if values is None:
        values = daily_net_r(trades, start, end)
    return {
        **drawdown_bounds(values, config),
        "source": source,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


def write(result, folder) -> None:
    """Atomic saved result; do not cache across changed input series/configuration."""
    path = folder / "drawdown_bounds.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def markdown(result, label="") -> list[str]:
    cfg = result["config"]
    lines = [
        "",
        f"## Double-bootstrap {label}".rstrip(),
        "",
        (
            f"{result['source']}; {result['days']} historic days; horizon {cfg['horizon_days']} days; "
            f"outer={cfg['outer']}, inner={cfg['inner']}, block_days={cfg['block_days']}, "
            f"seed={cfg['seed']}. Fixed-fraction bounds (no compounding)."
        ),
        "",
        "| DD quantile | Units | Median | 90% upper | 95% upper |",
        "|---|---|---|---|---|",
    ]
    for row in result["rows"]:
        for unit, values in [
            ("R", row["bounds_r"]),
            *((f"% balance at {float(r) * 100:g}% risk", v) for r, v in row["bounds_pct"].items()),
        ]:
            lines.append(
                f"| {row['q']:.0%} | {unit} | "
                + " | ".join(f"{v:.3f}" for v in values.values())
                + " |"
            )
    if result["status"] != "ok":
        lines += ["", result["reason"]]
    return lines
