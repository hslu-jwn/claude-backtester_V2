"""Replay a saved run through FTMO rule sets; no backtest or random sampling.

Spec: risk-management.md > Challenge path simulator and FTMO rule sets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backtester.paths import RESULTS_DIR
from backtester.risk.challenge_path import RULE_SETS, simulate
from backtester.tools.monte_carlo import load_run


def _number(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def markdown(report: dict) -> str:
    lines = [
        "# Challenge paths",
        "",
        f"Period: {report['start']} to {report['end']}; risk: {report['risk']:.2%}.",
        "",
        (
            "Outcome percentages exclude open attempts. Instant has no pass target; "
            "funding time and cost per pass are n/a. Day indices in JSON are zero-based "
            "indices into dates; elapsed weekdays include the start day."
        ),
        "",
        (
            "| Rule set | Attempts | Pass % | Daily breach % | Max breach % | Open | "
            "Survived | Median weekdays to funding | p90 weekdays to funding |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in report["rules"].items():
        s = row["summary"]
        lines.append(
            f"| {name} | {s['attempts']} | {_number(s['pass_pct'])} | "
            f"{_number(s['daily_pct'])} | {_number(s['max_pct'])} | {s['open']} | "
            f"{s['survived']} | {_number(s['median_weekdays_to_funding'])} | "
            f"{_number(s['p90_weekdays_to_funding'])} |"
        )
    lines += [
        "",
        ("| Rule set | Fee input | Cost per funded before refund | Cost per funded after refund |"),
        "|---|---:|---:|---:|",
    ]
    for name, row in report["rules"].items():
        s = row["summary"]
        cost = s.get("cost_per_funded_before_refund", s.get("cost_per_funded"))
        after = s.get("cost_per_funded_after_refund", cost)
        lines.append(f"| {name} | {_number(s.get('fee'))} | {_number(cost)} | {_number(after)} |")
    lines += [
        "",
        (
            "Fees are not published in the spec and must be supplied as inputs. "
            "2-Step is refunded with the first reward; after refund is zero for passed accounts."
        ),
        "",
        (
            "Not modelled: news restrictions (2 minutes before/after) and holding through "
            "market breaks longer than 2 hours on funded and Instant accounts. "
            "The replay stops at funding for evaluation accounts. "
            "Equity uses the Monte Carlo worst-point approximation, not a candle equity replay."
        ),
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--risk", type=float, default=0.01)
    parser.add_argument("--rules", nargs="+", choices=tuple(RULE_SETS), default=list(RULE_SETS))
    parser.add_argument("--fee", nargs="+", action="extend", default=[], metavar="NAME=PRICE")
    parser.add_argument("--watch-days", type=int, default=126)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)
    try:
        fees = {}
        for item in args.fee:
            name, sep, value = item.partition("=")
            if not sep:
                raise ValueError("--fee must be NAME=PRICE")
            fees[name] = float(value)
        try:
            run = load_run(args.run_id, args.results_dir)
        except SystemExit as error:
            raise ValueError(str(error)) from None
        report = simulate(
            run["trades"], run["start"], run["end"], args.rules, args.risk, fees, args.watch_days
        )
        folder = args.results_dir / args.run_id
        (folder / "challenge_path.json").write_text(
            json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf8"
        )
        (folder / "challenge_path.md").write_text(markdown(report), encoding="utf8")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError) as error:
        parser.error(str(error))
    print(f"Wrote {folder / 'challenge_path.json'} and {folder / 'challenge_path.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
