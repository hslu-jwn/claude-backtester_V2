"""Pure helpers of the /live page and the top bar (ROADMAP 7.3): no Dash, no bot."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

import pytest

from backtester.live.bot import FORWARD_SYMBOLS, BotConfig
from backtester.live.status import STALE_S
from backtester.ui import live_model as m

NOW = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)


def iso(**kw) -> str:
    return (NOW + timedelta(**kw)).isoformat()


# --- durations and countdown ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("seconds", "text"),
    [(0, "<1 min"), (59, "<1 min"), (60, "1 min"), (47 * 60 + 5, "47 min"),
     (2 * 3600 + 14 * 60, "2 h 14 min"), (3 * 3600, "3 h"), (26 * 3600 + 5 * 60, "1 d 2 h")],
)  # fmt: skip
def test_fmt_duration(seconds, text):
    assert m.fmt_duration(seconds) == text


def test_countdown_before_the_window():
    s = {"name": "US open", "open_utc": iso(hours=2, minutes=14, seconds=10),
         "close_utc": iso(hours=4), "is_open": False}  # fmt: skip
    assert m.countdown_text(s, NOW) == "US open in 2 h 14 min"


def test_countdown_inside_the_window():
    s = {"name": "US open", "open_utc": iso(hours=-1), "close_utc": iso(minutes=47, seconds=30),
         "is_open": True}  # fmt: skip
    assert m.countdown_text(s, NOW) == "open, 47 min left"


def test_countdown_missing_or_garbage():
    assert m.countdown_text(None, NOW) == "–"
    assert m.countdown_text({}, NOW) == "–"
    assert m.countdown_text({"open_utc": "x", "close_utc": "y"}, NOW) == "–"


def test_countdown_uses_flag_when_times_are_missing():
    assert m.countdown_text({"is_open": True}, NOW) == "open"


def test_countdown_stale_open_time_in_the_past():
    s = {"name": "US open", "open_utc": iso(seconds=-5), "close_utc": iso(hours=1),
         "is_open": False}  # fmt: skip
    assert m.countdown_text(s, NOW).startswith("open, ")  # the times decide, not the old flag


def test_window_text_in_swiss_time():
    # 2026-01-12 14:30 UTC = 15:30 CET (user 2026-10-17: Swiss time on the Live page)
    s = {"name": "US open", "open_utc": "2026-01-12T14:30:00+00:00",
         "close_utc": "2026-01-12T21:00:00+00:00"}  # fmt: skip
    assert m.window_text(s) == "US open 15:30–22:00 CH"
    assert m.window_text(None) == "–"


def test_clock_ch():
    assert m.clock_ch("2026-07-01T12:41:00+00:00") == "14:41 CH"  # CEST
    assert m.clock_ch("2026-01-12T12:41:00+00:00") == "13:41 CH"  # CET
    assert m.clock_ch("") == "–"
    assert m.clock_ch("garbage") == "–"
    assert m.clock_ch("2026-07-01T12:41:00") == "–"  # naive time: not trusted


def test_hm_ch_for_tables():
    assert m.hm_ch("2026-07-01T12:41:05+00:00") == "14:41"
    assert m.hm_ch("2026-07-01T12:41:05+00:00", seconds=True) == "14:41:05"
    assert m.hm_ch("") == ""
    assert m.hm_ch("2026-07-01T12:41:05") == ""  # naive time: not trusted


# --- heartbeat ---------------------------------------------------------------------------------


def test_heartbeat_text():
    assert m.heartbeat_text(4) == "checked 4 s ago"
    assert m.heartbeat_text(125) == "checked 2 min ago"
    assert m.heartbeat_text(None) == "–"
    assert m.heartbeat_text(-3) == "checked 0 s ago"  # clock skew


def test_heartbeat_stale():
    assert m.heartbeat_stale(STALE_S + 1) and not m.heartbeat_stale(STALE_S)
    assert m.heartbeat_stale(None)


# --- bars --------------------------------------------------------------------------------------


def test_ftmo_bars():
    status = {"equity": 96_000.0, "initial_balance": 100_000.0, "day_pl_percent": -2.5,
              "guard": {"ftmo_daily_percent": 5.0, "ftmo_max_percent": 10.0}}  # fmt: skip
    daily, mx = m.ftmo_bars(status)
    assert daily["used"] == 2.5 and daily["fraction"] == 0.5 and daily["left"] == 2.5
    assert mx["used"] == 4.0 and mx["fraction"] == 0.4 and mx["left"] == 6.0
    assert daily["level"] == "warn" and mx["level"] == "ok"


def test_ftmo_bars_gain_and_breach_and_missing():
    gain = m.ftmo_bars({"equity": 105_000.0, "initial_balance": 100_000.0, "day_pl_percent": 3.0})
    assert gain[0]["used"] == 0 and gain[1]["used"] == 0 and gain[0]["fraction"] == 0
    breach = m.ftmo_bars({"equity": 89_000.0, "initial_balance": 100_000.0,
                          "day_pl_percent": -6.0})  # fmt: skip
    assert breach[0]["level"] == "breach" and breach[0]["fraction"] == 1.0
    assert breach[1]["level"] == "breach" and breach[1]["left"] == 0
    none = m.ftmo_bars({})
    assert none[0]["used"] is None and none[1]["used"] is None  # shown as "–"
    assert none[0]["fraction"] == 0 and none[0]["limit"] == 5.0 and none[1]["limit"] == 10.0


def test_today_bar_against_the_daily_stop():
    gain = m.today_bar({"day_pl_percent": 0.33, "guard": {"daily_stop_percent": 2.0}})
    assert gain["fraction"] == 0 and gain["level"] == "ok" and gain["stop"] == 2.0
    loss = m.today_bar({"day_pl_percent": -1.0, "guard": {"daily_stop_percent": 2.0}})
    assert loss["fraction"] == 0.5 and loss["level"] == "ok"
    hit = m.today_bar({"day_pl_percent": -2.0, "guard": {"daily_stop_percent": 2.0}})
    assert hit["fraction"] == 1.0 and hit["level"] == "stopped"
    assert m.today_bar({})["stop"] == 2.0  # the GuardConfig default
    assert m.today_bar({"day_pl_percent": "x"})["fraction"] == 0


# --- setup funnel -----------------------------------------------------------------------------


def test_funnel_marks_done_and_current():
    rows = m.funnel_rows({"stage": "waiting_breakout", "detail": "range 100-110"})
    states = [r["state"] for r in rows]
    assert [r["key"] for r in rows] == list(m.STAGES)
    assert states == ["done", "done", "done", "current", "todo", "todo", "todo"]
    assert rows[3]["detail"] == "range 100-110" and rows[0]["detail"] == ""


def test_funnel_done_stage_is_all_ticked():
    assert {r["state"] for r in m.funnel_rows({"stage": "done"})} == {"done"}


def test_funnel_unknown_or_missing_stage():
    assert {r["state"] for r in m.funnel_rows(None)} == {"todo"}
    assert {r["state"] for r in m.funnel_rows({"stage": "nonsense"})} == {"todo"}
    assert {r["state"] for r in m.funnel_rows({})} == {"todo"}


# --- trades -------------------------------------------------------------------------------------


def write_trades(tmp_path, day, rows):
    folder = tmp_path / day
    folder.mkdir()
    cols = ["symbol", "exit_time", "r_net", "money", "risk_money"]
    lines = [",".join(cols)] + [",".join(str(r[c]) for c in cols) for r in rows]
    (folder / "trades.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def trade(day, hh, money, r=0.0, symbol="US500"):
    return {"symbol": symbol, "exit_time": f"{day}T{hh}:00:00+00:00", "r_net": r, "money": money,
            "risk_money": 250}  # fmt: skip


def test_read_trades_across_day_folders_sorted(tmp_path):
    write_trades(
        tmp_path, "2026-01-12", [trade("2026-01-12", "16", 300), trade("2026-01-12", "15", -100)]
    )
    write_trades(tmp_path, "2026-01-09", [trade("2026-01-09", "15", 50)])
    (tmp_path / "junk").mkdir()
    (tmp_path / "junk" / "trades.csv").write_text("x\n")
    got = m.read_trades(tmp_path)
    assert [t["money"] for t in got] == [50.0, -100.0, 300.0]


def test_read_trades_empty_and_broken(tmp_path):
    assert m.read_trades(tmp_path) == []
    assert m.read_trades(tmp_path / "nope") == []
    write_trades(tmp_path, "2026-01-12", [trade("2026-01-12", "15", "oops")])
    (tmp_path / "2026-01-11").mkdir()
    (tmp_path / "2026-01-11" / "trades.csv").write_bytes(b"\xff\xfe garbage")
    assert m.read_trades(tmp_path) == []


def test_strip_percent_of_balance_and_balance_line():
    trades = [
        {"symbol": "A", "exit_time": "2026-01-12T15:00:00+00:00", "money": -1000.0, "r_net": -1.0},
        {"symbol": "B", "exit_time": "2026-01-12T16:00:00+00:00", "money": 989.0, "r_net": 1.0},
    ]
    s = m.trade_strip(trades, 100_000.0, "all", NOW)
    assert s["pct"][0] == -1.0  # of the balance before each trade: 100000, 99000
    assert s["pct"][1] == pytest.approx(989 / 99_000 * 100)
    assert s["balance"] == [99_000.0, 99_989.0]
    assert s["total"] == -11.0


def test_strip_day_week_all_windows():
    old = "2026-01-01T15:00:00+00:00"
    wk = "2026-01-08T15:00:00+00:00"
    today = "2026-01-12T15:00:00+00:00"
    trades = [
        {"symbol": "A", "exit_time": t, "money": 100.0, "r_net": 0.4} for t in (old, wk, today)
    ]
    day = m.trade_strip(trades, 100_000.0, "day", NOW)
    week = m.trade_strip(trades, 100_000.0, "week", NOW)
    allr = m.trade_strip(trades, 100_000.0, "all", NOW)
    assert (len(day["pct"]), len(week["pct"]), len(allr["pct"])) == (1, 2, 3)
    assert day["balance"] == [100_300.0]  # earlier trades still count toward the balance
    assert m.trade_strip(trades, 100_000.0, "bogus", NOW)["pct"] == allr["pct"]


def test_strip_empty_and_no_initial_balance():
    empty = m.trade_strip([], 100_000.0, "all", NOW)
    assert empty == {"pct": [], "balance": [], "labels": [], "total": 0.0}
    t = [{"symbol": "A", "exit_time": "2026-01-12T15:00:00+00:00", "money": 50.0, "r_net": 0.2}]
    s = m.trade_strip(t, None, "all", NOW)
    assert s["balance"] == [50.0] and s["pct"] == [0.0]  # no base: no percent, P/L only
    assert m.trade_strip(t, -5.0, "all", NOW)["pct"] == [0.0]


def test_strip_bad_times_are_skipped_in_windows():
    t = [{"symbol": "A", "exit_time": "garbage", "money": 50.0, "r_net": 0.2}]
    assert m.trade_strip(t, 100_000.0, "day", NOW)["pct"] == []
    assert len(m.trade_strip(t, 100_000.0, "all", NOW)["pct"]) == 1


# --- settings ----------------------------------------------------------------------------------


def test_defaults_come_from_the_configs():
    assert m.DEFAULT_RISK == BotConfig.risk_percent
    assert m.DEFAULT_SYMBOLS == FORWARD_SYMBOLS
    assert m.MAX_RISK_PERCENT == 2.0 and m.MAX_DAILY_STOP_PERCENT == 5.0


def test_validate_settings_ok():
    clean, err = m.validate_settings(0.25, 2.0, ["US500", "NAS100"])
    assert err == "" and clean == {"risk": 0.25, "daily_stop": 2.0, "symbols": ["US500", "NAS100"]}
    assert m.validate_settings("1.5", "3", ["US30"])[0]["risk"] == 1.5  # numbers typed as text


@pytest.mark.parametrize(
    ("risk", "stop", "symbols", "word"),
    [(0, 2, ["A"], "risk"), (-1, 2, ["A"], "risk"), (2.01, 2, ["A"], "risk"),
     (None, 2, ["A"], "risk"), ("abc", 2, ["A"], "risk"), (float("nan"), 2, ["A"], "risk"),
     (1, 0, ["A"], "daily"), (1, 5.01, ["A"], "daily"), (1, None, ["A"], "daily"),
     (1, 2, [], "symbol"), (1, 2, None, "symbol")],
)  # fmt: skip
def test_validate_settings_rejects(risk, stop, symbols, word):
    clean, err = m.validate_settings(risk, stop, symbols)
    assert clean is None and word in err.lower()


def test_validate_settings_limits_are_inclusive():
    assert m.validate_settings(2.0, 5.0, ["A"])[1] == ""


def test_start_command():
    clean = {"risk": 0.5, "daily_stop": 1.5, "symbols": ["US500", "NAS100"]}
    cmd = m.start_command(clean)
    assert cmd[0] == sys.executable
    assert cmd[1:] == ["-m", "backtester.live.bot", "--symbols", "US500", "NAS100",
                       "--risk", "0.5", "--daily-stop", "1.5"]  # fmt: skip
    assert m.start_command(None)[1:] == ["-m", "backtester.live.bot"]


# --- state and top bar ---------------------------------------------------------------------------


def hb(age=10.0, **kw):
    return {"running": True, "connected": True, "heartbeat": iso(seconds=-age), **kw}


def test_bot_state():
    assert m.bot_state(None, NOW) == "none"
    assert m.bot_state(hb(STALE_S + 1), NOW) == "stale"
    assert m.bot_state(hb(5, running=False), NOW) == "stopped"
    assert m.bot_state(hb(5), NOW) == "running"
    assert m.bot_state(hb(5, paused=True), NOW) == "paused"
    assert m.bot_state({"running": True}, NOW) == "stale"  # no heartbeat at all


def test_nav_view():
    assert m.nav_view(hb(5), NOW) == {
        "live": True, "text": "MT5 connected · bot running", "level": "ok"
    }  # fmt: skip
    assert m.nav_view(hb(5, paused=True), NOW)["text"] == "MT5 connected · bot paused"
    assert m.nav_view(hb(5, connected=False), NOW)["level"] == "warn"
    for status in (None, hb(STALE_S + 5), hb(5, running=False)):
        v = m.nav_view(status, NOW)
        assert v["live"] is False and v["level"] == "idle"


def test_landing_path():
    running = hb(5)
    assert m.landing_path("/", False, running, NOW) == "/live"
    assert m.landing_path("/", True, running, NOW) is None  # only the first load of a session
    assert m.landing_path("/", False, None, NOW) is None
    assert m.landing_path("/results/x", False, running, NOW) is None
    assert m.landing_path("/live", False, running, NOW) is None
    assert m.landing_path("/", False, hb(STALE_S + 5), NOW) is None


# --- trades that open on the chart (ROADMAP 7.6) -----------------------------------------------


def write_full_trades(tmp_path, day, rows):
    from backtester.live.bot import TRADE_COLUMNS

    folder = tmp_path / day
    folder.mkdir()
    lines = [",".join(TRADE_COLUMNS)]
    lines += [",".join(str(r.get(c, "")) for c in TRADE_COLUMNS) for r in rows]
    (folder / "trades.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def full_trade(**kw):
    base = {"symbol": "US500", "side": "sell", "ticket": 7, "lots": 1.0,
            "entry_time": "2026-01-12T14:35:00+00:00", "exit_time": "2026-01-12T15:00:00+00:00",
            "entry_fill": 7700.0, "exit_price": 7690.0, "sl": 7710.0, "exit_reason": "signal",
            "r_net": 1.0, "money": 250.0, "risk_money": 250.0}  # fmt: skip
    return {**base, **kw}


def test_read_trades_keeps_what_the_chart_needs_for_the_order(tmp_path):
    write_full_trades(tmp_path, "2026-01-12", [full_trade()])
    (got,) = m.read_trades(tmp_path)
    assert (got["side"], got["entry_time"], got["entry_fill"], got["sl"], got["exit_price"]) == (
        "sell", "2026-01-12T14:35:00+00:00", "7700.0", "7710.0", "7690.0"
    )  # fmt: skip


def test_window_trades_follow_the_strips_windows():
    old = {"symbol": "A", "exit_time": "2026-01-01T15:00:00+00:00", "money": 1.0, "r_net": 0.1}
    today = {"symbol": "B", "exit_time": "2026-01-12T14:00:00+00:00", "money": 1.0, "r_net": 0.1}
    assert m.window_trades([old, today], "day", NOW) == [today]
    assert m.window_trades([old, today], "all", NOW) == [old, today]
    assert m.window_trades([today, old], "all", NOW) == [old, today]  # oldest exit first
    assert m.window_trades([old, today], "bogus", NOW) == [old, today]
