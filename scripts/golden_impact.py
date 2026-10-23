"""Net-R impact of a deliberate golden rewrite: committed (git HEAD) vs working-tree lists.

python scripts/golden_impact.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

GOLDEN = Path("tests/golden")


def _totals(lines: list[str]) -> tuple[int, float, float]:
    trades = [json.loads(line) for line in lines if line.strip()]
    return len(trades), sum(t["r_net"] for t in trades), sum(t["r_gross"] for t in trades)


def main() -> int:
    print(f"{'strategy':20} {'trades':>13} {'net R old':>10} {'net R new':>10} {'change':>8} "
          f"{'R/trade old':>11} {'new':>8}")  # fmt: skip
    for path in sorted(GOLDEN.glob("*.jsonl")):
        old = subprocess.run(
            ["git", "show", f"HEAD:{path.as_posix()}"], capture_output=True, text=True,
            check=True, encoding="utf-8",
        ).stdout.splitlines()  # fmt: skip
        n0, net0, _ = _totals(old)
        n1, net1, _ = _totals(path.read_text(encoding="utf-8").splitlines())
        print(f"{path.stem:20} {n0:>6}->{n1:<6} {net0:>10.1f} {net1:>10.1f} {net1 - net0:>+8.1f} "
              f"{net0 / max(n0, 1):>11.3f} {net1 / max(n1, 1):>8.3f}")  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
