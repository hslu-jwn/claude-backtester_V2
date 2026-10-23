"""The "Prop firm" card of a backtest's results page: pass probability and friends, computed
from the run's R trade list and cached in the run folder.

Spec: risk-management.md > Prop-firm field (where it shows) and > Monte Carlo (A. Day reshuffle,
FTMO 2-Step, daily loss approximation); ROADMAP 5.6. The numbers are kind A of the Monte Carlo
report (`risk/monte_carlo.py`, defaults: 1,000 reshuffles, seed 42, risk 0.5 / 1 / 1.5 %).

- `FIRMS` maps a firm id to its preset (label + Monte Carlo / challenge rules). FTMO 2-Step
  is the only one so far; another firm's rules plug in here (the page lists the dropdown).
- `compute_card` is pure; `ensure_card` reads / writes `<run folder>/prop_firm.json`. An entry is
  reused only while its key (card version, firm rules, card limits, the run's period and a hash
  of trades.csv) is unchanged; a missing or broken file is ignored and rewritten.
- A big run takes 20-30 s, so the page starts `python -m backtester.risk.prop_card <run id>`
  in the background (`ui/prop_card_job.py`).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from pathlib import Path

from backtester.analytics.records import read_trades
from backtester.paths import RESULTS_DIR
from backtester.risk.adaptive import AdaptiveRisk
from backtester.risk.monte_carlo import (
    MonteCarloConfig,
    build_days,
    ftmo_by_risk,
    reshuffle_orders,
    weekdays,
)

# 2: funded account risks on the initial balance (2026-10-20); 3: fixed and adaptive lines,
# average days to pass (ROADMAP 5.7); bump when the card's numbers or format change
# 4: B1-B3 decisions (2026-10-22): full passing days, unfinished share, entry-known risk
CARD_VERSION = 4
CACHE_FILE = "prop_firm.json"
DEFAULT_FIRM = "ftmo_2step"


@dataclass(frozen=True, slots=True)
class FirmPreset:
    label: str
    mc: MonteCarloConfig  # challenge rules + runs / seed / risk levels (fixed risk)
    # settings of the card's "adaptive" lines
    adaptive: AdaptiveRisk = field(default_factory=AdaptiveRisk)


@dataclass(frozen=True, slots=True)
class PropCardConfig:
    # Fewer than this and the numbers say nothing (accepted by the user 2026-10-20):
    # a challenge needs two phases of at least 4 trading days and the funded watch is 126 days
    min_trades: int = 100
    min_days: int = 120  # weekdays of the run's period (about 6 months)

    def __post_init__(self) -> None:
        if self.min_trades < 1 or self.min_days < 1:
            raise ValueError("min_trades and min_days must be >= 1")


FIRMS: dict[str, FirmPreset] = {
    DEFAULT_FIRM: FirmPreset("FTMO 2-Step", MonteCarloConfig(fan_paths=0)),
}
DEFAULT_CARD = PropCardConfig()


def too_few_reason(n_trades: int, n_days: int, card: PropCardConfig) -> str | None:
    reasons = []
    if n_trades < card.min_trades:
        reasons.append(f"{n_trades} trades (at least {card.min_trades} needed)")
    if n_days < card.min_days:
        reasons.append(f"{n_days} trading days (at least {card.min_days} needed)")
    if not reasons:
        return None
    return "Too little data for a meaningful estimate: " + " and ".join(reasons) + "."


def _row(risk: float, ftmo: dict) -> dict:
    observed = ftmo["funded_observed"]
    return {
        "risk": risk,
        "attempts": ftmo["attempts"],
        "unfinished_attempts": ftmo["unfinished_attempts"],
        "total_attempts": ftmo["total_attempts"],
        "unfinished_share": ftmo["unfinished_share"],
        "passes": ftmo["passes"],
        "pass_probability": ftmo["pass_probability"],
        "fail_daily": ftmo["fail_daily"],
        "fail_max": ftmo["fail_max"],
        "median_days_to_pass": ftmo["median_days_to_pass"],
        "average_days_to_pass": ftmo["average_days_to_pass"],
        "skipped_trades": ftmo["skipped_trades"],
        "trades_seen": ftmo["trades_seen"],
        "funded_observed": observed,
        "funded_lost_probability": ftmo["funded_lost_probability"] if observed else None,
    }


def compute_card(
    trades, start: date, end: date, preset: FirmPreset, card: PropCardConfig = DEFAULT_CARD
) -> dict:
    """The card of a trade list (anything with `entry_time`, `exit_time`, `r_net`) over the
    run's period: {"status": "ok", "rows": [...]} or {"status": "too_few", "reason": ...}."""
    trades = list(trades)
    n_days = len(weekdays(start, end))
    base = {"version": CARD_VERSION, "label": preset.label, "trades": len(trades), "days": n_days}
    reason = too_few_reason(len(trades), n_days, card)
    if reason:
        return {**base, "status": "too_few", "reason": reason}
    # the same reshuffled day orders for the fixed and the adaptive lines; only the FTMO
    # simulation runs (the card needs no account statistics)
    days = build_days(trades, start, end)
    orders = reshuffle_orders(len(days), preset.mc)
    fixed = ftmo_by_risk(days, orders, replace(preset.mc, adaptive=None))
    adaptive = ftmo_by_risk(days, orders, replace(preset.mc, adaptive=preset.adaptive))
    return {
        **base,
        "status": "ok",
        "runs": preset.mc.runs,
        "seed": preset.mc.seed,
        "funded_days": preset.mc.funded_days,
        "rows": [_row(risk, ftmo) for risk, ftmo in fixed.items()],
        "adaptive": {"floor": preset.adaptive.floor, "daily_budget": preset.adaptive.daily_budget},
        "adaptive_rows": [_row(risk, ftmo) for risk, ftmo in adaptive.items()],
    }


