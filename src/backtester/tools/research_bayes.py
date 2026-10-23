"""Saved-trade reporting. Spec: research-runner.md > Bayesian view."""

from backtester.analytics.bayes import BayesConfig, compare_posteriors, report, warning_flags
from backtester.tools.research_grid import families, family_variants, resolved_key


def calculate(folder, results_dir, spec, variants, chosen_id, tests, pairs, *, reader, config=None):
    cfg = config or BayesConfig()
    cache = {}

    def load(path):
        if path not in cache:
            try:
                cache[path] = report(reader(path), cfg)
            except (OSError, ValueError, KeyError) as exc:
                data = report([], cfg)
                reason = f"saved trades unavailable: {type(exc).__name__}"
                data["mean_r"]["reason"] = data["evidence"]["reason"] = reason
                cache[path] = data
        return cache[path]

    result = {"development": None, "tests": [], "twins": []}
    if chosen_id is not None:
        result["development"] = load(folder / "variants" / chosen_id)
    for test in tests:
        result["tests"].append(
            {
                "test_run": int(test["test_run"]),
                "variant_id": test["variant_id"],
                "run_folder": test["run_folder"],
                "report": load(results_dir / test["run_folder"]),
            }
        )
    comparing = [f for f in families(spec) if f.compare_to is not None]
    aliases = {}
    if comparing:
        retained = {resolved_key(spec, v): v.id for v in variants}
        aliases = {v.id: retained.get(resolved_key(spec, v)) for v in family_variants(spec)}
    for family in comparing:
        entries = []
        unmatched = 0
        for pair in pairs:
            if pair["family"] != family.name:
                continue
            if pair["status"] != "matched":
                unmatched += 1
                continue
            a_id, b_id = aliases[pair["twin_id"]], aliases[pair["variant_id"]]
            comparison = compare_posteriors(
                load(folder / "variants" / a_id),
                load(folder / "variants" / b_id),
                cfg,
            )
            entries.append(
                {
                    "a_id": pair["twin_id"],
                    "b_id": pair["variant_id"],
                    "a_saved_id": a_id,
                    "b_saved_id": b_id,
                    **comparison,
                }
            )
        summary = {
            "family": family.name,
            "compare_to": family.compare_to,
            "matched": len(entries),
            "unmatched": unmatched,
            "pairs": entries,
        }
        for key in ("p_mean_b_gt_a", "p_win_b_gt_a"):
            values = [e[key] for e in entries if e[key] is not None]
            summary[key] = sum(values) / len(values) if values else None
            summary[key + "_unavailable"] = len(entries) - len(values)
        result["twins"].append(summary)
    result["flags"] = warning_flags(result["development"], cfg) if chosen_id else []
    return result


def markdown(result):
    if result is None:
        return []

    def show(value):
        if value is None:
            return "n/a"
        if isinstance(value, list):
            return "[" + ", ".join(show(v) for v in value) + "]"
        return f"{value:.6g}"

    lines = [
        "",
        "## Bayesian view",
        "",
        "Prior edge:no-edge odds 1:50. Strong skeptical Beta is restricted above p* for BF.",
        "Normal-normal mean posterior treats sample variance as known; overlap adjusts mean-R n.",
        "p* is estimated from this list; these diagnostics do not correct for selection.",
    ]
    periods = [("development", result["development"])] + [
        (f"test {t['test_run']}", t["report"]) for t in result["tests"]
    ]
    for label, data in periods:
        lines += ["", f"### {label}", ""]
        if data is None:
            lines += ["n/a (no chosen variant)"]
            continue
        cfg = data["config"]
        lines += [
            (
                f"Raw n: {data['n']}; effective n: {show(data['effective_n'])}; "
                f"p*: {show(data['p_star'])}."
            ),
            (
                f"Mean prior: Normal(0, {cfg['mean_prior_sd']:g} R sd); "
                f"weak/strong strengths: {cfg['weak_strength']:g}/{cfg['strong_strength']:g}."
            ),
            "",
            "| Win-rate prior | Posterior mean | 95% interval | P(p > p*) |",
            "| --- | --- | --- | --- |",
        ]
        for name, posterior in data["win_rate"].items():
            lines.append(
                f"| {name} | {show(posterior['mean'])} | "
                f"{show(posterior['interval'])} | {show(posterior['p_above'])} |"
            )
        mean, evidence = data["mean_r"], data["evidence"]
        lines += [
            "",
            f"Mean R: {show(mean['mean'])}; 95% interval: {show(mean['interval'])}; "
            f"P(mean R > 0): {show(mean['p_positive'])}."
            + (f" {mean['reason']}." if mean["reason"] else ""),
            (
                f"BF(edge/no edge): {show(evidence['bayes_factor'])}; "
                f"log BF: {show(evidence.get('log_bayes_factor'))}; "
                f"posterior odds: {show(evidence['posterior_odds'])}:1; "
                f"log odds: {show(evidence.get('log_posterior_odds'))}."
            ),
            f"Trades needed (total, fixed-edge KL approximation) for {cfg['target_odds']:g}:1: "
            f"{show(evidence.get('trades_needed'))}; "
            f"additional: {show(evidence.get('additional_trades'))}."
            + (f" {evidence['reason']}." if evidence["reason"] else ""),
        ]
    if result["twins"]:
        lines += [
            "",
            (
                "Twin A/B uses independent posterior draws (seeded, 20,000 by default). "
                "Shared filter signals make this an approximation, not a paired causal test. "
                "Family probabilities average matched available pairs equally."
            ),
        ]
    for twin in result["twins"]:
        lines += [
            "",
            (
                f"Filter twins B={twin['family']}, A={twin['compare_to']}: "
                f"P(mean B > A)={show(twin['p_mean_b_gt_a'])}; "
                f"P(win B > A)={show(twin['p_win_b_gt_a'])}; "
                f"matched={twin['matched']}, unmatched={twin['unmatched']}; "
                f"unavailable mean/win pairs={twin['p_mean_b_gt_a_unavailable']}/"
                f"{twin['p_win_b_gt_a_unavailable']}."
            ),
        ]
        for pair in twin["pairs"]:
            lines.append(
                f"- B={pair['b_id']}, A={pair['a_id']}: "
                f"P(mean B > A)={show(pair['p_mean_b_gt_a'])}, "
                f"P(win B > A)={show(pair['p_win_b_gt_a'])} "
                f"({pair['draws']} draws, seed {pair['seed']})."
            )
    lines += ["", f"Flags: {', '.join(result['flags']) or 'none'}."]
    return lines
