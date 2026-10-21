"""Bot trades overlay: the demo bot's trades on the chart. Spec: live-trading.md > Bot data and
chart (ROADMAP 7.8c).

Shows the trades of the bot since its **current** start (`results/live/status.json` `started_at`)
on the chart's symbol: closed ones from `<day>/trades.csv`, open ones from `positions`. Each is
drawn like a focused order (`trade_focus.order_drawings`: entry, SL, TP if any, exit marker); an
open position is dashed and labelled "open". The bot has no TP (strategy 6 exits at the session
end), so none is drawn. Missing or broken files give an empty overlay.

No lookahead (replay): a trade appears at the close of its entry candle; only the candles up to
the cursor are given to the drawing, so an exit after the cursor is not shown yet.

The overlay is on by default for the bot's symbols, once per symbol and browser (`default_selection`):
a symbol is offered once, so the user's later choice stays.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from backtester.detectors.base import Event
from backtester.engine.replay import Replay
from backtester.live.status import STATUS_NAME, read_status
from backtester.paths import RESULTS_DIR
from backtester.ui import live_model, trade_focus
from backtester.ui.drawing import Drawing, Label, Line
from backtester.ui.overlays import OverlayContext, OverlaySettings, OverlayType, register

LIVE_DIR = RESULTS_DIR / "live"
KEY = "bot"
OPEN_TEXT = " (open)"


@dataclass(frozen=True, slots=True)
class BotTrade(Event):
    """One bot order on the loaded candles; `opens` are the chart candles' open times."""

    order: dict
    opens: tuple[datetime, ...]


def bot_symbols(out_dir: Path = LIVE_DIR) -> tuple[str, ...]:
    """The symbols of the running (or last) bot from status.json; () when unknown."""
    symbols = (read_status(Path(out_dir) / STATUS_NAME) or {}).get("symbols")
    if not isinstance(symbols, list):
        return ()
    return tuple(s for s in symbols if isinstance(s, str))


def bot_orders(out_dir: Path, symbol: str) -> list[dict]:
    """Orders of `symbol` entered since the bot's current start, oldest first: its closed trades
    plus its open positions. [] without a readable status.json / `started_at`."""
    status = read_status(Path(out_dir) / STATUS_NAME)
    started = live_model._parse_utc((status or {}).get("started_at"))
    if started is None:
        return []
    positions = status.get("positions")
    rows = [t for t in live_model.read_trades(out_dir) if t.get("symbol") == symbol]
    rows += [p for p in positions if isinstance(p, dict)] if isinstance(positions, list) else []
    orders = [
        o
        for row in rows
        if row.get("symbol") == symbol
        and (o := trade_focus.live_order(row)) is not None
        and trade_focus._time(o["entry_time"]) >= started
    ]
    return sorted(orders, key=lambda o: o["entry_time"])


def detect_bot_trades(
    replay: Replay, settings: OverlaySettings | None = None, out_dir: Path = LIVE_DIR
) -> list[BotTrade]:
    opens = tuple(c.ts for c in replay.view(len(replay) - 1))
    if not opens:
        return []
    last_close = opens[-1] + replay.timeframe.duration
    out = []
    for order in bot_orders(out_dir, replay.symbol):
        entry = trade_focus._time(order["entry_time"])
        if not opens[0] < entry <= last_close:
            continue
        x = trade_focus._containing(opens, entry)
        out.append(BotTrade(x, opens[x] + replay.timeframe.duration, order, opens))
    return out


def draw_bot_trades(events: Sequence[BotTrade], ctx: OverlayContext) -> list[Drawing]:
    drawings: list[Drawing] = []
    for e in events:
        shown = e.opens[: ctx.cursor + 1]  # an exit after the cursor is not known yet
        found = trade_focus.order_drawings(e.order, shown, ctx.timeframe, ctx.digits, ctx.config)
        if e.order["exit_time"] is not None:
            drawings += found
            continue
        for d in found:  # an open position: dashed lines, "open" on the labels
            if isinstance(d, Line):
                d = replace(d, dash="dash")
            elif isinstance(d, Label):
                d = replace(d, text=d.text + OPEN_TEXT) if d.text.startswith("Entry") else d
            drawings.append(d)
    return drawings


def default_selection(
    symbol: str | None,
    types: Sequence[str],
    master: Sequence[str],
    seen: Sequence[str],
    symbols: Sequence[str],
) -> tuple[list[str], list[str], list[str]] | None:
    """(overlays switch, overlay types, symbols already offered) after the chart opens `symbol`,
    or None when nothing changes: the overlay is switched on once for each bot symbol."""
    if not symbol or symbol not in symbols or symbol in seen:
        return None
    return ["on"], [*types, KEY] if KEY not in types else list(types), [*seen, symbol]


BOT = register(
    OverlayType(
        KEY,
        "Bot trades",
        lambda replay, settings: detect_bot_trades(replay, settings),
        draw_bot_trades,
        order="7.8",
    )
)
