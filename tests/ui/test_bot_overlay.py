"""Bot trades overlay: the demo bot's trades since its current start on the chart (ROADMAP 7.8c).
Spec: live-trading.md > Bot data and chart."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

from conftest import build_series
from overlay_helpers import by_layer

from backtester.core.models import Timeframe
from backtester.engine.replay import Replay
from backtester.live.bot import TRADE_COLUMNS
from backtester.ui import bot_overlay, trade_focus
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.drawing import Line, Marker
from backtester.ui.overlays import OVERLAYS, OverlayContext, visible_events

START = datetime(2026, 10, 21, 13, 0, tzinfo=UTC)
STARTED = "2026-10-21T13:30:00+00:00"


def write_status(out_dir, **fields):
    out_dir.mkdir(parents=True, exist_ok=True)
    status = {"started_at": STARTED, "symbols": ["US500", "NAS100"], "positions": [], **fields}
    (out_dir / "status.json").write_text(json.dumps(status), encoding="utf-8")


def write_trades(out_dir, day, rows):
    folder = out_dir / day
    folder.mkdir(parents=True, exist_ok=True)
    lines = [",".join(TRADE_COLUMNS)]
    for r in rows:
        lines.append(",".join(str(r.get(c, "0")) for c in TRADE_COLUMNS))
    (folder / "trades.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def closed(symbol, entry, exit_, side="sell", fill=100.0, sl=101.0, exit_price=99.0):
    return {
        "symbol": symbol, "side": side, "entry_time": entry, "exit_time": exit_,
        "entry_fill": fill, "sl": sl, "exit_price": exit_price, "money": 10, "r_net": 1,
    }  # fmt: skip


def position(symbol="US500", since="2026-10-21T14:06:00+00:00"):
    return {"symbol": symbol, "side": "sell", "entry": 100.0, "sl": 101.0, "ticket": 7,
            "since": since}  # fmt: skip


def replay(symbol="US500", n=120):
    ohlc = [(100.0, 100.5, 99.5, 100.0)] * n
    return Replay(build_series(ohlc, Timeframe.M1, START, symbol))


def one_closed(tmp_path):
    write_status(tmp_path)
    write_trades(tmp_path, "2026-10-21", [
        closed("US500", "2026-10-21T13:10:00+00:00", "2026-10-21T13:20:00+00:00"),  # before start
        closed("US500", "2026-10-21T13:40:00+00:00", "2026-10-21T13:50:00+00:00"),
        closed("NAS100", "2026-10-21T13:40:00+00:00", "2026-10-21T13:50:00+00:00"),  # other symbol
    ])  # fmt: skip


# --- which trades ----------------------------------------------------------------------------


def test_only_trades_since_the_current_start_of_this_symbol(tmp_path):
    one_closed(tmp_path)
    orders = bot_overlay.bot_orders(tmp_path, "US500")
    assert [o["entry_time"] for o in orders] == ["2026-10-21T13:40:00Z"]
    assert orders[0]["exit"] == 99.0


def test_open_position_is_an_order_without_exit(tmp_path):
    write_status(tmp_path, positions=[position(), position("NAS100")])
    orders = bot_overlay.bot_orders(tmp_path, "US500")
    assert len(orders) == 1 and orders[0]["exit_time"] is None and orders[0]["tp"] is None


def test_open_position_before_start_is_skipped(tmp_path):
    write_status(tmp_path, positions=[position(since="2026-10-21T13:00:00+00:00")])
    assert bot_overlay.bot_orders(tmp_path, "US500") == []


def test_missing_or_broken_files_give_nothing(tmp_path):
    assert bot_overlay.bot_orders(tmp_path / "nope", "US500") == []
    (tmp_path / "status.json").write_text("{broken", encoding="utf-8")
    assert bot_overlay.bot_orders(tmp_path, "US500") == []
    write_status(tmp_path, started_at="yesterday")
    assert bot_overlay.bot_orders(tmp_path, "US500") == []
    write_status(tmp_path)
    (tmp_path / "2026-10-21").mkdir()
    (tmp_path / "2026-10-21" / "trades.csv").write_bytes(b"\xff\xfe junk")
    assert bot_overlay.bot_orders(tmp_path, "US500") == []
    write_status(tmp_path, positions=["junk", {"symbol": "US500"}])
    assert bot_overlay.bot_orders(tmp_path, "US500") == []


def test_bot_symbols_from_status(tmp_path):
    assert bot_overlay.bot_symbols(tmp_path) == ()
    write_status(tmp_path)
    assert bot_overlay.bot_symbols(tmp_path) == ("US500", "NAS100")
    write_status(tmp_path, symbols="oops")
    assert bot_overlay.bot_symbols(tmp_path) == ()


# --- drawing ---------------------------------------------------------------------------------


def ctx_for(rp, cursor=None):
    return OverlayContext(
        rp.symbol, len(rp) - 1 if cursor is None else cursor, 0, DEFAULT_CONFIG, rp.timeframe
    )


def test_closed_trade_draws_entry_sl_and_exit_marker(tmp_path):
    one_closed(tmp_path)
    rp = replay()
    events = bot_overlay.detect_bot_trades(rp, out_dir=tmp_path)
    assert len(events) == 1 and events[0].confirmed_index == 39  # candle closing 13:40
    layers = by_layer(bot_overlay.draw_bot_trades(events, ctx_for(rp)))
    assert any(isinstance(d, Marker) for d in layers["Order exit"])
    assert all(d.dash == "solid" for d in layers["Order level"] if isinstance(d, Line))


def test_open_position_is_dashed_and_marked_open(tmp_path):
    write_status(tmp_path, positions=[position()])
    rp = replay()
    events = bot_overlay.detect_bot_trades(rp, out_dir=tmp_path)
    layers = by_layer(bot_overlay.draw_bot_trades(events, ctx_for(rp)))
    assert "Order exit" not in layers
    assert all(d.dash == "dash" for d in layers["Order level"])
    assert any("open" in d.text for d in layers["Order label"])


def test_no_future_exit_before_the_cursor(tmp_path):
    one_closed(tmp_path)
    rp = replay()
    events = bot_overlay.detect_bot_trades(rp, out_dir=tmp_path)
    assert visible_events(events, 30) == []  # before the entry candle closed
    layers = by_layer(bot_overlay.draw_bot_trades(events, ctx_for(rp, cursor=45)))
    assert "Order exit" not in layers  # the exit (13:50) is after the cursor


def test_other_symbol_or_range_is_empty(tmp_path):
    one_closed(tmp_path)
    assert bot_overlay.detect_bot_trades(replay("GBPJPY"), out_dir=tmp_path) == []
    late = Replay(
        build_series([(1, 2, 0.5, 1)] * 10, Timeframe.M1, START + timedelta(days=1), "US500")
    )
    assert bot_overlay.detect_bot_trades(late, out_dir=tmp_path) == []


def test_overlay_is_registered():
    assert bot_overlay.BOT.key in OVERLAYS


# --- on by default for the bot's symbols -----------------------------------------------------


def test_default_on_once_per_bot_symbol():
    f = bot_overlay.default_selection
    assert f("US500", ["swings"], [], [], ("US500",)) == (["on"], ["swings", "bot"], ["US500"])
    assert f("US500", [], ["on"], ["US500"], ("US500",)) is None  # offered before: user's choice
    assert f("XAUUSD", [], [], [], ("US500",)) is None
    assert f("US500", ["bot"], ["on"], [], ("US500",)) == (["on"], ["bot"], ["US500"])
    assert f(None, [], [], [], ("US500",)) is None


# --- focus on a live (open) position ---------------------------------------------------------


def test_todays_live_position_focus_finds_its_days():
    focus = trade_focus.focus_from_order(
        trade_focus.live_order(position()), trade_focus.LIVE_TIMEFRAME
    )
    today = date(2026, 10, 21)
    cached = [today - timedelta(days=i) for i in (3, 2, 1, 0)]
    found = trade_focus.focus_dates(cached, focus, DEFAULT_CONFIG)
    assert found is not None and found[1] == today.isoformat()
    assert trade_focus.focus_dates(cached[:-1], focus, DEFAULT_CONFIG) is None
