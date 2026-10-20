"""Single-instance lock `results/live/bot.lock` (ROADMAP 13.4): a PID file, stale when the PID
is gone. The bot takes it at startup, `start_bot` (Live page) refuses while it is held."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from backtester.live import bot as bot_module
from backtester.live.bot import BotConfig
from backtester.live.lock import LOCK_NAME, BotLock, lock_holder, pid_alive
from backtester.ui.pages import live


def tmp_config(folder):
    @dataclass(frozen=True)
    class TmpConfig(BotConfig):
        out_dir: Path = folder

    return TmpConfig


def dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def test_pid_alive_knows_itself_and_a_finished_process():
    assert pid_alive(os.getpid())
    assert not pid_alive(dead_pid())
    assert not pid_alive(0) and not pid_alive(-5)


def test_lock_file_is_a_config_property(tmp_path):
    assert BotConfig(out_dir=tmp_path).lock_file == tmp_path / LOCK_NAME == tmp_path / "bot.lock"


def test_acquire_writes_the_pid_and_release_removes_it(tmp_path):
    lock = BotLock(tmp_path / LOCK_NAME)
    assert lock.acquire()
    assert (tmp_path / LOCK_NAME).read_text().strip() == str(os.getpid())
    lock.release()
    assert not (tmp_path / LOCK_NAME).exists()


def test_a_second_bot_is_refused_while_the_first_lives(tmp_path):
    path = tmp_path / LOCK_NAME
    path.write_text("4242")
    second = BotLock(path, alive=lambda pid: pid == 4242, pid=999)
    assert not second.acquire()
    assert path.read_text() == "4242"  # untouched
    assert lock_holder(path, alive=lambda pid: True) == 4242


def test_a_stale_lock_of_a_dead_pid_is_taken_over(tmp_path):
    path = tmp_path / LOCK_NAME
    path.write_text(str(dead_pid()))
    assert lock_holder(path) is None
    lock = BotLock(path)
    assert lock.acquire()
    assert path.read_text().strip() == str(os.getpid())


def test_release_leaves_a_lock_that_is_not_ours(tmp_path):
    path = tmp_path / LOCK_NAME
    lock = BotLock(path)
    lock.acquire()
    path.write_text("31337")
    lock.release()
    assert path.read_text() == "31337"


def test_an_unreadable_fresh_lock_counts_as_held_an_old_one_as_stale(tmp_path):
    path = tmp_path / LOCK_NAME
    path.write_text("")  # another bot just created it and has not written its PID yet
    assert not BotLock(path).acquire()
    old = path.stat().st_mtime - 3600
    os.utime(path, (old, old))
    assert BotLock(path).acquire()


def test_lock_holder_without_a_file_is_none(tmp_path):
    assert lock_holder(tmp_path / LOCK_NAME) is None


def test_start_bot_refuses_while_the_lock_is_held_even_without_a_heartbeat(tmp_path):
    (tmp_path / LOCK_NAME).write_text("4242")
    calls = []
    msg = live.start_bot(
        tmp_path, datetime.now(UTC), spawn=lambda *a: calls.append(a), alive=lambda pid: True
    )
    assert calls == [] and "already running" in msg.lower()
    assert (tmp_path / LOCK_NAME).exists()


def test_start_bot_does_not_touch_stop_files_when_refusing(tmp_path):
    (tmp_path / LOCK_NAME).write_text("4242")
    (tmp_path / "STOP").write_text("")
    live.start_bot(tmp_path, datetime.now(UTC), spawn=lambda *a: None, alive=lambda pid: True)
    assert (tmp_path / "STOP").exists()


def test_start_bot_ignores_a_stale_lock(tmp_path):
    (tmp_path / LOCK_NAME).write_text("4242")
    calls = []
    live.start_bot(
        tmp_path, datetime.now(UTC), spawn=lambda *a: calls.append(a), alive=lambda pid: False
    )
    assert len(calls) == 1


def test_main_exits_without_trading_when_another_bot_holds_the_lock(tmp_path, monkeypatch):
    (tmp_path / LOCK_NAME).write_text("4242")
    monkeypatch.setattr(bot_module, "BotLock", lambda p: BotLock(p, alive=lambda pid: True))
    monkeypatch.setattr(bot_module, "load_trading_settings", lambda: SimpleNamespace(platform=""))
    monkeypatch.setattr(bot_module, "load_credentials", lambda platform: None)
    monkeypatch.setattr(bot_module, "load_mt5", lambda: pytest.fail("must not touch MT5"))
    monkeypatch.setattr(bot_module, "BotConfig", tmp_config(tmp_path))
    monkeypatch.setattr(bot_module, "utf8_output", lambda: None)
    assert bot_module.main(["--symbols", "US500"]) == 3
    assert (tmp_path / LOCK_NAME).read_text() == "4242"


def test_main_releases_the_lock_when_the_bot_ends(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_module, "load_trading_settings", lambda: SimpleNamespace(platform=""))
    monkeypatch.setattr(bot_module, "load_credentials", lambda platform: None)
    monkeypatch.setattr(bot_module, "load_mt5", lambda: object())
    monkeypatch.setattr(bot_module, "utf8_output", lambda: None)
    monkeypatch.setattr(bot_module, "_telegram_notifier", lambda cfg: None)
    monkeypatch.setattr(bot_module, "BotConfig", tmp_config(tmp_path))
    seen = {}

    class FakeBot:
        def __init__(self, config, *a, **k):
            seen["lock"] = (tmp_path / LOCK_NAME).read_text().strip()

        def run(self):
            return 0

    monkeypatch.setattr(bot_module, "Bot", FakeBot)
    assert bot_module.main(["--symbols", "US500"]) == 0
    assert seen["lock"] == str(os.getpid())  # held while running
    assert not (tmp_path / LOCK_NAME).exists()  # released afterwards
