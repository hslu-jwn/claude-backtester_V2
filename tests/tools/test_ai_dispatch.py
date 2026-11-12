"""ai_dispatch: how Opus calls Codex and Gemini (Antigravity CLI). Spec: AGENTS.md › Team."""

from __future__ import annotations

import pytest

from backtester.tools.ai_dispatch import (
    DispatchConfig,
    RepoState,
    Task,
    _fresh_path,
    build_agy_cmd,
    build_api_request,
    build_codex_cmd,
    build_local_request,
    child_env,
    guard_violations,
    hit_limit,
    parse_agy_output,
    parse_porcelain_z,
    prompt_for,
    usage_summary,
)

CFG = DispatchConfig()


def task(**kw) -> Task:
    base = {
        "tool": "codex",
        "prompt": "Review x.py",
        "effort": "medium",
        "write": False,
        "cwd": "C:/repo",
    }
    return Task(**{**base, **kw})


# --- command lines -------------------------------------------------------------------------


def test_codex_runs_in_shell_mode_with_model_and_effort():
    """Shell mode (approved by the user, 2026-10-22): on Windows Codex's plain sandboxes block
    every command, so it runs with --approve-for-me (workspace-write sandbox + automatic
    reviewer). Read-only tasks are enforced by the guard."""
    cmd = build_codex_cmd("codex.cmd", task(), CFG, out_file="C:/out.md")
    assert cmd[:2] == ["codex.cmd", "exec"]
    assert "--approve-for-me" in cmd and "-s" not in cmd
    assert cmd[cmd.index("-m") + 1] == CFG.codex_model
    assert 'model_reasoning_effort="medium"' in cmd
    assert cmd[cmd.index("-C") + 1] == "C:/repo"
    assert cmd[cmd.index("-o") + 1] == "C:/out.md"
    assert cmd[-1] == "-"  # prompt comes from stdin: no quoting problems with long briefs
    assert "--dangerously-bypass-approvals-and-sandbox" not in cmd


def test_codex_never_gets_full_access():
    cmd = build_codex_cmd("codex.cmd", task(write=True), CFG, out_file="o.md")
    assert "danger-full-access" not in cmd
    assert "--dangerously-bypass-approvals-and-sandbox" not in cmd


def test_codex_web_search_only_when_asked():
    """Idea harvest (skill idea-harvest): `codex exec` has no web search unless `--search` is
    given before `exec` (probe 2026-11-12); the default stays offline."""
    assert "--search" not in build_codex_cmd("codex.cmd", task(), CFG, out_file="o.md")
    cmd = build_codex_cmd("codex.cmd", task(search=True), CFG, out_file="o.md")
    assert cmd[:3] == ["codex.cmd", "--search", "exec"]


def test_codex_web_search_refused_for_write_tasks():
    """Web pages are untrusted input: a task that reads the web never edits files."""
    with pytest.raises(ValueError, match="search"):
        build_codex_cmd("codex.cmd", task(search=True, write=True), CFG, out_file="o.md")


def test_codex_model_override():
    cmd = build_codex_cmd("codex.cmd", task(model="gpt-6-astra"), CFG, out_file="o.md")
    assert cmd[cmd.index("-m") + 1] == "gpt-6-astra"


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_agy_effort_picks_the_flash_variant(effort):
    cmd = build_agy_cmd("agy.exe", task(tool="gemini", effort=effort), CFG)
    assert cmd[cmd.index("--model") + 1] == CFG.gemini_models[effort]
    assert "--sandbox" in cmd  # terminal restrictions always on
    assert cmd[cmd.index("-p") + 1].startswith("Follow AGENTS.md")


def test_agy_tools_run_inside_its_sandbox_and_answer_as_json():
    """Headless agy auto-denies every tool permission (even `git diff`), so tools are approved
    and run inside --sandbox; read-only is enforced by the guard, as for Codex."""
    for write in (False, True):
        cmd = build_agy_cmd("agy.exe", task(tool="gemini", write=write), CFG)
        assert "--sandbox" in cmd and "--dangerously-skip-permissions" in cmd
        assert cmd[cmd.index("--output-format") + 1] == "json"


