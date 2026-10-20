"""The /live page (ROADMAP 7.2 monitoring): view model, buttons and rendering. No real bot."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from dash import html

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


def rendered(tmp_path, st=None, now=NOW) -> str:
    if st is not None:
        write_status(tmp_path / "status.json", st)
    return text_of(live.render(live.live_view(tmp_path, now), now))


def test_render_shows_the_numbers(tmp_path):
    text = rendered(tmp_path, status(initial_balance=100_000.0, symbols=["US500"]))
    for s in ("DEMO", "-1.00 %", "US500", "$99,000", "$100,000", "-$1,000 floating", "-2.0 R",
              "Running"):  # fmt: skip
        assert s in text


def test_render_signals_and_positions(tmp_path):
    text = rendered(tmp_path, status())
    assert (
        "daily stop active" in text and "15:41" in text and "+0.40" in text
    )  # 14:41 UTC = 15:41 CET


def test_stale_heartbeat_is_red(tmp_path):
    text = rendered(tmp_path, status(age_s=STALE_S + 30))
    assert "lv-stale" in text and "no heartbeat" in text.lower() and "Stopped" in text


def test_fresh_heartbeat_is_not_red(tmp_path):
    text = rendered(tmp_path, status(age_s=10))
    assert "lv-stale" not in text and "checked 10 s ago" in text


def test_render_without_status_does_not_crash(tmp_path):
    text = rendered(tmp_path)
    assert "not started" in text.lower() and "Stopped" in text and "–" in text


def test_render_with_a_minimal_old_status_shows_dashes(tmp_path):
    old = {"running": True, "heartbeat": (NOW - timedelta(seconds=5)).isoformat()}
    text = rendered(tmp_path, old)
    assert "Running" in text and "–" in text  # no balance / strategy / session: dashes, no crash


def test_render_new_fields(tmp_path):
    session = {"name": "US open", "open_utc": "2026-01-12T14:30:00+00:00",
               "close_utc": "2026-01-12T21:00:00+00:00", "is_open": True}  # fmt: skip
    st = status(
        strategy="Opening-range breakout", risk_percent=0.25, session=session,
        started_at="2026-01-12T13:00:00+00:00", initial_balance=100_000.0, symbols=["US500"],
        setups={"US500": {"stage": "range_set", "detail": "range 100-110", "time": ""}},
    )  # fmt: skip
    text = rendered(tmp_path, st)
    for s in ("Opening-range breakout", "open, 6 h left", "14:00 CH", "range 100-110",
              "US open 15:30–22:00 CH", "Range set", "lv-step-done", "lv-step-current"):  # fmt: skip
        assert s in text


def test_paused_state_and_labels(tmp_path):
    write_status(tmp_path / "status.json", status(age_s=5))
    assert live.live_view(tmp_path, NOW)["state"] == "running"
    assert live.toggle_pause(tmp_path) is True and (tmp_path / "PAUSE").exists()
    view = live.live_view(tmp_path, NOW)
    assert view["state"] == "paused" and live.button_state(view)["pause_label"] == "Resume"
    assert live.toggle_pause(tmp_path) is False and not (tmp_path / "PAUSE").exists()
    write_status(tmp_path / "status.json", status(age_s=5, paused=True))
    assert live.live_view(tmp_path, NOW)["state"] == "paused"


def test_a_leftover_pause_file_is_ignored_when_stopped(tmp_path):
    (tmp_path / "PAUSE").touch()
    assert live.live_view(tmp_path, NOW)["state"] == "none"


def test_button_states(tmp_path):
    none = live.button_state(live.live_view(tmp_path, NOW))
    assert none == {"start_disabled": False, "pause_label": "Pause", "pause_disabled": True,
                    "stop_disabled": True, "emergency_disabled": True}  # fmt: skip
    write_status(tmp_path / "status.json", status(age_s=5))
    run = live.button_state(live.live_view(tmp_path, NOW))
    assert run["start_disabled"] and not run["pause_disabled"] and not run["stop_disabled"]
    assert not run["emergency_disabled"]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process flags")
def test_spawn_hides_the_console_window(tmp_path, monkeypatch):
    # DETACHED_PROCESS + the venv launcher opened an empty console; a hidden console does not
    seen = {}
    monkeypatch.setattr(live.subprocess, "Popen", lambda cmd, **kw: seen.update(kw))
    live._spawn_detached(["x"], tmp_path / "bot.log")
    flags = seen["creationflags"]
    assert flags & subprocess.CREATE_NO_WINDOW and flags & subprocess.CREATE_NEW_PROCESS_GROUP
    assert not flags & subprocess.DETACHED_PROCESS


def test_settings_follow_the_bot(tmp_path):
    idle = live.settings_state(live.live_view(tmp_path, NOW))
    assert idle == {"disabled": False, "risk": None, "stop": None, "symbols": None}
    write_status(tmp_path / "status.json", status(age_s=5, risk_percent=0.5, symbols=["US30"]))
    run = live.settings_state(live.live_view(tmp_path, NOW))
    assert run["disabled"] and run["risk"] == 0.5 and run["stop"] == 2.0
    assert run["symbols"] == ["US30"]
    write_status(tmp_path / "status.json", status(age_s=STALE_S + 5))
    assert live.settings_state(live.live_view(tmp_path, NOW))["disabled"] is False


def test_start_passes_the_settings_to_the_bot(tmp_path):
    calls = []
    clean = {"risk": 0.5, "daily_stop": 1.0, "symbols": ["US500"]}
    live.start_bot(tmp_path, NOW, spawn=lambda cmd, log: calls.append(cmd), settings=clean)
    assert calls[0][3:] == ["--symbols", "US500", "--risk", "0.5", "--daily-stop", "1"]


def test_start_removes_a_leftover_pause_file(tmp_path):
    (tmp_path / "PAUSE").touch()
    live.start_bot(tmp_path, NOW, spawn=lambda *a: None)
    assert not (tmp_path / "PAUSE").exists()


def test_usd_formatting():
    assert live.usd(100412.4) == "$100,412" and live.usd(-326.0, signed=True) == "-$326"
    assert live.usd(326.0, signed=True) == "+$326" and live.usd(None) == "–"
    assert live.usd("x") == "–"


def test_trades_figure_empty_and_filled():
    empty = live.trades_figure(live.lm.trade_strip([], 100_000.0, "all", NOW))
    assert len(empty.data) == 0 and "No trades" in empty.layout.annotations[0].text
    # no data: no axes with made-up ranges (-1..6), only the note
    assert empty.layout.xaxis.visible is False and empty.layout.yaxis.visible is False
    t = [{"symbol": "A", "exit_time": "2026-01-12T15:00:00+00:00", "money": -50.0, "r_net": -0.2},
         {"symbol": "A", "exit_time": "2026-01-12T16:00:00+00:00", "money": 80.0, "r_net": 0.3}]  # fmt: skip
    fig = live.trades_figure(live.lm.trade_strip(t, 100_000.0, "all", NOW))
    assert list(fig.data[0].marker.color) == ["#f6465d", "#2ebd85"] and len(fig.data) == 2
    assert fig.layout.xaxis.visible is not False and fig.layout.yaxis.visible is not False


def test_guard_bar_scale():
    bar = live.guard_bar(status(day_pl_percent=-2.5))
    assert bar["loss"] == 2.5 and bar["stop"] == 2.0 and bar["fraction"] == 1.0
    assert bar["level"] == "stopped"
    assert live.guard_bar(status(day_pl_percent=1.0))["fraction"] == 0.0
    assert live.guard_bar(status(day_pl_percent=-1.0))["level"] == "ok"


# --- the app ---------------------------------------------------------------------------------


def ids_of(component) -> set[str]:
    return set(re.findall(r'"id": "([^"]+)"', text_of(component)))


def test_app_routes_live_and_has_the_top_bar():
    page = app_module.page_for("/live", None)
    assert "lv-interval" in text_of(page)
    app = app_module.create_app()
    text = text_of(app.layout)
    for i in ("nav-chart", "nav-backtest", "nav-live", "nav-status", "nav-landed"):
        assert i in text
    assert "lv-interval" in text_of(app.validation_layout)


def test_live_page_has_connection_and_settings():
    ids = ids_of(live.layout())
    for i in ("tr-login", "tr-password", "tr-server", "tr-path", "tr-save", "tr-test", "tr-orders",
              "tr-tg-token", "tr-tg-chat", "lv-risk", "lv-daily-stop", "lv-symbols", "lv-start",
              "lv-pause", "lv-stop", "lv-emergency", "lv-range", "lv-trades"):  # fmt: skip
        assert i in ids


def _details(component, out=None):
    out = [] if out is None else out
    if isinstance(component, html.Details):
        out.append(component)
    kids = getattr(component, "children", None)
    for k in kids if isinstance(kids, list) else [kids]:
        if hasattr(k, "children"):
            _details(k, out)
    return out


def _summary(details) -> str:
    return text_of(details.children[0])


def test_connection_is_closed_by_default_whatever_the_bot_state(tmp_path):
    def conn_open(path):
        return getattr(live.layout(path, NOW).children[-1], "open", False)

    assert not conn_open(tmp_path)  # no status file
    write_status(tmp_path / "status.json", status(age_s=5))
    assert not conn_open(tmp_path)
    write_status(tmp_path / "status.json", status(age_s=5, connected=False))
    assert not conn_open(tmp_path)


def test_setup_in_progress_and_connection_are_closed_details(tmp_path):
    found = {_summary(d): d for d in _details(live.layout(tmp_path, NOW))}
    setup = next(d for t, d in found.items() if "Setup in progress" in t)
    conn = next(d for t, d in found.items() if "Connection" in t)
    for d in (setup, conn):
        assert not getattr(d, "open", False)
    assert "lv-setup" in ids_of(setup)
    assert {"tr-login", "tr-password", "tr-server", "tr-save"} <= ids_of(conn)


def test_chart_page_sweep_controls_moved_into_the_settings():
    from backtester.data.sources import DEFAULT_SOURCES
    from backtester.ui.pages import chart

    page = chart.layout(DEFAULT_SOURCES)
    ids = ids_of(page)
    assert not {"tb-sweep", "pop-sweep", "tr-open", "tr-modal"} & ids
    assert {"chart-sweep-tol", "chart-sweep-cancel", "chart-sweep-n", "chart-sweep-top",
            "chart-sweep-tweak"} <= ids  # fmt: skip
    text = text_of(page)
    # two collapsible blocks in the Settings popover: Chart Settings and Chart Overlays
    assert text.count('"type": "Details"') == 2 and "Account connection" not in text


def _nested_lists(node, path="root") -> list[str]:
    """Dash's renderer fails (React error 31) on a list inside a children list."""
    found = []
    children = getattr(node, "children", None)
    if isinstance(children, list):
        for i, child in enumerate(children):
            if isinstance(child, list):
                found.append(f"{path}[{i}]")
            else:
                found += _nested_lists(child, f"{path}[{i}]")
    elif children is not None and not isinstance(children, str | int | float):
        found += _nested_lists(children, path)
    return found


