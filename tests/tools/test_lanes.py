"""Lanes: git worktrees next to V2 for parallel strategy work. Spec: research-runner.md > Lanes.

Every test works in a temporary git repository (`git init` in tmp_path, user.name / email set
locally there); no worktree or branch is ever created in the repository the tests run from.
Cases: briefs/v26c-test-cases.md D.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from backtester.tools import lanes


def git(cwd, *args):
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, encoding="utf-8"
    )
    return done.stdout.strip()


def write(root, rel, text="x\n"):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def commit_all(cwd, message="change"):
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "-m", message)


@pytest.fixture
def root(tmp_path):
    """The stand-in for the V2 root: a temporary repo with one strategy and a registry."""
    repo = tmp_path / "V2"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "commit.gpgsign", "false")
    write(repo, ".gitignore", "lanes.json\nresults/\n")
    write(repo, "src/backtester/strategy/gap_fade/config.py")
    write(repo, "src/backtester/strategy/registry.py")
    write(repo, "src/backtester/engine/loop.py")
    write(repo, "docs/strategy-gap-fade.md")
    write(repo, "research/grids/other.toml")
    commit_all(repo, "initial")
    return repo


def lane_path(root, name):
    return root.parent / f"bt-lane-{name}"


def test_d1_create_registers_worktree_branch_and_base(root):
    head = git(root, "rev-parse", "HEAD")
    entry = lanes.create("momo", root=root)
    path = lane_path(root, "momo")
    assert Path(entry["path"]) == path.resolve() and path.is_dir()
    assert entry["branch"] == "lane/momo" and entry["base_commit"] == head
    assert entry["created"]
    assert git(path, "rev-parse", "--abbrev-ref", "HEAD") == "lane/momo"
    assert git(path, "rev-parse", "HEAD") == head
    saved = json.loads((root / "lanes.json").read_text(encoding="utf-8"))
    assert [e["name"] for e in saved["lanes"]] == ["momo"]
    assert set(saved["lanes"][0]) == {"name", "path", "branch", "base_commit", "created"}
    assert not (path / "data").exists()  # data / results are shared, never copied
    assert "lane/momo" in git(root, "branch", "--list")


def test_d2_create_twice_existing_path_or_branch_refused(root):
    lanes.create("momo", root=root)
    with pytest.raises(lanes.LaneError, match="already"):
        lanes.create("momo", root=root)
    lane_path(root, "other").mkdir()
    with pytest.raises(lanes.LaneError, match="exists"):
        lanes.create("other", root=root)
    git(root, "branch", "lane/third")
    with pytest.raises(lanes.LaneError, match="branch"):
        lanes.create("third", root=root)
    saved = json.loads((root / "lanes.json").read_text(encoding="utf-8"))
    assert [e["name"] for e in saved["lanes"]] == ["momo"]  # no half state registered
    assert not lane_path(root, "third").exists()


@pytest.mark.parametrize(
    "name", ["", "Momo", "mo-mo", "mo.mo", "mo mo", "a/b", "..", "mo\\mo", "mömö", " "]
)
def test_d3_bad_names_refused(root, name):
    with pytest.raises(lanes.LaneError, match="name"):
        lanes.create(name, root=root)
    assert not (root / "lanes.json").exists()


def test_d3_good_names(root):
    for name in ("a", "gap_2", "0x1_y"):
        lanes.create(name, root=root)
    assert [e["name"] for e in lanes.load(root)] == ["a", "gap_2", "0x1_y"]


def test_d4_existing_strategy_name_needs_flag(root):
    with pytest.raises(lanes.LaneError, match="existing"):
        lanes.create("gap_fade", root=root)
    entry = lanes.create("gap_fade", root=root, existing=True)
    assert entry["name"] == "gap_fade"
    assert lanes.check("gap_fade", root=root) == []


def test_d5_registry_is_git_ignored(root):
    lanes.create("momo", root=root)
    assert git(root, "status", "--porcelain", "--", "lanes.json") == ""
    assert git(root, "check-ignore", "lanes.json") == "lanes.json"
    # the repository the tests run from ignores it as well
    repo = Path(__file__).resolve().parents[2]
    ignored = (repo / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "lanes.json" in [line.strip() for line in ignored]


ALLOWED = [
    "src/backtester/strategy/momo/config.py",
    "src/backtester/strategy/momo/sub/deep.py",
    "docs/strategy-momo.md",
    "tests/strategy/momo/test_x.py",
    "research/grids/momo.toml",
    "research/grids/momo_fx.toml",
]


def test_d6_check_passes_for_allowed_paths_committed_uncommitted_untracked(root):
    lanes.create("momo", root=root)
    lane = lane_path(root, "momo")
    for rel in ALLOWED[:2]:
        write(lane, rel)
    commit_all(lane, "strategy")
    write(lane, ALLOWED[2])  # untracked
    write(lane, ALLOWED[3])
    git(lane, "add", ALLOWED[3])  # staged
    write(lane, ALLOWED[4])
    write(lane, ALLOWED[5])
    assert lanes.check("momo", root=root) == []
    assert lanes.main(["check", "momo"], root=root) == 0


def test_d7_check_fails_listing_other_files(root, capsys):
    lanes.create("momo", root=root)
    lane = lane_path(root, "momo")
    write(lane, ALLOWED[0])
    bad = [
        "src/backtester/engine/new.py",
        "src/backtester/strategy/registry.py",
        "src/backtester/strategy/other/config.py",
        "src/backtester/strategy/momo_extra/config.py",  # prefix of the name is not the folder
        "docs/strategy-momo-fx.md",
        "docs/strategy-gap-fade.md",
        "tests/strategy/momo2/test_x.py",
        "research/grids/other.toml",
        "research/grids/momo/sub.toml",
        "README.md",
    ]
    for rel in bad:
        write(lane, rel, "changed\n")
    commit_all(lane, "mixed")
    write(lane, "src/backtester/engine/loop.py", "edited\n")  # tracked, uncommitted edit
    write(lane, "notes.txt")  # untracked
    found = lanes.check("momo", root=root)
    assert sorted(found) == sorted([*bad, "src/backtester/engine/loop.py", "notes.txt"])
    assert ALLOWED[0] not in found
    capsys.readouterr()
    assert lanes.main(["check", "momo"], root=root) == 1
    out = capsys.readouterr()
    text = out.out + out.err
    assert "src/backtester/engine/new.py" in text and "notes.txt" in text
    assert ALLOWED[0] not in text


def test_d7_deleting_and_renaming_shared_files_is_caught(root):
    lanes.create("momo", root=root)
    lane = lane_path(root, "momo")
    (lane / "src/backtester/engine/loop.py").unlink()
    git(lane, "mv", "docs/strategy-gap-fade.md", "docs/strategy-momo.md")
    found = lanes.check("momo", root=root)
    assert "src/backtester/engine/loop.py" in found
    assert "docs/strategy-gap-fade.md" in found  # the rename's old side is a shared file


def test_d8_list_shows_state(root):
    lanes.create("momo", root=root)
    lanes.create("clean", root=root)
    lane = lane_path(root, "momo")
    write(lane, ALLOWED[0])
    commit_all(lane, "one")
    write(root, "docs/new.md")
    commit_all(root, "on main")
    write(lane, "src/backtester/engine/oops.py")  # dirty and off limits
    rows = {r["name"]: r for r in lanes.list_lanes(root=root)}
    momo, clean = rows["momo"], rows["clean"]
    assert Path(momo["path"]) == lane.resolve() and momo["branch"] == "lane/momo"
    assert (momo["ahead"], momo["behind"]) == (1, 1)
    assert momo["dirty"] is True and momo["check_ok"] is False
    assert momo["offending"] == ["src/backtester/engine/oops.py"]
    assert (clean["ahead"], clean["behind"], clean["dirty"], clean["check_ok"]) == (
        0,
        1,
        False,
        True,
    )
    shutil_rmtree(lane_path(root, "clean"))
    rows = {r["name"]: r for r in lanes.list_lanes(root=root)}
    assert rows["clean"]["missing"] is True


def shutil_rmtree(path):
    import shutil
    import stat

    def writable(func, p, _):
        Path(p).chmod(stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=writable)


def test_d8_list_cli_prints_a_row_per_lane(root, capsys):
    lanes.create("momo", root=root)
    capsys.readouterr()
    assert lanes.main(["list"], root=root) == 0
    out = capsys.readouterr().out
    assert "momo" in out and "lane/momo" in out and "dirty" in out
    empty = root.parent / "none"
    empty.mkdir()
    assert lanes.list_lanes(root=empty) == []


def test_d9_remove_clean_merged_lane_keeps_branch(root):
    lanes.create("momo", root=root)
    lanes.remove("momo", root=root)
    assert not lane_path(root, "momo").exists()
    assert lanes.load(root) == []
    assert "lane/momo" in git(root, "branch", "--list")
    assert "bt-lane-momo" not in git(root, "worktree", "list")


def test_d10_remove_refuses_dirty_without_force(root):
    lanes.create("momo", root=root)
    lane = lane_path(root, "momo")
    write(lane, ALLOWED[0])
    with pytest.raises(lanes.LaneError, match="uncommitted"):
        lanes.remove("momo", root=root)
    assert lane.is_dir() and [e["name"] for e in lanes.load(root)] == ["momo"]
    lanes.remove("momo", root=root, force=True)
    assert not lane.exists() and lanes.load(root) == []
    assert "lane/momo" in git(root, "branch", "--list")


def test_d11_remove_refuses_unmerged_branch_and_never_deletes_it(root):
    lanes.create("momo", root=root)
    lane = lane_path(root, "momo")
    write(lane, ALLOWED[0])
    commit_all(lane, "work")
    with pytest.raises(lanes.LaneError, match="unmerged"):
        lanes.remove("momo", root=root)
    assert lane.is_dir()
    lanes.remove("momo", root=root, force=True)
    assert not lane.exists()
    assert "lane/momo" in git(root, "branch", "--list")  # commits are not lost
    # once merged into the V2 branch a lane can be removed without --force
    lanes.create("two", root=root)
    write(lane_path(root, "two"), "src/backtester/strategy/two/a.py")
    commit_all(lane_path(root, "two"), "two")
    git(root, "merge", "-q", "--no-edit", "lane/two")
    lanes.remove("two", root=root)
    assert not lane_path(root, "two").exists()


def test_d11_remove_lane_whose_folder_is_gone(root):
    lanes.create("momo", root=root)
    shutil_rmtree(lane_path(root, "momo"))
    lanes.remove("momo", root=root)
    assert lanes.load(root) == []
    assert "bt-lane-momo" not in git(root, "worktree", "list")


def test_d12_unknown_lane(root, capsys):
    with pytest.raises(lanes.LaneError, match="no lane"):
        lanes.check("nope", root=root)
    with pytest.raises(lanes.LaneError, match="no lane"):
        lanes.remove("nope", root=root)
    assert lanes.main(["check", "nope"], root=root) == 1
    assert lanes.main(["remove", "nope"], root=root) == 1
    assert "no lane" in capsys.readouterr().err


def test_d13_cli_roundtrip_and_exit_codes(root, capsys):
    assert lanes.main(["create", "momo"], root=root) == 0
    assert lane_path(root, "momo").is_dir()
    assert lanes.main(["create", "momo"], root=root) == 1
    assert lanes.main(["create", "Bad-Name"], root=root) == 1
    assert lanes.main(["create", "gap_fade"], root=root) == 1
    assert lanes.main(["create", "gap_fade", "--existing"], root=root) == 0
    write(lane_path(root, "momo"), "src/backtester/engine/x.py")
    assert lanes.main(["check", "momo"], root=root) == 1
    assert lanes.main(["remove", "momo"], root=root) == 1
    assert lanes.main(["remove", "momo", "--force"], root=root) == 0
    assert [e["name"] for e in lanes.load(root)] == ["gap_fade"]
    capsys.readouterr()


def test_resolve_lane_by_name_or_path(root):
    entry = lanes.create("momo", root=root)
    assert lanes.find("momo", root=root)["path"] == entry["path"]
    with pytest.raises(lanes.LaneError):
        lanes.find("nope", root=root)
