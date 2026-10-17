"""The /live page (ROADMAP 7.2 monitoring): view model, buttons and rendering. No real bot."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from backtester.live.status import STALE_S, write_status
from backtester.ui import app as app_module
from backtester.ui.pages import live

NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def status(age_s=10.0, **kw) -> dict:
    base = {
        "running": True, "connected": True, "account_mode": "DEMO",
        "heartbeat": (NOW - timedelta(seconds=age_s)).isoformat(),
        "date": "2026-01-12", "balance": 100_000.0, "equity": 99_000.0,
        "day_pl": -1000.0, "day_pl_percent": -1.0, "day_r": -2.0,
        "guard": {"state": "ok", "reason": "", "daily_stop_percent": 2.0,
                  "ftmo_daily_percent": 5.0, "ftmo_max_percent": 10.0},
        "positions": [{"symbol": "US500", "side": "buy", "lots": 1.0, "entry": 100.0,
                       "sl": 95.0, "floating_r": 0.4, "ticket": 1, "since": ""}],
        "signals": [{"time": "2026-01-12T14:41:00+00:00", "symbol": "US500", "side": "buy",
                     "status": "skipped", "reason": "daily stop active"}],
        "last_error": "",
    }  # fmt: skip
    return {**base, **kw}


def text_of(component) -> str:
    return json.dumps(component, default=lambda o: o.to_plotly_json(), ensure_ascii=False)


# --- view model ----------------------------------------------------------------------------


def test_no_status_file_means_never_started(tmp_path):
    view = live.live_view(tmp_path, NOW)
    assert view["state"] == "none" and view["status"] is None and view["log"] == []


def test_fresh_heartbeat_is_running(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=30))
    assert live.live_view(tmp_path, NOW)["state"] == "running"


def test_stale_heartbeat_is_flagged(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=STALE_S + 1))
    assert live.live_view(tmp_path, NOW)["state"] == "stale"


def test_a_stopped_bot_is_not_running_even_with_a_fresh_beat(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=5, running=False))
    assert live.live_view(tmp_path, NOW)["state"] == "stopped"


def test_log_shows_the_last_50_lines_of_today(tmp_path):
    folder = tmp_path / "2026-01-12"
    folder.mkdir()
    lines = [
        json.dumps(
            {
                "time": f"2026-01-12T14:{i // 60:02d}:{i % 60:02d}+00:00",
                "label": "skip",
                "request": {"symbol": "US500", "reason": f"n{i}"},
            }
        )
        for i in range(80)
    ]
    (folder / "orders.jsonl").write_text("\n".join(lines) + "\nnot json\n", encoding="utf-8")
    (tmp_path / "2026-01-11").mkdir()
    (tmp_path / "2026-01-11" / "orders.jsonl").write_text(
        json.dumps({"time": "x", "label": "old", "request": {}}) + "\n"
    )
    log = live.live_view(tmp_path, NOW)["log"]
    assert len(log) == 50
    assert "reason=n79" in log[-1] and "skip" in log[-1] and all("old" not in x for x in log)


# --- buttons ---------------------------------------------------------------------------------


def test_stop_and_emergency_create_the_files(tmp_path):
    live.request_stop(tmp_path)
    assert (tmp_path / "STOP").exists() and not (tmp_path / "EMERGENCY").exists()
    live.request_emergency(tmp_path)
    assert (tmp_path / "EMERGENCY").exists()


def test_start_spawns_a_detached_bot(tmp_path):
    calls = []
    msg = live.start_bot(tmp_path, NOW, spawn=lambda cmd, log: calls.append((cmd, log)))
    (cmd, log) = calls[0]
    assert cmd[1:] == ["-m", "backtester.live.bot"]
    assert "started" in msg.lower()
    assert log.parent == tmp_path


def test_start_refuses_while_the_heartbeat_is_fresh(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=20))
    calls = []
    msg = live.start_bot(tmp_path, NOW, spawn=lambda *a: calls.append(a))
    assert calls == [] and "already running" in msg.lower()


def test_start_allowed_when_stale_or_stopped(tmp_path):
    calls = []
    for n, kw in enumerate(({"age_s": STALE_S + 60}, {"age_s": 5, "running": False}), start=1):
        write_status(tmp_path / "status.json", status(**kw))
        live.start_bot(tmp_path, NOW, spawn=lambda *a: calls.append(a))
        assert len(calls) == n


def test_start_removes_a_leftover_stop_file(tmp_path):
    (tmp_path / "STOP").write_text("")
    live.start_bot(tmp_path, NOW, spawn=lambda *a: None)
    assert not (tmp_path / "STOP").exists()


def test_start_reports_a_spawn_failure(tmp_path):
    def boom(*a):
        raise OSError("no python")

    assert "could not" in live.start_bot(tmp_path, NOW, spawn=boom).lower()


# --- rendering -------------------------------------------------------------------------------


def test_render_shows_the_numbers(tmp_path):
    write_status(tmp_path / "status.json", status())
    text = text_of(live.render(live.live_view(tmp_path, NOW)))
    for s in ("DEMO", "-1.0", "US500", "daily stop active", "99,000"):
        assert s in text


def test_stale_heartbeat_is_red(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=STALE_S + 30))
    text = text_of(live.render(live.live_view(tmp_path, NOW)))
    assert "lv-stale" in text and "no heartbeat" in text.lower()


def test_fresh_heartbeat_is_not_red(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=10))
    assert "lv-stale" not in text_of(live.render(live.live_view(tmp_path, NOW)))


def test_render_without_status_does_not_crash(tmp_path):
    assert "not started" in text_of(live.render(live.live_view(tmp_path, NOW))).lower()


def test_guard_bar_scale():
    s = status(day_pl_percent=-2.5)
    bar = live.guard_bar(s)
    assert bar["loss_percent"] == 2.5 and bar["stop_percent"] == 2.0 and bar["limit_percent"] == 5.0
    assert bar["fill_width"] == 50.0 and bar["level"] == "stopped"
    assert live.guard_bar(status(day_pl_percent=1.0))["fill_width"] == 0.0
    assert live.guard_bar(status(day_pl_percent=-1.0))["level"] == "ok"
    assert live.guard_bar(status(day_pl_percent=-4.9))["fill_width"] == 98.0
    assert live.guard_bar(status(day_pl_percent=-9.0))["fill_width"] == 100.0


# --- the app ---------------------------------------------------------------------------------


def test_app_routes_live_and_links_to_it():
    page = app_module.page_for("/live", None)
    assert "lv-interval" in text_of(page)
    app = app_module.create_app()
    assert "lv-interval" in text_of(app.validation_layout)
    from backtester.ui import trading_panel

    assert "/live" in text_of(trading_panel.layout())