def test_no_nested_children_lists(tmp_path):
    write_status(
        tmp_path / "status.json",
        status(setups={"US500": {"stage": "entered", "detail": "x"}}, symbols=["US500"]),
    )
    assert _nested_lists(live.layout(tmp_path, NOW)) == []
    for piece in live.render(live.live_view(tmp_path, NOW), NOW).values():
        assert _nested_lists(piece) == []


# --- trades that open on the chart (ROADMAP 7.6) -----------------------------------------------


def links_in(component) -> list[str]:
    """Every dcc.Link href inside a component tree."""
    found = []
    if getattr(component, "href", None) is not None and type(component).__name__ == "Link":
        found.append(component.href)
    children = getattr(component, "children", None)
    for child in children if isinstance(children, list) else [children]:
        if child is not None and not isinstance(child, str | int | float):
            found += links_in(child)
    return found


def test_open_positions_link_to_the_chart_with_entry_and_sl_but_no_tp(tmp_path):
    from urllib.parse import parse_qs, urlparse

    pos = {"symbol": "US500", "side": "buy", "lots": 1.0, "entry": 7700.0, "sl": 7690.0,
           "floating_r": 0.4, "ticket": 1, "since": "2026-01-12T14:35:00+00:00"}  # fmt: skip
    write_status(tmp_path / "status.json", status(positions=[pos]))
    view = live.live_view(tmp_path, NOW)
    (href,) = links_in(live.render_positions(view))
    query = parse_qs(urlparse(href).query)
    assert query["symbol"] == ["US500"] and query["dir"] == ["long"] and query["tf"] == ["M1"]
    assert query["ep"] == ["7700.0"] and query["sl"] == ["7690.0"]
    assert "tp" not in query and "exit" not in query  # the bot records no take profit


