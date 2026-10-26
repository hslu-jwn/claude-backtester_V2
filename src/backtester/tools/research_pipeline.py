"""Research pipeline per grid: one resumable command that fills a research card.

    python -m backtester.tools.research_pipeline research/grids/orb.toml

Steps (state per step in `results/research/<id>/pipeline.json`, a rerun skips done steps):

1. `research`     the research runner on the grid, development period only (`dev_only`, one
                  worker), never a retest. The runner already writes the profile / regime
                  breakdown (`profile.json`), parameter stability (`sensitivity.csv`, status in
                  `research.json`), significance, Bayes, monkeys, skill bounds, drawdown bounds
                  and the warning flags (`variants.csv`); none of that is computed again here.
2. `monte_carlo`  the Monte Carlo report of the chosen variant's development run with the
                  tool's own defaults, written to `results/monte_carlo/<dev run>/` (where
                  `ui/research_model.py` reads it). The only card input the runner does not write.
3. `card_inputs`  read-only check: which card input files exist, the stability status and the
                  chosen variant's flags, recorded in `pipeline.json` for the card.

The one-time MT5 test (`tools/research --retest`) is not part of the pipeline and has no option
here. Spec: research-runner.md > Pipeline (ROADMAP V2.6 step 3).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from backtester.filelock import file_lock
from backtester.jobs.storage import atomic_json
from backtester.paths import RESULTS_DIR

PIPELINE_FILE = "pipeline.json"
VERSION = 1
STEPS = ("research", "monte_carlo", "card_inputs")
PENDING, RUNNING, DONE, FAILED = "pending", "running", "done", "failed"
MONTE_CARLO_DIR = "monte_carlo"  # = ui/monte_carlo_job.MONTE_CARLO_DIR, read by research_model
RESEARCH_OK = ("dev_only", "no_test")  # outcomes of a development-only run
ERROR_MAX = 2000  # characters of an error text kept in pipeline.json
# card input files in the research folder (name -> file), as read by ui/research_model.py
FOLDER_INPUTS = {
    "profile": "profile.json",
    "significance": "significance.json",
    "bayes": "bayes.json",
    "skill_bounds": "skill_bounds.json",
    "monkeys": "monkeys.json",
    "sensitivity": "sensitivity.csv",
    "variants": "variants.csv",
}


class PipelineBusy(RuntimeError):
    """Another process is running the pipeline of this grid."""


def _now() -> str:
    return datetime.now(UTC).isoformat()


# --- folder and state ----------------------------------------------------------------------


def research_folder(grid: Path | str, results_dir: Path | str = RESULTS_DIR) -> Path:
    """The grid's research folder (the runner's `results/research/<grid id>`). Raises
    `research_grid.GridError` for a missing or invalid grid file."""
    from backtester.tools.research_grid import expand, grid_id, load_grid

    spec = load_grid(grid)
    variants, _, _ = expand(spec)
    return Path(results_dir) / "research" / grid_id(spec, variants)


def read_state(folder: Path | str) -> dict | None:
    """`pipeline.json` of a research folder; None when missing or unreadable."""
    try:
        data = json.loads((Path(folder) / PIPELINE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def progress(state: dict | None) -> str:
    """The text of the card: "queued", "step 2 of 3: monte_carlo", "done" or
    "failed: <step>: <error>". `state` None (no pipeline.json yet) is "queued"."""
    if not state or state.get("state") == PENDING:
        return "queued"
    steps = state.get("steps") or []
    if state.get("state") == DONE:
        return "done"
    if state.get("state") == FAILED:
        failed = next((s for s in steps if s.get("state") == FAILED), {})
        return f"failed: {failed.get('name', '?')}: {failed.get('error') or 'unknown error'}"
    names = [s.get("name") for s in steps]
    current = state.get("current")
    index = names.index(current) + 1 if current in names else 1
    return f"step {index} of {len(steps)}: {current}"


def _new_state(grid: Path, folder: Path) -> dict:
    return {
        "version": VERSION,
        "grid": str(grid),
        "id": folder.name,
        "created": _now(),
        "updated": _now(),
        "state": PENDING,
        "current": None,
        "steps": [
            {
                "name": name,
                "state": PENDING,
                "started": None,
                "ended": None,
                "error": None,
                "note": None,
            }
            for name in STEPS
        ],
        "chosen": None,
        "monte_carlo": None,
        "inputs": None,
    }


def _overall(state: dict) -> str:
    states = [s["state"] for s in state["steps"]]
    if any(s == FAILED for s in states):
        return FAILED
    if all(s == DONE for s in states):
        return DONE
    if any(s in (RUNNING, DONE) for s in states):
        return RUNNING
    return PENDING


# --- default step implementations ----------------------------------------------------------


def default_research(grid: Path, **kwargs) -> dict:
    from backtester.tools.research import run_research

    return run_research(grid, **kwargs)


def default_monte_carlo(dev_run: str, results_dir: Path, out: Path) -> dict:
    """The Monte Carlo tool's report of a run (`--run`), every setting at the tool's default.
    Returns what is recorded in pipeline.json (kind, runs, paths, seed)."""
    from backtester.tools import monte_carlo

    code = monte_carlo.main(
        ["--run", dev_run, "--results-dir", str(results_dir), "--out", str(out)]
    )
    if code:
        raise RuntimeError(f"monte_carlo exited with {code}")
    defaults = monte_carlo.ToolConfig()
    return {
        "kind": "monte_carlo --run (kinds A-D, tool defaults)",
        "runs": defaults.runs,
        "paths": defaults.paths,
        "seed": defaults.seed,
    }


# --- steps ---------------------------------------------------------------------------------


def _error_text(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"[:ERROR_MAX]


def _flags(folder: Path, chosen_id: str | None) -> list[str]:
    try:
        with (folder / "variants.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, ValueError, csv.Error):
        return []
    row = next((r for r in rows if r.get("variant_id") == chosen_id), {})
    return [f for f in str(row.get("flags") or "").split(";") if f]


def _card_inputs(folder: Path, results_dir: Path, state: dict) -> dict:
    """What the card has, read from files the runner and the Monte Carlo step wrote."""
    chosen = state.get("chosen") or {}
    present = [name for name, file in FOLDER_INPUTS.items() if (folder / file).is_file()]
    dev_run = chosen.get("dev_run")
    if dev_run and (results_dir / MONTE_CARLO_DIR / dev_run / "summary.json").is_file():
        present.append("monte_carlo")
    if dev_run and (results_dir / dev_run / "drawdown_bounds.json").is_file():
        present.append("drawdown_bounds")
    try:
        info = json.loads((folder / "research.json").read_text(encoding="utf-8"))
        sensitivity = (info.get("sensitivity") or {}).get("status")
    except (OSError, ValueError, AttributeError):
        sensitivity = None
    wanted = [*FOLDER_INPUTS, "monte_carlo", "drawdown_bounds"]
    return {
        "present": present,
        "missing": [n for n in wanted if n not in present],
        "stability": sensitivity,
        "flags": _flags(folder, chosen.get("id")),
    }


def _step_research(state, grid, folder, results_dir, fns, log):
    outcome = fns["research"](
        grid, results_dir=results_dir, workers=1, retest=False, dev_only=True, log=log
    )
    status = outcome.get("status")
    if status not in RESEARCH_OK:
        raise RuntimeError(f"research ended with status {status}: {outcome.get('message')}")
    chosen = outcome.get("chosen")
    state["chosen"] = (
        {"id": chosen["id"], "dev_run": chosen["dev_run"]} if chosen and chosen.get("id") else None
    )
    return outcome.get("message")


def _step_monte_carlo(state, grid, folder, results_dir, fns, log):
    chosen = state.get("chosen")
    if not chosen:
        return "no chosen variant: Monte Carlo not run"
    out = results_dir / MONTE_CARLO_DIR / chosen["dev_run"]
    if (out / "summary.json").is_file():
        return "summary already present (not computed again)"
    info = dict(fns["monte_carlo"](chosen["dev_run"], results_dir, out) or {})
    state["monte_carlo"] = {**info, "out": f"{MONTE_CARLO_DIR}/{chosen['dev_run']}"}
    return None


def _step_card_inputs(state, grid, folder, results_dir, fns, log):
    state["inputs"] = _card_inputs(folder, results_dir, state)
    missing = state["inputs"]["missing"]
    return f"missing: {', '.join(missing)}" if missing else None


STEP_FUNCTIONS = {
    "research": _step_research,
    "monte_carlo": _step_monte_carlo,
    "card_inputs": _step_card_inputs,
}


def run_pipeline(
    grid: Path | str,
    *,
    results_dir: Path | str = RESULTS_DIR,
    research_fn: Callable | None = None,
    monte_carlo_fn: Callable | None = None,
    log: Callable[..., None] = print,
) -> dict:
    """Run (or resume) the pipeline of a grid; returns the pipeline state (= pipeline.json).

    `research_fn(grid, results_dir=, workers=, retest=, dev_only=, log=)` returns the runner's
    outcome dict; `monte_carlo_fn(dev_run, results_dir, out)` returns a dict recorded in
    pipeline.json. Both default to the real tools. Raises `PipelineBusy` when another process
    runs this grid's pipeline, and `GridError` for a bad grid file."""
    grid, results_dir = Path(grid), Path(results_dir)
    folder = research_folder(grid, results_dir)
    fns = {
        "research": research_fn or default_research,
        "monte_carlo": monte_carlo_fn or default_monte_carlo,
    }
    try:
        lock = file_lock(results_dir / ".locks" / "pipeline" / f"{folder.name}.lock", timeout=0)
        lock.__enter__()
    except TimeoutError as exc:
        raise PipelineBusy(f"the pipeline of {folder.name} is already running") from exc
    try:
        state = read_state(folder)
        if not state or [s.get("name") for s in state.get("steps", [])] != list(STEPS):
            state = _new_state(grid, folder)

        def save() -> None:
            state["updated"] = _now()
            state["state"] = _overall(state)
            atomic_json(folder / PIPELINE_FILE, state)

        for step in state["steps"]:
            if step["state"] == DONE:
                log(f"pipeline: {step['name']} done before")
                continue
            step.update(state=RUNNING, started=_now(), ended=None, error=None, note=None)
            state["current"] = step["name"]
            save()
            log(f"pipeline: {step['name']}")
            try:
                step["note"] = STEP_FUNCTIONS[step["name"]](
                    state, grid, folder, results_dir, fns, log
                )
            except (Exception, KeyboardInterrupt, SystemExit) as error:
                step.update(state=FAILED, ended=_now(), error=_error_text(error))
                state["current"] = None
                save()
                log(f"pipeline: {step['name']} failed: {step['error']}")
                if isinstance(error, KeyboardInterrupt):
                    raise
                return state
            step.update(state=DONE, ended=_now())
            state["current"] = None
            save()
        save()
        return state
    finally:
        lock.__exit__(None, None, None)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m backtester.tools.research_pipeline", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )  # fmt: skip
    p.add_argument("grid", type=Path, help="research/grids/<name>.toml")
    p.add_argument("--results-dir", type=Path, default=RESULTS_DIR, help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    from backtester.tools.research import ResearchError
    from backtester.tools.research_grid import GridError

    args = parse_args(argv)
    try:
        state = run_pipeline(args.grid, results_dir=args.results_dir)
    except (GridError, ResearchError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except PipelineBusy as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"\npipeline {state['id']}: {progress(state)}")
    return 0 if state["state"] == DONE else 1


if __name__ == "__main__":
    raise SystemExit(main())
