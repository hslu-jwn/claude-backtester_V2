"""ai_dispatch: how Opus calls Codex and Gemini (Antigravity CLI). Spec: AGENTS.md â€º Team."""

from __future__ import annotations

import pytest

from backtester.tools.ai_dispatch import (
    DispatchConfig,
    RepoState,
    Task,
    build_agy_cmd,
    build_codex_cmd,
    child_env,
    guard_violations,
    hit_limit,
    prompt_for,
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


def test_codex_read_only_task_uses_read_only_sandbox_model_and_effort():
    cmd = build_codex_cmd("codex.cmd", task(), CFG, out_file="C:/out.md")
    assert cmd[:2] == ["codex.cmd", "exec"]
    assert cmd[cmd.index("-s") + 1] == "read-only"
    assert cmd[cmd.index("-m") + 1] == CFG.codex_model
    assert 'model_reasoning_effort="medium"' in cmd
    assert cmd[cmd.index("-C") + 1] == "C:/repo"
    assert cmd[cmd.index("-o") + 1] == "C:/out.md"
    assert cmd[-1] == "-"  # prompt comes from stdin: no quoting problems with long briefs
    assert "--dangerously-bypass-approvals-and-sandbox" not in cmd


def test_codex_write_task_gets_workspace_write_never_full_access():
    cmd = build_codex_cmd("codex.cmd", task(write=True), CFG, out_file="o.md")
    assert cmd[cmd.index("-s") + 1] == "workspace-write"
    assert "danger-full-access" not in cmd


def test_codex_model_override():
    cmd = build_codex_cmd("codex.cmd", task(model="gpt-6-astra"), CFG, out_file="o.md")
    assert cmd[cmd.index("-m") + 1] == "gpt-6-astra"


@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_agy_effort_picks_the_flash_variant(effort):
    cmd = build_agy_cmd("agy.exe", task(tool="gemini", effort=effort), CFG)
    assert cmd[cmd.index("--model") + 1] == CFG.gemini_models[effort]
    assert "--sandbox" in cmd  # terminal restrictions always on
    assert cmd[cmd.index("-p") + 1].startswith("Follow AGENTS.md")


def test_agy_only_write_tasks_auto_approve_tools():
    read = build_agy_cmd("agy.exe", task(tool="gemini"), CFG)
    write = build_agy_cmd("agy.exe", task(tool="gemini", write=True), CFG)
    assert "--dangerously-skip-permissions" not in read
    assert "--dangerously-skip-permissions" in write


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
    ):
        assert must in p


# --- environment ---------------------------------------------------------------------------


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
        }
    )
    assert env["PATH"] == "p" and env["USERPROFILE"] == "u"
    assert (
        not {"TELEGRAM_TOKEN", "MT5_PASSWORD", "SOME_API_KEY", "GH_TOKEN", "MY_SECRET"} & env.keys()
    )
    assert env["NODE_OPTIONS"] == "--use-system-ca"


# --- guard ---------------------------------------------------------------------------------


def state(head="a1", branch="main", dirty=()):
    return RepoState(head=head, branch=branch, dirty=frozenset(dirty))


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
