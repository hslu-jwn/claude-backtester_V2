"""Development-only diagnostics. Spec: research-runner.md > Parameter sensitivity, Filter twins."""

import hashlib
import json
import math
from dataclasses import dataclass

from backtester.tools.research_grid import (
    GridError,
    GridSpec,
    Variant,
    families,
    family_variants,
    resolved_key,
    resolved_values,
    variant_settings,
)


@dataclass(frozen=True, slots=True)
class SensitivityConfig:
    changes: tuple[float, ...] = (-0.20, -0.10, 0.10, 0.20)
    minimum_share: float = 0.50


def neighbours(spec: GridSpec, chosen: Variant) -> list[dict]:
    """Requested neighbours including named config rejections; duplicate IDs reuse runs."""
    family = next(f for f in families(spec) if f.name == chosen.family)
    values = resolved_values(spec, chosen)
    rows = []
    for setting in family.grid:
        original = values[setting]
        if isinstance(original, bool) or not isinstance(original, int | float):
            continue
        for change in SensitivityConfig().changes:
            value = original * (1 + change)
            if isinstance(original, int):
                value = math.copysign(math.floor(abs(value) + 0.5), value)
                direction = 1 if change > 0 else -1
                if value == original:
                    value = original + direction * (-1 if original < 0 else 1)
                value = int(value)
            overrides = {**chosen.overrides, setting: value}
            digest = hashlib.sha256(
                json.dumps([chosen.id, setting, value], sort_keys=True).encode()
            ).hexdigest()[:16]
            row = {
                "id": f"{chosen.id}-{digest}",
                "setting": setting,
                "change": change,
                "value": value,
                "status": "pending",
                "reason": "",
                "overrides": overrides,
            }
            try:
                variant_settings(spec, Variant(row["id"], f"{setting}={value}", overrides))
            except GridError as exc:
                row.update(status="skipped", reason=str(exc))
            rows.append(row)
    return rows


def sensitivity_summary(rows: list[dict], chosen_net_r: float) -> dict:
    failed = sorted(
        {
            r["setting"]
            for r in rows
            if r["status"] != "done"
            or chosen_net_r <= 0
            or r["net_r"] <= 0
            or r["net_r_share"] < SensitivityConfig().minimum_share
        }
    )
    return {
        "status": "gentle" if rows and not failed else "sharp",
        "failed_settings": failed,
        "rows": len(rows),
    }


def twin_rows(spec: GridSpec, variants: list[Variant], rows: list[dict]) -> tuple[list, list]:
    """Match full family occurrences to available runs, including resolved duplicates."""
    if not any(f.compare_to for f in families(spec)):
        return [], []
    by_id = {r["variant_id"]: r for r in rows}
    available = {resolved_key(spec, v): by_id[v.id] for v in variants if v.id in by_id}
    occurrences = list(family_variants(spec))
    values = {v.id: resolved_values(spec, v) for v in occurrences}
    cards = {v.id: available.get(resolved_key(spec, v)) for v in occurrences}
    pairs, summaries = [], []
    for family in families(spec):
        if family.compare_to is None:
            continue

        def key(v, excluded=family.base):
            return json.dumps(
                {k: val for k, val in values[v.id].items() if k not in excluded},
                sort_keys=True,
                default=str,
            )

        targets = {}
        for v in occurrences:
            if v.family == family.compare_to:
                targets.setdefault(key(v), v)
        matched = []
        for v in occurrences:
            if v.family != family.name:
                continue
            twin = targets.get(key(v))
            card, other = cards[v.id], cards[twin.id] if twin else None
            pair = {"family": family.name, "variant_id": v.id, "twin_id": "", "status": "unmatched"}
            if card is not None and other is not None:
                pair.update(
                    twin_id=twin.id,
                    status="matched",
                    net_r=card["net_r"],
                    twin_net_r=other["net_r"],
                    difference=card["net_r"] - other["net_r"],
                    trades=card["trades"],
                    twin_trades=other["trades"],
                )
                matched.append(pair)
            pairs.append(pair)
        mean = sum(p["net_r"] for p in matched) / len(matched) if matched else None
        other_mean = sum(p["twin_net_r"] for p in matched) / len(matched) if matched else None
        summaries.append(
            {
                "family": family.name,
                "compare_to": family.compare_to,
                "matched": len(matched),
                "mean_net_r": mean,
                "mean_twin_net_r": other_mean,
                "lifts_average": ("yes" if mean > other_mean else "no") if matched else None,
            }
        )
    return pairs, summaries


def haircut(avg_r: float | None, bounds: tuple[float, float]) -> str:
    """Expectation multiplication factors, including negative/absent period averages."""
    low, high = bounds
    if avg_r is None:
        values = "n/a"
    elif avg_r <= 0:  # a haircut would make a loss look smaller
        values = "no positive edge to discount"
    else:
        values = f"{avg_r * low:.3f} to {avg_r * high:.3f} R per trade"
    return (
        f"Live expectation: {low * 100:g}-{high * 100:g} % of the backtest's average R "
        f"per trade = {values}"
    )
