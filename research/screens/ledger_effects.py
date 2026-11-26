"""R10 ledger effect columns (docs/research-runner.md › Ledger, lead review A file 10 › C): check and list est / se.

est = one effect per row in the predicted direction (positive = right sign), se its standard error, same unit.
Run: .venv/Scripts/python.exe research/screens/ledger_effects.py [check | add-columns | list]
"""

import csv
import sys
from pathlib import Path

LEDGER = Path("research/ledger.csv")
EFFECT_COLUMNS = ["est", "se", "est_unit", "est_basis", "est_sample", "type", "dup_group"]
BASES = {"gross", "net"}
SAMPLES = {
    "dev",
    "presample",
    "test",
    "forward",
    "expected",
}  # expected = pre-registered guess, no data look
TYPES = set(
    "abcdef"
)  # a forced flow, b published premium, c crypto breadth, d share anomaly, e price pattern, f original


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames or [], list(r)


def number(text):
    try:
        return float(text)
    except ValueError:
        return None


def check(path=LEDGER) -> list[str]:
    header, rows = read(path)
    missing = [c for c in EFFECT_COLUMNS if c not in header]
    if missing:
        return [f"missing column(s): {', '.join(missing)}"]
    errors = []
    for r in rows:
        i, est, se = r["id"], r["est"].strip(), r["se"].strip()
        if r["type"] and r["type"] not in TYPES:
            errors.append(f"{i}: type {r['type']!r} not in a-f")
        if not est and not se:
            continue
        if est and number(est) is None:
            errors.append(f"{i}: est {est!r} is not a number")
        elif not se or number(se) is None or number(se) <= 0:
            errors.append(f"{i}: se must be a number > 0 when est is set")
        elif r["est_basis"] not in BASES:
            errors.append(f"{i}: est_basis {r['est_basis']!r} not gross / net")
        elif r["est_sample"] not in SAMPLES:
            errors.append(f"{i}: est_sample {r['est_sample']!r} not in {sorted(SAMPLES)}")
        elif not r["est_unit"]:
            errors.append(f"{i}: est_unit missing")
    return errors


def t_values(path=LEDGER) -> dict[str, float]:
    _, rows = read(path)
    return {
        r["id"]: float(r["est"]) / float(r["se"])
        for r in rows
        if r["est"].strip() and r["se"].strip()
    }


def add_columns(path=LEDGER) -> None:
    header, rows = read(path)
    header += [c for c in EFFECT_COLUMNS if c not in header]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(argv):
    cmd = argv[0] if argv else "check"
    if cmd == "add-columns":
        add_columns()
    elif cmd == "list":
        _, rows = read(LEDGER)
        for r in rows:
            if r["est"].strip():
                print(
                    f"{r['id']:10} {r['type']} {r['est_sample']:9} {r['est_basis']:5} t {float(r['est']) / float(r['se']):+.2f}"
                )
    errors = check()
    print("\n".join(errors) or f"ok: {len(t_values())} rows with est / se")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