# ----- cache -------------------------------------------------------------------------------


def _read_summary_period(folder: Path) -> tuple[date, date]:
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    return date.fromisoformat(summary["start"]), date.fromisoformat(summary["end"])


def cache_key(folder: Path, firm: str, preset: FirmPreset, card: PropCardConfig) -> str:
    start, end = _read_summary_period(folder)
    trades_hash = hashlib.sha256((folder / "trades.csv").read_bytes()).hexdigest()
    payload = {
        "v": CARD_VERSION, "firm": firm, "preset": asdict(preset), "card": asdict(card),
        "start": start.isoformat(), "end": end.isoformat(), "trades": trades_hash,
    }  # fmt: skip
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _entries(folder: Path) -> dict:
    try:
        data = json.loads((folder / CACHE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = data.get("entries") if isinstance(data, dict) else None
    return entries if isinstance(entries, dict) else {}


def _resolve(firm: str, preset: FirmPreset | None, card: PropCardConfig | None):
    return preset or FIRMS[firm], card or DEFAULT_CARD  # KeyError for an unknown firm


def cached_card(
    folder: Path, firm: str = DEFAULT_FIRM, preset: FirmPreset | None = None,
    card: PropCardConfig | None = None,
) -> dict | None:  # fmt: skip
    """The stored card when its key still matches, else None (no file, broken file, changed
    settings or trades)."""
    preset, card = _resolve(firm, preset, card)
    folder = Path(folder)
    entry = _entries(folder).get(firm)
    if not isinstance(entry, dict) or not isinstance(entry.get("card"), dict):
        return None
    try:
        key = cache_key(folder, firm, preset, card)
    except (OSError, ValueError, KeyError):
        return None
    return entry["card"] if entry.get("key") == key else None


def ensure_card(
    folder: Path, firm: str = DEFAULT_FIRM, preset: FirmPreset | None = None,
    card: PropCardConfig | None = None,
) -> dict:  # fmt: skip
    """The card of a run folder: from the cache, else computed and written."""
    preset, card = _resolve(firm, preset, card)
    folder = Path(folder)
    found = cached_card(folder, firm, preset, card)
    if found is not None:
        return found
    start, end = _read_summary_period(folder)
    result = compute_card(read_trades(folder), start, end, preset, card)
    entries = _entries(folder)
    entries[firm] = {"key": cache_key(folder, firm, preset, card), "card": result}
    tmp = folder / (CACHE_FILE + ".tmp")
    tmp.write_text(json.dumps({"entries": entries}, indent=1), encoding="utf-8")
    os.replace(tmp, folder / CACHE_FILE)
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m backtester.risk.prop_card", description=__doc__)
    p.add_argument("run_id")
    p.add_argument("--firm", default=DEFAULT_FIRM, choices=tuple(FIRMS))
    p.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = p.parse_args(argv)
    folder = args.results_dir / args.run_id
    if not (folder / "trades.csv").is_file() or not (folder / "summary.json").is_file():
        print(f"no run folder {folder}")
        return 1
    result = ensure_card(folder, args.firm)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
