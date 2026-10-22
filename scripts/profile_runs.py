"""Profile real backtests in-process (workers=1): where does a research sweep spend its time?

    python scripts/profile_runs.py > results/profile/summary.txt

Writes one cProfile file per strategy to results/profile/<name>.prof and prints the top
functions by cumulative and by own time. Nothing is written to the trial log.
"""

from __future__ import annotations

import cProfile
import io
import pstats
import time
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config

RUNS = (  # (strategy, symbols): one research-typical symbol set each
    ("opening_range", ["US500", "NAS100"]),
    ("ny_index_sweep", ["NAS100"]),
    ("session_zone_sweep", ["XAUUSD"]),
)
START, END = date(2019, 1, 1), date(2021, 9, 13)  # development period (data split 2021-09-14)
OUT = Path("results/profile")
TOP = 25


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, symbols in RUNS:
        settings = replace(RunSettings(), strategy=default_config(name))
        prof = cProfile.Profile()
        t0 = time.perf_counter()
        prof.enable()
        result = run_backtests(symbols, START, END, settings, workers=1)
        prof.disable()
        seconds = time.perf_counter() - t0
        prof.dump_stats(OUT / f"{name}.prof")
        print(f"===== {name} {symbols}: {len(result.trades)} trades, {seconds:.1f} s")
        for key in ("cumulative", "tottime"):
            buf = io.StringIO()
            pstats.Stats(prof, stream=buf).sort_stats(key).print_stats(TOP)
            lines = [ln for ln in buf.getvalue().splitlines() if ln.strip()]
            start = next(i for i, ln in enumerate(lines) if ln.lstrip().startswith("ncalls"))
            print(f"--- by {key}")
            print("\n".join(lines[start : start + TOP + 1]))
        print(flush=True)


if __name__ == "__main__":
    main()
