"""Saved-development significance. Spec: research-runner.md > Significance of the best variant."""

from dataclasses import dataclass, field

from backtester.analytics.best_of_n import RealityCheckConfig, reality_check
from backtester.analytics.effective_n import effective_trials, trade_uniqueness
from backtester.analytics.pbo import PBOConfig, cscv_pbo
from backtester.analytics.records import read_trades
from backtester.analytics.trial_log import TrialRecord, series_matrix


@dataclass(frozen=True)
class SignificanceConfig:
    reality_check: RealityCheckConfig = field(default_factory=RealityCheckConfig)
    pbo: PBOConfig = field(default_factory=PBOConfig)
    rc_threshold: float = 0.05
    pbo_threshold: float = 0.5

    def __post_init__(self):
        if not 0 <= self.rc_threshold <= 1 or not 0 <= self.pbo_threshold <= 1:
            raise ValueError("significance thresholds must be in [0, 1]")


def warning_flags(rc, pbo, config: SignificanceConfig | None = None) -> list[str]:
    cfg = config or SignificanceConfig()
    flags = []
    if rc.get("p_value") is not None and rc["p_value"] > cfg.rc_threshold:
        flags.append("rc_not_significant")
    if pbo.get("pbo") is not None and pbo["pbo"] >= cfg.pbo_threshold:
        flags.append("pbo_high")
    return flags


def calculate(
    folder, variant_ids, chosen_id, *, reader=read_trades, config: SignificanceConfig | None = None
) -> dict:
    """Read exactly the grid folders, never a trial family or sensitivity/test folders.

    Synthetic records use the existing series reader without writing trial-log lines.
    Relative series paths are rooted here, allowing arbitrary --results-dir locations.
    """
    cfg = config or SignificanceConfig()
    result = {"series_kind": "net_r_mtm", "variant_ids": list(variant_ids), "chosen_id": chosen_id}
    records = [
        TrialRecord("", "", {}, [], "", "", "", "", series=f"variants/{vid}/daily.csv")
        for vid in variant_ids
    ]
    try:
        dates, matrix = series_matrix(records, "net_r_mtm", folder)
    except (OSError, ValueError, KeyError) as exc:
        reason = f"development MTM series unavailable: {type(exc).__name__}"
        result.update(
            days=None,
            reality_check={"p_value": None, "reason": reason},
            pbo={"pbo": None, "median_oos_rank": None, "reason": reason},
            effective_trials={"n": len(variant_ids), "n_eff": None, "reason": reason},
        )
    else:
        result.update(
            days=len(dates),
            reality_check=reality_check(matrix, cfg.reality_check),
            pbo=cscv_pbo(matrix, cfg.pbo),
            effective_trials=effective_trials(matrix),
        )
    result["effective_trades"] = {"effective_trades": None, "reason": "no chosen variant"}
    if chosen_id is not None:
        try:
            result["effective_trades"] = trade_uniqueness(reader(folder / "variants" / chosen_id))
        except (OSError, ValueError, KeyError) as exc:
            result["effective_trades"] = {
                "effective_trades": None,
                "reason": f"saved trade intervals unavailable: {type(exc).__name__}",
            }
    result["flags"] = warning_flags(result["reality_check"], result["pbo"], cfg)
    return result


def markdown(result) -> list[str]:
    if result is None:
        return []

    def show(data, key):
        value = data.get(key)
        return f"{value:.6g}" if value is not None else f"n/a ({data.get('reason', 'unavailable')})"

    rc, pbo = result["reality_check"], result["pbo"]
    trials, trades = result["effective_trials"], result["effective_trades"]
    return [
        "",
        "## Is the best variant better than luck?",
        "",
        "Development marked-to-market daily R; sensitivity neighbours and tests excluded.",
        f"- Reality Check p-value: {show(rc, 'p_value')}",
        f"- PBO: {show(pbo, 'pbo')}; median relative OOS rank: {show(pbo, 'median_oos_rank')}",
        f"- N: {trials['n']}; N_eff: {show(trials, 'n_eff')} (DSR N unchanged)",
        (
            f"- Effective trades of chosen variant: {show(trades, 'effective_trades')}; "
            f"average uniqueness: {show(trades, 'average_uniqueness')}"
        ),
        f"- Flags: {', '.join(result['flags']) or 'none'}",
    ]