def test_agy_json_answer_is_unpacked():
    ok = '{"status":"SUCCESS","response":"APPROVE\\n","denied_actions":[]}'
    assert parse_agy_output(ok) == ("APPROVE\n", True, "")
    denied = '{"status":"SUCCESS","response":"","denied_actions":[{"action":"command"}]}'
    assert parse_agy_output(denied) == ("", False, "denied: command")
    assert parse_agy_output('{"status":"ERROR","response":"x"}') == ("x", False, "status ERROR")
    assert parse_agy_output("not json") == ("not json", False, "no json answer")


@pytest.mark.parametrize(
    ("effort", "model"),
    [("low", "claude-sonnet-4-6"), ("medium", "claude-sonnet-4-6"),
     ("high", "claude-opus-4-6-thinking")],
)  # fmt: skip
def test_claude46_runs_through_agy_with_sonnet_or_opus(effort, model):
    cmd = build_agy_cmd("agy.exe", task(tool="claude46", effort=effort, write=True), CFG)
    assert cmd[cmd.index("--model") + 1] == model
    assert "--sandbox" in cmd and "--dangerously-skip-permissions" in cmd


def test_unknown_effort_is_refused():
    with pytest.raises(ValueError, match="effort"):
        build_agy_cmd("agy.exe", task(tool="gemini", effort="ultra"), CFG)


# --- prompt --------------------------------------------------------------------------------


def test_prompt_carries_the_limits_and_the_task():
    p = prompt_for(task(prompt="Write tests for 3.2"), CFG)
    assert p.startswith("Follow AGENTS.md")
    for must in (
        "never commit",
        "never push",
        "credentials",
        "src/backtester/live/",
        "Write tests for 3.2",
        "no subagents",  # Claude 4.6 burned its weekly quota on four parallel subagents
    ):
        assert must in p


# --- environment ---------------------------------------------------------------------------


def test_fresh_path_is_unchanged_off_windows(monkeypatch):
    monkeypatch.setattr("backtester.tools.ai_dispatch.sys.platform", "linux")
    assert _fresh_path("a;b") == "a;b"


def test_child_env_drops_secrets_and_sets_system_ca():
    env = child_env(
        {
            "PATH": "p",
            "TELEGRAM_TOKEN": "x",
            "MT5_PASSWORD": "y",
            "SOME_API_KEY": "z",
            "GH_TOKEN": "t",
            "MY_SECRET": "s",
            "USERPROFILE": "u",
            "AWS_ACCESS_KEY_ID": "a",
            "SSH_PRIVATE_KEY": "k",
        }
    )
    assert env["PATH"] == "p" and env["USERPROFILE"] == "u"
    assert (
        not {
            "TELEGRAM_TOKEN",
            "MT5_PASSWORD",
            "SOME_API_KEY",
            "GH_TOKEN",
            "MY_SECRET",
            "AWS_ACCESS_KEY_ID",
            "SSH_PRIVATE_KEY",
        }
        & env.keys()
    )
    assert env["NODE_OPTIONS"] == "--use-system-ca"


# --- guard ---------------------------------------------------------------------------------


def state(head="a1", branch="main", dirty=(), refs=("a1 refs/heads/main",), reflog=5):
    return RepoState(head, branch, frozenset(dirty), frozenset(refs), reflog)


def test_commit_then_reset_new_branch_and_push_are_violations():
    """HEAD back where it was still leaves a reflog entry; a push moves a remote-tracking ref."""
    found = guard_violations(
        state(refs={"a1 refs/heads/main", "a1 refs/remotes/origin/main"}),
        state(
            refs={"a1 refs/heads/main", "b2 refs/heads/x", "b2 refs/remotes/origin/main"}, reflog=7
        ),
        CFG,
        write=True,
    )
    text = "\n".join(found)
    assert "reflog" in text and "refs/heads/x" in text and "refs/remotes/origin/main" in text


def test_protected_paths_match_regardless_of_case():
    found = guard_violations(state(), state(dirty={"SRC/Backtester/Live/bot.py"}), CFG, write=True)
    assert found == ["protected path changed: SRC/Backtester/Live/bot.py"]


def test_porcelain_z_keeps_the_first_character_and_skips_rename_sources():
    z = " M src/a.py\0?? new file.md\0R  docs/new.md\0docs/old.md\0"
    assert parse_porcelain_z(z) == {"src/a.py", "new file.md", "docs/new.md"}


