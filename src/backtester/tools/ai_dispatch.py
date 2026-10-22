"""Call Codex or Gemini (Antigravity CLI) non-interactively for one task. Spec: AGENTS.md › Team.

    python -m backtester.tools.ai_dispatch codex  --effort medium --brief briefs/x.md
    python -m backtester.tools.ai_dispatch gemini --effort high --write --prompt "Write tests ..."

Opus is the only dispatcher. Every call:
- prepends the shared limits (AGENTS.md, never commit / push, no credentials, no live/ code),
- runs with secrets removed from the environment,
- checks the repo afterwards (no commit, no branch switch, no protected path touched) and
  exits 3 on a violation, 4 when the tool reports a usage limit,
- writes the answer to results/ai/<time>_<tool>.md and logs the call to results/ai_calls.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

EXIT_VIOLATION = 3
EXIT_LIMIT = 4


@dataclass(frozen=True)
class DispatchConfig:
    codex_model: str = "gpt-6.1-sol"
    gemini_models: Mapping[str, str] = field(
        default_factory=lambda: {
            "low": "gemini-3.8-flash-low",
            "medium": "gemini-3.8-flash-medium",
            "high": "gemini-3.8-flash-high",
        }
    )
    codex_efforts: tuple[str, ...] = ("low", "medium", "high", "xhigh")
    protected: tuple[str, ...] = ("src/backtester/live/", ".env")  # models never write here
    secret_env: str = (
        r"TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|CREDENTIAL|ACCESS_KEY|PRIVATE_KEY"
    )
    limit_patterns: str = r"usage limit|rate limit|quota exceeded|resource_exhausted|\b429\b"
    timeout_s: int = 3600
    agy_fallback: str = (
        r"~\AppData\Local\Microsoft\WinGet\Packages"
        r"\Google.AntigravityCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\agy.exe"
    )


DEFAULT = DispatchConfig()


@dataclass(frozen=True)
class Task:
    tool: str  # "codex" | "gemini"
    prompt: str
    effort: str = "medium"
    write: bool = False  # may edit files (still never commit)
    cwd: str = "."
    model: str | None = None


@dataclass(frozen=True)
class RepoState:
    head: str
    branch: str
    dirty: frozenset[str]
    refs: frozenset[str] = frozenset()  # "<sha> <ref>" for every branch, tag and remote ref
    reflog: int = 0  # HEAD reflog entries: a commit undone by a reset still adds some


def prompt_for(task: Task, cfg: DispatchConfig) -> str:
    access = "You may edit files in the workspace." if task.write else "Read only: change no files."
    limits = (
        "Follow AGENTS.md (the project rules) exactly. "
        f"{access} Hard limits: never commit, never push, never create branches; "
        "never read, print or ask for credentials (passwords, tokens, keys); "
        f"never edit {', '.join(cfg.protected)}. "
        "If a trading rule is unclear, stop and say so instead of guessing. "
        "End with a short report: what you did, files changed, test results, open questions."
    )
    return f"{limits}\n\nTASK:\n{task.prompt}"


def _effort(task: Task, allowed) -> str:
    if task.effort not in allowed:
        raise ValueError(f"effort {task.effort!r} not in {list(allowed)}")
    return task.effort


def build_codex_cmd(exe: str, task: Task, cfg: DispatchConfig, out_file: str) -> list[str]:
    effort = _effort(task, cfg.codex_efforts)
    return [
        exe, "exec",
        "-C", task.cwd,
        "-s", "workspace-write" if task.write else "read-only",
        "-m", task.model or cfg.codex_model,
        "-c", f'model_reasoning_effort="{effort}"',
        "--color", "never",
        "-o", out_file,
        "-",
    ]  # fmt: skip


def build_agy_cmd(exe: str, task: Task, cfg: DispatchConfig) -> list[str]:
    model = task.model or cfg.gemini_models[_effort(task, cfg.gemini_models)]
    cmd = [exe, "--model", model, "--sandbox", "--output-format", "text"]
    if task.write:
        cmd.append("--dangerously-skip-permissions")  # tools run inside --sandbox
    return [*cmd, "-p", prompt_for(task, cfg)]


def child_env(env: Mapping[str, str], cfg: DispatchConfig = DEFAULT) -> dict[str, str]:
    secret = re.compile(cfg.secret_env, re.IGNORECASE)
    kept = {k: v for k, v in env.items() if not secret.search(k)}
    kept["NODE_OPTIONS"] = "--use-system-ca"  # this PC intercepts TLS; Node must use Windows CAs
    return kept


def guard_violations(
    before: RepoState, after: RepoState, cfg: DispatchConfig, *, write: bool
) -> list[str]:
    found = []
    if after.head != before.head:
        found.append(f"commit made: HEAD {before.head[:8]} -> {after.head[:8]}")
    if after.branch != before.branch:
        found.append(f"branch switched: {before.branch} -> {after.branch}")
    if after.reflog != before.reflog:
        found.append(f"HEAD moved during the run (reflog {before.reflog} -> {after.reflog})")
    for ref in sorted(after.refs ^ before.refs):
        found.append(f"ref created, moved or deleted (commit / branch / push): {ref}")
    protected = tuple(p.lower() for p in cfg.protected)
    for path in sorted(after.dirty - before.dirty):
        if not write:
            found.append(f"read-only task changed: {path}")
        elif path.lower().startswith(protected):  # Windows paths ignore case
            found.append(f"protected path changed: {path}")
    return found


def hit_limit(text: str, cfg: DispatchConfig = DEFAULT) -> bool:
    return re.search(cfg.limit_patterns, text, re.IGNORECASE) is not None


# --- running -------------------------------------------------------------------------------


def parse_porcelain_z(z: str) -> frozenset[str]:
    """Paths from `git status --porcelain -z` ("XY path" records; a rename or copy is followed
    by its source path, which is skipped)."""
    paths, records = [], iter(z.split("\0"))
    for record in records:
        if len(record) < 4:
            continue
        paths.append(record[3:])
        if record[0] in "RC":
            next(records, None)
    return frozenset(paths)


def _git(cwd: str, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True
    )
    return out.stdout


def repo_state(cwd: str) -> RepoState:
    return RepoState(
        head=_git(cwd, "rev-parse", "HEAD").strip(),
        branch=_git(cwd, "branch", "--show-current").strip(),
        dirty=parse_porcelain_z(_git(cwd, "status", "--porcelain", "-z", "--untracked-files=all")),
        refs=frozenset(_git(cwd, "for-each-ref", "--format=%(objectname) %(refname)").split("\n"))
        - {""},
        reflog=len(_git(cwd, "reflog", "--format=%H").splitlines()),
    )


def _fresh_path(path: str) -> str:
    """PATH plus the machine and user PATH saved in the registry now: a process started before
    Node / the CLIs were installed (e.g. a long research loop) still finds them."""
    if sys.platform != "win32":
        return path
    import winreg

    saved = []
    for hive, key in (
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                saved.append(os.path.expandvars(winreg.QueryValueEx(k, "Path")[0]))
        except OSError:
            continue
    parts = [p for p in os.pathsep.join([path, *saved]).split(os.pathsep) if p]
    return os.pathsep.join(dict.fromkeys(parts))


def _exe(tool: str, cfg: DispatchConfig) -> str:
    if tool == "codex":
        found = shutil.which("codex.cmd") or shutil.which("codex")
        fallback = Path(os.environ.get("APPDATA", "")) / "npm" / "codex.cmd"
    else:
        found = shutil.which("agy")
        fallback = Path(cfg.agy_fallback).expanduser()
    if found:
        return found
    if fallback.exists():
        return str(fallback)
    raise FileNotFoundError(f"{tool} CLI not found")


def run(task: Task, cfg: DispatchConfig, results: Path, label: str) -> int:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = results / "ai" / f"{stamp}_{task.tool}_{label}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    exe = _exe(task.tool, cfg)
    if task.tool == "codex":
        cmd, stdin = build_codex_cmd(exe, task, cfg, str(out)), prompt_for(task, cfg)
    else:
        cmd, stdin = build_agy_cmd(exe, task, cfg), None
    env = child_env(os.environ, cfg)
    env["PATH"] = _fresh_path(env.get("PATH", ""))
    before = repo_state(task.cwd)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, check=False, input=stdin, cwd=task.cwd, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=cfg.timeout_s,
        )  # fmt: skip
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, code = str(e.stdout or ""), f"timeout after {cfg.timeout_s}s", 124
    seconds = round(time.monotonic() - start)
    if task.tool != "codex" or not out.exists():
        out.write_text(stdout, encoding="utf-8")
    violations = guard_violations(before, repo_state(task.cwd), cfg, write=task.write)
    limited = code != 0 and hit_limit(stdout + stderr, cfg)
    status = "violation" if violations else "limit" if limited else "ok" if code == 0 else "error"
    entry = {
        "time": stamp, "tool": task.tool, "label": label, "model": cmd[cmd.index(
            "-m" if task.tool == "codex" else "--model") + 1], "effort": task.effort,
        "write": task.write, "seconds": seconds, "exit": code, "status": status,
        "violations": violations, "answer": str(out),
    }  # fmt: skip
    with (results / "ai_calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry) + "\n")
    print(json.dumps(entry, indent=1))
    if code != 0:
        print(stderr[-2000:], file=sys.stderr)
    if violations:
        return EXIT_VIOLATION
    if limited:
        return EXIT_LIMIT
    return code


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("tool", choices=["codex", "gemini"])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt", help="task text")
    src.add_argument("--brief", type=Path, help="task brief file (markdown)")
    p.add_argument("--effort", default="medium")
    p.add_argument("--model", help="override the default model")
    p.add_argument("--write", action="store_true", help="allow file edits (never commits)")
    p.add_argument("--cwd", default=".", help="repo or worktree to work in")
    p.add_argument("--label", default="task", help="short name for the answer file and log")
    p.add_argument("--results", type=Path, default=Path("results"))
    a = p.parse_args(argv)
    prompt = a.prompt if a.prompt else a.brief.read_text(encoding="utf-8")
    task = Task(a.tool, prompt, a.effort, a.write, a.cwd, a.model)
    return run(task, DispatchConfig(), a.results, a.label)


if __name__ == "__main__":
    raise SystemExit(main())
