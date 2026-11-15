"""Family budget ledger (Fable backlog FB-255, 2026-11-15): looks taken per family, the threshold in force and the
expected false passes, from `research/ledger.csv`. Rule (idea-harvest skill › Rules): |t| >= 3.0 up to 10 screened
ideas in a family, 3.5 up to 50, 4.0 above. A "look" = a ledger row past the card stage (screened, tested, ...);
harvest rows (HV-) and carded / rejected / parked rows are not looks. Expected false passes = cells x two-sided
p(|t| >= threshold) under no effect (normal approximation), cells = the row's numeric `cells` (1 if blank).
Run: .venv/Scripts/python.exe research/screens/family_budget.py [--md OUT]
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

LOOK_STAGES = {"screened", "dev_tested", "tested", "dev_passed", "falsified", "specced"}
P = {3.0: 2 * (1 - NormalDist().cdf(3.0)), 3.5: 2 * (1 - NormalDist().cdf(3.5)), 4.0: 2 * (1 - NormalDist().cdf(4.0))}


def threshold(looks):
    return 3.0 if looks <= 10 else 3.5 if looks <= 50 else 4.0


def cells(text):
    try:
        return max(1, int(float(text)))
    except ValueError:
        return 1


def main(argv):
    with open("research/ledger.csv", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    fam = defaultdict(lambda: {"looks": 0, "cells": 0, "passed": [], "ids": []})
    for r in rows:
        if r["id"].startswith("HV-") or r["stage"] not in LOOK_STAGES:
            continue
        f = fam[r["family"] or "(none)"]
        f["looks"] += 1
        f["cells"] += cells(r["cells"])
        f["ids"].append(r["id"])
        if "PASSED" in r["verdict"].upper() and "FAIL" not in r["verdict"].upper():
            f["passed"].append(r["id"])
    lines = ["| family | looks | cells | threshold now | expected false passes | passed | ids |", "|---|---|---|---|---|---|---|"]
    tot_cells, tot_fp = 0, 0.0
    for name, f in sorted(fam.items(), key=lambda kv: -kv[1]["looks"]):
        th = threshold(f["looks"])
        fp = f["cells"] * P[th]
        tot_cells += f["cells"]
        tot_fp += fp
        lines.append(f"| {name} | {f['looks']} | {f['cells']} | {th} | {fp:.3f} | {' '.join(f['passed']) or '-'} | "
                     f"{' '.join(f['ids'])} |")
    lines.append(f"| **all** | {sum(f['looks'] for f in fam.values())} | {tot_cells} | | {tot_fp:.2f} | | |")
    text = "\n".join(lines)
    print(text)
    if "--md" in argv:
        Path(argv[argv.index("--md") + 1]).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
