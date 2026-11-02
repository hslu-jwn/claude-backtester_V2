"""Call Codex, Gemini / Claude 4.6 (via Antigravity CLI) or a local Ollama model for one task.
Spec: docs/agent-routing.md.

    python -m backtester.tools.ai_dispatch codex  --effort medium --brief briefs/x.md
    python -m backtester.tools.ai_dispatch gemini --effort high --write --prompt "Write tests ..."
    python -m backtester.tools.ai_dispatch local  --brief errors.txt --prompt "Summarise ..."
    python -m backtester.tools.ai_dispatch groq   --model <id> --prompt "..."  (also openrouter, deepseek)
    python -m backtester.tools.ai_dispatch stats   # calls, minutes, limits per tool and model

It never falls back to another model on its own. Every call:
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

from backtester.paths import RESULTS_DIR

EXIT_VIOLATION = 3
EXIT_LIMIT = 4


KEY_SERVICE = (
    "backtester-ai"  # Windows Credential Manager: python -m keyring set backtester-ai <provider>
)


@dataclass(frozen=True)
class Provider:
    """An OpenAI-compatible chat API; text in / text out, no tools or file access."""

    url: str
    model: str | None = None  # default, set only after a verified probe
    free_suffix: str = ""  # only models ending in this are allowed (OpenRouter free models)
    paid: bool = False  # refused unless --allow-paid


@dataclass(frozen=True)
class DispatchConfig:
    codex_model: str = "gpt-6.1-terra"  # cheapest first; --model gpt-6.1-sol for engine / risk
    gemini_models: Mapping[str, str] = field(
        default_factory=lambda: {
            "low": "gemini-3.8-flash-low",
            "medium": "gemini-3.8-flash-medium",
            "high": "gemini-3.8-flash-high",
        }
    )
    claude46_models: Mapping[str, str] = field(  # older Claude models on the Google quota
        default_factory=lambda: {
            "low": "claude-sonnet-4-6",
            "medium": "claude-sonnet-4-6",
            "high": "claude-opus-4-6-thinking",
        }
    )
    local_models: Mapping[str, str] = field(  # Ollama on this PC: zero paid tokens, text only
        default_factory=lambda: {
            "low": "qwen3.5:4b-q4_K_M",
            "medium": "qwen3.5:9b-q4_K_M",
            "high": "qwen3.5:27b-q4_K_M",
        }
    )
    ollama_url: str = "http://localhost:11434/api/generate"
    providers: Mapping[str, Provider] = field(
        default_factory=lambda: {
            "groq": Provider(
                "https://api.groq.com/openai/v1/chat/completions", model="openai/gpt-oss-120b"
            ),
            "openrouter": Provider(
                "https://openrouter.ai/api/v1/chat/completions",
                model="nvidia/nemotron-3-ultra-550b-a55b:free",
                free_suffix=":free",
            ),
            "deepseek": Provider("https://api.deepseek.com/chat/completions", paid=True),
            "gemini-api": Provider(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                model="gemini-3.8-flash",
            ),
            # github-models: models.github.ai answered "OK" to every request, even unauthenticated
            # (2026-11-02); left out until it returns real API responses.
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
    tool: str  # "codex" | "gemini" | "claude46" (agy) | "local" (Ollama) | a cfg.providers key
    prompt: str
    effort: str = "medium"
    write: bool = False  # may edit files (still never commit)
    cwd: str = "."
    model: str | None = None
    allow_paid: bool = False  # hosted APIs that bill per token


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
        "Work alone: no subagents or parallel tasks (they burn the quota). "
        "End with a short report: what you did, files changed, test results, open questions."
    )
    return f"{limits}\n\nTASK:\n{task.prompt}"


def _effort(task: Task, allowed) -> str:
    if task.effort not in allowed:
        raise ValueError(f"effort {task.effort!r} not in {list(allowed)}")
    return task.effort


def build_codex_cmd(exe: str, task: Task, cfg: DispatchConfig, out_file: str) -> list[str]:
    effort = _effort(task, cfg.codex_efforts)
    # Shell mode (user, 2026-10-22): Windows blocks every command in Codex's plain sandboxes;
    # --approve-for-me runs them in workspace-write with an automatic reviewer. Read-only
    # tasks are enforced by guard_violations.
    return [
        exe, "exec",
        "-C", task.cwd,
        "--approve-for-me",
        "-m", task.model or cfg.codex_model,
        "-c", f'model_reasoning_effort="{effort}"',
        "--color", "never",
        "-o", out_file,
        "-",
    ]  # fmt: skip


def build_agy_cmd(exe: str, task: Task, cfg: DispatchConfig) -> list[str]:
    models = cfg.claude46_models if task.tool == "claude46" else cfg.gemini_models
    model = task.model or models[_effort(task, models)]
    # Headless agy auto-denies every tool (even `git diff`): tools are approved and run inside
    # --sandbox; read-only tasks are enforced by guard_violations, as for Codex.
    return [
        exe, "--model", model, "--sandbox", "--dangerously-skip-permissions",
        "--output-format", "json", "-p", prompt_for(task, cfg),
    ]  # fmt: skip


def build_local_request(task: Task, cfg: DispatchConfig) -> dict:
    model = task.model or cfg.local_models[_effort(task, cfg.local_models)]
    rule = "Answer concise and only from the text below; say so if it is not there."
    prompt = f"{rule}\n\n{task.prompt}"
    return {"model": model, "prompt": prompt, "stream": False, "think": False}


def run_local(task: Task, cfg: DispatchConfig) -> tuple[str, str, int]:
    import urllib.request

    body = json.dumps(build_local_request(task, cfg)).encode()
    req = urllib.request.Request(cfg.ollama_url, body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            return json.loads(resp.read())["response"], "", 0
    except OSError as e:  # Ollama not running: an error, never a silent switch to a paid model
        return "", f"ollama: {e}", 1


def build_api_request(task: Task, cfg: DispatchConfig) -> tuple[str, dict]:
    p = cfg.providers[task.tool]
    model = task.model or p.model
    if not model:
        raise ValueError(f"{task.tool}: no verified default model, give --model")
    if p.free_suffix and not model.endswith(p.free_suffix):
        raise ValueError(f"{task.tool}: only free models ({p.free_suffix}) are allowed")
    if p.paid and not task.allow_paid:
        raise ValueError(f"{task.tool} bills per token: pass --allow-paid to use it")
    rule = "Text only: you cannot read files or run commands. Answer concise."
    content = f"{rule}\n\n{task.prompt}"
    return p.url, {"model": model, "messages": [{"role": "user", "content": content}],
                   "stream": False}  # fmt: skip


def run_api(task: Task, cfg: DispatchConfig) -> tuple[str, str, int]:
    import urllib.error
    import urllib.request

    import keyring

    url, body = build_api_request(task, cfg)
    key = keyring.get_password(KEY_SERVICE, task.tool)
    if not key:
        return "", f"no key: python -m keyring set {KEY_SERVICE} {task.tool}", 1
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "backtester-ai-dispatch/1.0",  # Groq's Cloudflare blocks Python-urllib
    }
    req = urllib.request.Request(url, json.dumps(body).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"], "", 0
    except urllib.error.HTTPError as e:  # 429 -> exit 4 via hit_limit; never a paid fallback
        return "", f"{task.tool}: HTTP {e.code} {e.read()[:500]!r}", 1
    except OSError as e:
        return "", f"{task.tool}: {e}", 1


def usage_summary(rows: list[Mapping]) -> list[tuple[str, str, int, float, dict[str, int]]]:
    """(tool, model, calls, minutes, statuses) per tool and model, from results/ai_calls.jsonl."""
    groups: dict[tuple[str, str], list[Mapping]] = {}
    for r in rows:
        groups.setdefault((r["tool"], r["model"]), []).append(r)
    out = []
    for (tool, model), rs in sorted(groups.items()):
        statuses: dict[str, int] = {}
        for r in rs:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        out.append((tool, model, len(rs), round(sum(r["seconds"] for r in rs) / 60, 1), statuses))
    return out


def parse_agy_output(text: str) -> tuple[str, bool, str]:
    """(answer, ok, note) from agy's JSON answer; text mode prints nothing after tool use."""
    try:
        data = json.loads(text.strip().splitlines()[-1] if text.strip() else "")
    except (json.JSONDecodeError, IndexError):
        return text, False, "no json answer"
    response = data.get("response", "")
    if data.get("status") != "SUCCESS":
        return response, False, f"status {data.get('status')}"
    denied = [d.get("action", "?") for d in data.get("denied_actions") or []]
    if denied:
        return response, False, f"denied: {', '.join(denied)}"
    return response, True, ""


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
    before = repo_state(task.cwd)
    start = time.monotonic()
    if task.tool == "local":
        model = build_local_request(task, cfg)["model"]
        stdout, stderr, code = run_local(task, cfg)
        out.write_text(stdout, encoding="utf-8")
        return _finish(task, cfg, out, stamp, label, model, start, before, stdout, stderr, code, "")
    if task.tool in cfg.providers:
        model = build_api_request(task, cfg)[1]["model"]
        stdout, stderr, code = run_api(task, cfg)
        out.write_text(stdout, encoding="utf-8")
        return _finish(task, cfg, out, stamp, label, model, start, before, stdout, stderr, code, "")
    exe = _exe(task.tool, cfg)
    if task.tool == "codex":
        cmd, stdin = build_codex_cmd(exe, task, cfg, str(out)), prompt_for(task, cfg)
    else:
        cmd, stdin = build_agy_cmd(exe, task, cfg), None
    env = child_env(os.environ, cfg)
    env["PATH"] = _fresh_path(env.get("PATH", ""))
    try:
        proc = subprocess.run(
            cmd, check=False, input=stdin, cwd=task.cwd, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=cfg.timeout_s,
        )  # fmt: skip
        stdout, stderr, code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, code = str(e.stdout or ""), f"timeout after {cfg.timeout_s}s", 124
    note = ""
    if task.tool != "codex":
        answer, ok, note = parse_agy_output(stdout)
        out.write_text(answer, encoding="utf-8")
        if code == 0 and not ok:
            code = 1
    elif not out.exists():
        out.write_text(stdout, encoding="utf-8")
    model = cmd[cmd.index("-m" if task.tool == "codex" else "--model") + 1]
    return _finish(task, cfg, out, stamp, label, model, start, before, stdout, stderr, code, note)


