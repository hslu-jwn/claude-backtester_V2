"""Declared development cells in result envelopes. Spec: research-intake.md > V2.6l."""

import csv
import json
from collections.abc import Callable
from pathlib import Path

from backtester.analytics.records import read_trades
from backtester.analytics.robustness import load_slippage_p90, stressed_net, stressed_net_p90
from backtester.engine.costs import CostConfig
from backtester.settings import from_dict


def _declared(folder: Path) -> list[str] | None:
    path = folder / "variants.csv"
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "variant_id" not in reader.fieldnames:
            raise ValueError("variants.csv lacks variant_id")
        ids = [row["variant_id"] for row in reader]
    if any(not ident or Path(ident).name != ident or ident in (".", "..") for ident in ids):
        raise ValueError("Invalid variant id")
    return sorted(ids)


def cell_manifest(folder: Path, costs_of: Callable[[dict], CostConfig] | None = None) -> list[dict]:
    """Return the declared development cells, including failed cells."""
    folder = Path(folder)
    result = []
    for ident in _declared(folder) or []:
        run = folder / "variants" / ident
        row = {"cell_id": ident, "parameters": None, "status": "FAILED"}
        row.update(
            dict.fromkeys(
                (
                    "trades",
                    "gross_mean_r",
                    "net_mean_r",
                    "gross_total_r",
                    "net_total_r",
                    "stop_rate",
                    "half_first_net_r",
                    "half_second_net_r",
                    "cost_stresses",
                )
            )
        )
        try:
            card = json.loads((run / "scorecard.json").read_text(encoding="utf-8"))
            row["parameters"] = card["overrides"]
            if not (run / "trades.csv").is_file():
                raise FileNotFoundError("trades.csv missing")
            with (run / "trades.csv").open(encoding="utf-8", newline="") as stream:
                columns = csv.DictReader(stream).fieldnames or []
                required = {
                    "id",
                    "symbol",
                    "direction",
                    "entry_time",
                    "entry_candle",
                    "entry",
                    "initial_stop",
                    "exit_time",
                    "exit_price",
                    "exit_reason",
                    "r_gross",
                    "r_net",
                }
                if not required.issubset(columns):
                    raise ValueError("trades.csv lacks required columns")
            trades = read_trades(run)
        except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
            row["reason"] = f"{type(exc).__name__}: {exc}"
            result.append(row)
            continue
        notes = []
        try:
            settings = json.loads((run / "settings.json").read_text(encoding="utf-8"))
            costs = costs_of(settings) if costs_of else from_dict(settings).engine.costs
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            costs = CostConfig()
            notes.append("Default CostConfig used: settings unavailable or unreadable.")
        n = len(trades)
        gross = sum(t.r_gross for t in trades)
        net = sum(t.r_net for t in trades)
        score = card.get("scorecard", {})

        def rounded(value):
            return round(value, 6) if value is not None else None

        row.update(
            status="COMPLETED",
            trades=n,
            gross_total_r=rounded(gross),
            net_total_r=rounded(net),
            gross_mean_r=rounded(gross / n) if n else None,
            net_mean_r=rounded(net / n) if n else None,
            stop_rate=rounded(sum(t.exit_reason == "stop_loss" for t in trades) / n) if n else None,
            half_first_net_r=rounded(score.get("half_first_net_r")),
            half_second_net_r=rounded(score.get("half_second_net_r")),
            cost_stresses={
                "factor_1.5": rounded(stressed_net(trades, 1.5)),
                "factor_2.0": rounded(stressed_net(trades, 2.0)),
                "fill_p90": rounded(stressed_net_p90(trades, load_slippage_p90(), costs)),
            },
        )
        if notes:
            row["notes"] = notes
        result.append(row)
    return result


def trial_accounting(folder: Path, info: dict, trial_log_count: int) -> dict:
    """Count declared cells and auxiliary sensitivity runs separately."""
    ids = _declared(Path(folder))
    sensitivity = Path(folder) / "sensitivity"
    return {
        "declared_cells": len(ids) if ids is not None else None,
        "sensitivity_runs": sum(p.is_dir() for p in sensitivity.iterdir())
        if sensitivity.is_dir()
        else 0,
        "trial_log_count": trial_log_count,
    }
