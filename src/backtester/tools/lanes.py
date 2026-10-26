"""Lanes: git worktrees next to V2 where a model builds one strategy in parallel.

    python -m backtester.tools.lanes create <name> [--existing]
    python -m backtester.tools.lanes list
    python -m backtester.tools.lanes check <name>
    python -m backtester.tools.lanes remove <name> [--force]

`create` runs `git worktree add <V2 parent>/bt-lane-<name> -b lane/<name>` from the current
commit and registers the lane in the git-ignored `lanes.json` in the V2 root (name, path,
branch, base commit, created). Data and results are not copied: lane jobs of the queue run with
`BACKTESTER_HOME` = the V2 root (`jobs/queue.py`). `check` lets a lane touch only its own
strategy (see `allowed`); everything else (shared code, `strategy/registry.py`) goes through
Opus. `remove` never deletes a branch.

Spec: research-runner.md > Lanes (ROADMAP V2.6 step 3).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from backtester.filelock import file_lock
from backtester.jobs.storage import atomic_json
from backtester.paths import HOME_DIR

REGISTRY_FILE = "lanes.json"
LANE_DIR_PREFIX = "bt-lane-"
BRANCH_PREFIX = "lane/"
NAME_PATTERN = re.compile(r"[a-z0-9_]+")
STRATEGY_DIR = Path("src") / "backtester" / "strategy"
GIT_TIMEOUT = 120


class LaneError(ValueError):
    """A lane command cannot go on; the message says why."""


def _root(root) -> Path:
    return Path(root if root is not None else HOME_DIR).resolve()


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    try:
        done = subprocess.run(
            ["git", *args], check=False, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
            timeout=GIT_TIMEOUT,
        )  # fmt: skip
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LaneError(f"git {args[0]} could not run: {error}") from error
    if check and done.returncode != 0:
        raise LaneError(
            f"git {' '.join(args[:2])} failed: {done.stderr.strip() or done.stdout.strip()}"
        )
    return done.stdout.strip() if check else str(done.returncode)


def _same(a: str | Path, b: str | Path) -> bool:
    return os.path.normcase(str(Path(a).resolve())) == os.path.normcase(str(Path(b).resolve()))


# --- registry ------------------------------------------------------------------------------


def _lock(root: Path):
    return file_lock(root / "results" / ".locks" / "lanes.lock")


def load(root=None) -> list[dict]:
    """The registered lanes (entries of `lanes.json`); empty when there is none."""
    path = _root(root) / REGISTRY_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        lanes = data["lanes"]
        return [e for e in lanes if isinstance(e, dict) and e.get("name") and e.get("path")]
    except FileNotFoundError:
        return []
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise LaneError(f"{REGISTRY_FILE} is unreadable: {error}") from error


def _save(root: Path, entries: list[dict]) -> None:
    atomic_json(root / REGISTRY_FILE, {"lanes": entries})


def find(name: str, root=None) -> dict:
    """The registry entry of lane `name`."""
    for entry in load(root):
        if entry["name"] == name:
            return entry
    raise LaneError(f"no lane {name!r} (see: lanes list)")


def resolve_cwd(cwd, root=None) -> str | None:
    """Working folder of a queue job: None for the V2 root (the default), else the path of a
    registered lane given by its name or its path. Any other folder raises `ValueError`."""
    if cwd is None or str(cwd) == "":
        return None
    home = _root(root)
    text = str(cwd)
    entries = load(home)
    for entry in entries:
        if NAME_PATTERN.fullmatch(text) and entry["name"] == text:
            return _lane_folder(entry)
    if _same(text, home):
        return None
    for entry in entries:
        if _same(text, entry["path"]):
            return _lane_folder(entry)
    raise ValueError(f"cwd {text!r} is neither the V2 root nor a registered lane")


def _lane_folder(entry: dict) -> str:
    path = Path(entry["path"])
    if not path.is_dir():
        raise ValueError(f"lane {entry['name']!r} has no folder {path}")
    return str(path.resolve())


# --- what a lane may touch -----------------------------------------------------------------


def allowed(name: str, rel: str) -> bool:
    """True if the repository-relative path `rel` (forward slashes) belongs to lane `name`:
    its strategy folder, its spec, its tests and its grid files."""
    n = re.escape(name)
    folders = (f"src/backtester/strategy/{name}/", f"tests/strategy/{name}/")
    return bool(
        rel.startswith(folders)
        or rel == f"docs/strategy-{name}.md"
        or re.fullmatch(rf"research/grids/{n}[^/]*\.toml", rel)
    )


def _changed(path: Path, base: str) -> list[str]:
    """Files changed against the base commit: committed, staged, edited and untracked."""
    diff = _git(path, "diff", "--name-only", "--no-renames", "-z", base)
    new = _git(path, "ls-files", "--others", "--exclude-standard", "-z")
    return sorted({p for p in (diff + "\0" + new).split("\0") if p})


def check(name: str, root=None) -> list[str]:
    """The files of lane `name` outside its allowed paths ([] = the lane passes)."""
    entry = find(name, root)
    path = Path(entry["path"])
    if not path.is_dir():
        raise LaneError(f"lane {name!r} has no folder {path}")
    return [f for f in _changed(path, entry["base_commit"]) if not allowed(name, f)]


# --- commands ------------------------------------------------------------------------------


def _validate(name: str) -> None:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
        raise LaneError(f"invalid lane name {name!r}: use only a-z, 0-9 and _")


def create(name: str, *, root=None, existing: bool = False) -> dict:
    """Create the worktree and branch of a lane and register it; returns the entry."""
    _validate(name)
    home = _root(root)
    if not existing and (home / STRATEGY_DIR / name).exists():
        raise LaneError(f"{name!r} is an existing strategy folder; use --existing to work on it")
    path = home.parent / f"{LANE_DIR_PREFIX}{name}"
    branch = f"{BRANCH_PREFIX}{name}"
    with _lock(home):
        entries = load(home)
        if any(e["name"] == name for e in entries):
            raise LaneError(f"lane {name!r} is already registered")
        if path.exists():
            raise LaneError(f"folder {path} exists")
        if (
            _git(home, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
            == "0"
        ):
            raise LaneError(f"branch {branch} already exists; remove it or pick another name")
        base = _git(home, "rev-parse", "HEAD")
        _git(home, "worktree", "add", str(path), "-b", branch)
        entry = {
            "name": name,
            "path": str(path.resolve()),
            "branch": branch,
            "base_commit": base,
            "created": datetime.now(UTC).isoformat(),
        }
        _save(home, [*entries, entry])
    return entry


def _dirty(path: Path) -> bool:
    return bool(_git(path, "status", "--porcelain", "-z"))


def _ahead_behind(home: Path, branch: str) -> tuple[int | None, int | None]:
    """(commits of the lane branch not in the V2 HEAD, commits of the V2 HEAD not in it)."""
    try:
        behind, ahead = _git(
            home, "rev-list", "--left-right", "--count", f"HEAD...{branch}"
        ).split()
    except (LaneError, ValueError):
        return None, None
    return int(ahead), int(behind)


def list_lanes(root=None) -> list[dict]:
    """One dict per lane: name, path, branch, ahead, behind (against the V2 HEAD), dirty,
    check_ok, offending (files outside the allowed paths), missing (no worktree folder)."""
    home = _root(root)
    rows = []
    for entry in load(home):
        path = Path(entry["path"])
        ahead, behind = _ahead_behind(home, entry["branch"])
        row = {
            **entry, "ahead": ahead, "behind": behind, "missing": not path.is_dir(),
            "dirty": None, "check_ok": None, "offending": [],
        }  # fmt: skip
        if not row["missing"]:
            row["dirty"] = _dirty(path)
            row["offending"] = check(entry["name"], home)
            row["check_ok"] = not row["offending"]
        rows.append(row)
    return rows


def remove(name: str, *, root=None, force: bool = False) -> None:
    """Remove the worktree and the registry entry of a lane. Refuses uncommitted changes or
    commits not in the V2 HEAD unless `force`; the branch is never deleted."""
    home = _root(root)
    with _lock(home):
        entry = find(name, home)
        path = Path(entry["path"])
        if not force:
            if path.is_dir() and _dirty(path):
                raise LaneError(f"lane {name!r} has uncommitted changes (--force removes them)")
            ahead, _ = _ahead_behind(home, entry["branch"])
            if ahead:
                raise LaneError(
                    f"lane {name!r}: branch {entry['branch']} has {ahead} unmerged commit(s) "
                    "(merge it, or --force removes the worktree and keeps the branch)"
                )
        if path.is_dir():
            _git(home, "worktree", "remove", *(["--force"] if force else []), str(path))
        else:
            _git(home, "worktree", "prune")
        _save(home, [e for e in load(home) if e["name"] != name])


# --- command line --------------------------------------------------------------------------


def _row_text(row: dict) -> str:
    if row["missing"]:
        state = "worktree folder missing"
    else:
        count = len(row["offending"])
        check_text = "ok" if row["check_ok"] else f"FAILED ({count} file(s))"
        state = f"dirty {'yes' if row['dirty'] else 'no'}; check {check_text}"
    return (
        f"{row['name']}  {row['path']}  {row['branch']}  "
        f"ahead {row['ahead']} behind {row['behind']}  {state}"
    )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m backtester.tools.lanes", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)  # fmt: skip
    sub = p.add_subparsers(dest="command", required=True)
    create_p = sub.add_parser("create")
    create_p.add_argument("name")
    create_p.add_argument("--existing", action="store_true",
                          help="allow the name of an existing strategy")  # fmt: skip
    sub.add_parser("list")
    sub.add_parser("check").add_argument("name")
    remove_p = sub.add_parser("remove")
    remove_p.add_argument("name")
    remove_p.add_argument("--force", action="store_true")
    return p


def main(argv: list[str] | None = None, *, root=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "create":
            entry = create(args.name, root=root, existing=args.existing)
            print(f"lane {entry['name']}: {entry['path']} on {entry['branch']}")
        elif args.command == "list":
            rows = list_lanes(root)
            print("\n".join(_row_text(r) for r in rows) if rows else "no lanes")
        elif args.command == "check":
            offending = check(args.name, root)
            if offending:
                print(f"lane {args.name}: files outside its allowed paths:", file=sys.stderr)
                print("\n".join(f"  {f}" for f in offending), file=sys.stderr)
                return 1
            print(f"lane {args.name}: ok")
        elif args.command == "remove":
            remove(args.name, root=root, force=args.force)
            print(f"lane {args.name} removed (the branch is kept)")
    except LaneError as error:
        print(f"lanes: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