def test_a_position_without_a_time_has_no_link(tmp_path):
    write_status(tmp_path / "status.json", status())  # the default position has since ""
    assert links_in(live.render_positions(live.live_view(tmp_path, NOW))) == []


def closed(**kw):
    base = {"symbol": "US500", "side": "sell", "entry_time": "2026-01-12T14:35:00+00:00",
            "exit_time": "2026-01-12T14:50:00+00:00", "entry_fill": "7700.0", "sl": "7710.0",
            "exit_price": "7690.0", "money": 250.0, "r_net": 1.0}  # fmt: skip
    return {**base, **kw}


def test_closed_trades_table_links_each_trade_to_the_chart():
    table = live.render_closed([closed(), closed(symbol="NAS100", side="buy", sl="7690.0")])
    hrefs = links_in(table)
    assert len(hrefs) == 2 and "symbol=NAS100" in hrefs[0] + hrefs[1]
    assert (
        "exit=2026-01-12T14%3A50%3A00Z" in hrefs[0] or "exit=2026-01-12T14%3A50%3A00Z" in hrefs[1]
    )
    text = text_of(table)
    assert "15:35" in text  # 14:35 UTC = 15:35 CH
    assert live.render_closed([]).children == "none yet"


def test_closed_trade_without_an_order_has_no_link_but_still_a_row():
    table = live.render_closed([closed(sl="")])
    assert links_in(table) == [] and "US500" in text_of(table)