def _finish(task, cfg, out, stamp, label, model, start, before, stdout, stderr, code, note) -> int:
    seconds = round(time.monotonic() - start)
    violations = guard_violations(before, repo_state(task.cwd), cfg, write=task.write)
    limited = code != 0 and hit_limit(stdout + stderr, cfg)
    status = "violation" if violations else "limit" if limited else "ok" if code == 0 else "error"
    entry = {
        "time": stamp, "tool": task.tool, "label": label, "model": model, "effort": task.effort,
        "write": task.write, "seconds": seconds, "exit": code, "status": status,
        "violations": violations, "note": note, "answer": str(out),
    }  # fmt: skip
    with (out.parent.parent / "ai_calls.jsonl").open("a", encoding="utf-8") as log:
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
    tools = ["codex", "gemini", "claude46", "local", *DEFAULT.providers, "stats"]
    p.add_argument("tool", choices=tools)
    p.add_argument("--prompt", help="task text (appended to --brief when both are given)")
    p.add_argument("--brief", type=Path, help="task brief file (markdown)")
    p.add_argument("--effort", default="medium")
    p.add_argument("--model", help="override the default model")
    p.add_argument("--write", action="store_true", help="allow file edits (never commits)")
    p.add_argument("--allow-paid", action="store_true", help="allow a per-token billed API")
    p.add_argument("--cwd", default=".", help="repo or worktree to work in")
    p.add_argument("--label", default="task", help="short name for the answer file and log")
    p.add_argument("--results", type=Path, default=RESULTS_DIR)
    a = p.parse_args(argv)
    if a.tool == "stats":
        log = a.results / "ai_calls.jsonl"
        rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
        for tool, model, calls, minutes, statuses in usage_summary(rows):
            print(f"{tool:9} {model:28} {calls:4} calls {minutes:7.1f} min  {statuses}")
        return 0
    if not (a.prompt or a.brief):
        p.error("give --prompt, --brief or both")
    parts = [a.brief.read_text(encoding="utf-8-sig") if a.brief else "", a.prompt or ""]
    prompt = "\n\n".join(x for x in parts if x)
    task = Task(a.tool, prompt, a.effort, a.write, a.cwd, a.model, a.allow_paid)
    try:
        return run(task, DispatchConfig(), a.results, a.label)
    except ValueError as e:  # refused route (no model, not free, paid without --allow-paid)
        p.error(str(e))


if __name__ == "__main__":
    raise SystemExit(main())