def test_clean_run_has_no_violations():
    assert guard_violations(state(), state(dirty={"tests/x.py"}), CFG, write=True) == []


def test_read_only_task_must_not_change_files():
    before = state(dirty={"docs/a.md"})  # Opus's own edit, not the model's
    assert guard_violations(before, state(dirty={"docs/a.md"}), CFG, write=False) == []
    found = guard_violations(before, state(dirty={"docs/a.md", "tests/x.py"}), CFG, write=False)
    assert found == ["read-only task changed: tests/x.py"]


def test_commit_branch_switch_and_live_edits_are_violations():
    found = guard_violations(
        state(dirty={"src/backtester/live/orders.py"}),  # already dirty before: not the model's
        state(
            head="b2",
            branch="other",
            dirty={"src/backtester/live/orders.py", "src/backtester/live/bot.py", ".env"},
        ),
        CFG,
        write=True,
    )
    text = "\n".join(found)
    assert "commit" in text and "branch" in text
    assert "src/backtester/live/bot.py" in text and ".env" in text
    assert "orders.py" not in text


# --- usage limits --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "You've hit your usage limit. Try again in 3h",
        "Error 429: RESOURCE_EXHAUSTED",
        "Quota exceeded for model",
        "rate limit reached",
    ],
)
def test_limit_messages_are_recognised(text):
    assert hit_limit(text)


def test_normal_output_is_not_a_limit():
    assert not hit_limit("All 12 tests passed; the limit order code is unchanged.")


def test_limit_detection_ignores_case():
    assert hit_limit("USAGE LIMIT reached") is True
    assert hit_limit("Rate Limit") is True


# --- local lane (Ollama, zero paid tokens) and usage stats --------------------------------


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_local_effort_picks_an_ollama_model_and_never_thinks(effort):
    body = build_local_request(task(tool="local", effort=effort), CFG)
    assert body["model"] == CFG.local_models[effort]
    assert body["stream"] is False and body["think"] is False
    assert body["prompt"].endswith("Review x.py")


def test_local_prompt_is_text_only_without_repo_rules():
    """The local model gets no tools, so it is told to answer briefly from the text alone."""
    prompt = build_local_request(task(tool="local"), CFG)["prompt"]
    assert "AGENTS.md" not in prompt and "concise" in prompt


def test_usage_summary_counts_calls_minutes_and_limits_per_tool_and_model():
    rows = [
        {"tool": "codex", "model": "m1", "status": "ok", "seconds": 60},
        {"tool": "codex", "model": "m1", "status": "limit", "seconds": 30},
        {"tool": "local", "model": "q", "status": "ok", "seconds": 5},
    ]
    assert usage_summary(rows) == [
        ("codex", "m1", 2, 1.5, {"ok": 1, "limit": 1}),
        ("local", "q", 1, 0.1, {"ok": 1}),
    ]


# --- hosted API lanes (Groq, OpenRouter, DeepSeek): text only, key from the Credential Manager


def test_api_request_is_openai_chat_format_with_the_limits_prompt():
    url, body = build_api_request(task(tool="groq", model="m-1"), CFG)
    assert url == CFG.providers["groq"].url
    assert body["model"] == "m-1" and body["stream"] is False
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][0]["content"].endswith("Review x.py")


def test_api_needs_a_model_when_the_provider_has_no_default():
    with pytest.raises(ValueError, match="--model"):
        build_api_request(
            task(tool="groq", model=None),
            DispatchConfig(providers={"groq": CFG.providers["groq"].__class__(url="u")}),
        )


def test_openrouter_refuses_models_that_are_not_free():
    with pytest.raises(ValueError, match=":free"):
        build_api_request(task(tool="openrouter", model="openai/gpt-x"), CFG)
    build_api_request(task(tool="openrouter", model="deepseek/deepseek-r1:free"), CFG)


def test_paid_provider_is_refused_unless_allowed():
    with pytest.raises(ValueError, match="--allow-paid"):
        build_api_request(task(tool="deepseek", model="deepseek-chat"), CFG)
    build_api_request(task(tool="deepseek", model="deepseek-chat", allow_paid=True), CFG)