def test_the_bars_of_the_trades_figure_carry_the_chart_link():
    rows = [closed(), closed(exit_time="2026-01-12T15:30:00+00:00")]
    fig = live.trades_figure(live.lm.trade_strip(rows, 100_000.0, "all", NOW), rows)
    assert len(fig.data[0].customdata) == 2
    assert all(str(link).startswith("/?symbol=US500") for link in fig.data[0].customdata)


# --- 13.4b: the bot must outlive the app process ---------------------------------------------


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process flags")
def test_spawn_breaks_away_from_the_apps_job_and_process_tree(tmp_path, monkeypatch):
    # Restarting the app killed the bot: it was the app's child (taskkill /T) and in the app's
    # job object. A launcher that exits starts it (no live parent), with BREAKAWAY_FROM_JOB.
    calls = []
    monkeypatch.setattr(live.subprocess, "Popen", lambda cmd, **kw: calls.append((cmd, kw)))
    live._spawn_detached(["bot.exe", "-m", "bot", "--risk", "0.25"], tmp_path / "bot.log")
    ((cmd, kw),) = calls
    assert kw["creationflags"] & subprocess.CREATE_BREAKAWAY_FROM_JOB
    assert kw["creationflags"] & subprocess.CREATE_NO_WINDOW
    assert cmd[0] == sys.executable and cmd[1] == "-c"  # the launcher
    assert cmd[3:] == [str(tmp_path / "bot.log"), "bot.exe", "-m", "bot", "--risk", "0.25"]
    assert str(subprocess.CREATE_BREAKAWAY_FROM_JOB) in cmd[2] or "0x01000000" in cmd[2]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process flags")
def test_spawn_falls_back_when_the_job_forbids_breakaway(tmp_path, monkeypatch):
    calls = []

    def popen(cmd, **kw):
        calls.append(kw["creationflags"])
        if kw["creationflags"] & subprocess.CREATE_BREAKAWAY_FROM_JOB:
            raise PermissionError("access denied")
        return object()

    monkeypatch.setattr(live.subprocess, "Popen", popen)
    live._spawn_detached(["x"], tmp_path / "bot.log")
    assert len(calls) == 2 and not calls[1] & subprocess.CREATE_BREAKAWAY_FROM_JOB
    assert calls[1] & subprocess.CREATE_NO_WINDOW


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process flags")
def test_spawned_command_really_runs_detached_from_the_caller(tmp_path):
    import time

    marker = tmp_path / "ran.txt"
    code = f"import time; time.sleep(1); open({str(marker)!r}, 'w').write('x')"
    live._spawn_detached([sys.executable, "-c", code], tmp_path / "bot.log")
    for _ in range(100):
        if marker.exists():
            break
        time.sleep(0.2)
    assert marker.exists()
