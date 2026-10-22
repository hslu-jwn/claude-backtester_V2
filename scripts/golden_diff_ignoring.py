"""Compare the committed golden lists (git HEAD) with the working-tree ones, ignoring named
fields that were added on purpose (e.g. a new TradeResult field with a neutral default).

    python scripts/golden_diff_ignoring.py risk_weight
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

GOLDEN = Path("tests/golden")


def main(ignore: list[str]) -> int:
    bad = 0
    for path in sorted(GOLDEN.glob("*.jsonl")):
        old = subprocess.run(
            ["git", "show", f"HEAD:{path.as_posix()}"], capture_output=True, text=True, check=True,
            encoding="utf-8",
        ).stdout.splitlines()  # fmt: skip
        new = path.read_text(encoding="utf-8").splitlines()
        diffs = 0
        for a, b in zip(old, new, strict=False):
            x, y = json.loads(a), json.loads(b)
            for key in ignore:
                y.pop(key, None)
                x.pop(key, None)
            diffs += x != y
        status = "identical" if diffs == 0 and len(old) == len(new) else "DIFFERENT"
        bad += status != "identical"
        print(f"{path.stem}: {status} ({len(old)} -> {len(new)} trades, {diffs} differing)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
