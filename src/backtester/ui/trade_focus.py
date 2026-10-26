"""Open one order on the chart (ROADMAP 7.6). No Dash, no MT5: pure and unit-tested
(`tests/ui/test_trade_focus.py`).

A trade of a backtest (results page, chart side panel) or a live trade (Live page) opens the chart
on its symbol and timeframe, scrolled to the trade, and draws only that **order**: a TradingView
position tool (entry, SL zone red, TP zone green) from the entry candle to the exit candle (to the
last candle while the trade is open), with the prices labelled. The strategy is not run, no overlay
is switched on.

- The **order** is a JSON dict (`make_order`): symbol, direction, entry_time (UTC, the CLOSE time of
  the entry candle, as everywhere in the engine), entry price, sl, tp (None: no take profit) and,
  for a closed trade, exit_time / exit price. It travels in the link (`order_link`, keys `symbol`,
  `tf`, `dir`, `entry`, `ep`, `sl`, `tp`, `exit`, `xp`) and in the chart's `chart-focus` /
  `chart-order` stores. Links of the older form (symbol, from, to, t0, t1: no order) still open the
  chart on that trade's days.
- The **timeframe** is the strategy's own base timeframe from the run's settings.json
  (`run_timeframe`; opening-range breakout: 1m, strategy 1: 5m); a live trade uses the bot's
  (`LIVE_TIMEFRAME`).
- The **days** to load are the trade's days plus a margin of `MARGIN_CANDLES` candles on each side
  (`focus_dates`), cut to the run of cached days around the entry and to the candle limit. A trade
  on a day that is not cached has no days: the chart says so.
- The **drawing** (`order_drawings`) puts the order on the candles that are loaded: x is the
  candle index, the entry on the candle that CLOSED at the entry time (the last candle opening
  before it), the exit likewise.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, urlencode

from backtester.analytics.records import TradeRecord
from backtester.core.models import Timeframe
from backtester.data.resample import supported
from backtester.data.sources import cached_block
from backtester.settings import from_dict, to_json
from backtester.strategy.opening_range.strategy import OpeningRange
from backtester.strategy.registry import REGISTRY, make_strategy
from backtester.ui.chart_config import ChartConfig
from backtester.ui.chart_data import encode
from backtester.ui.drawing import Box, Drawing, Label, Line, Marker
from backtester.ui.numbers import _number

DEFAULT_TIMEFRAME = Timeframe.M5.name  # a run whose settings can't be read
LIVE_TIMEFRAME = OpeningRange.base_timeframe.name  # the demo bot trades the opening-range breakout
MARGIN_CANDLES = 300  # candles loaded beyond the trade on each side (scrolling loads more)
MIN_MARGIN_DAYS = 1
MAX_RUN_ORDERS = 400  # the run's trades drawn light at once (no focused trade)
OVERLAY = "order"  # the drawings' overlay name (their `o` field in the payload)
LONG, SHORT = "long", "short"
_SIDES = {"buy": LONG, "sell": SHORT, LONG: LONG, SHORT: SHORT}

# order drawing: level lines, label size
LINE_WIDTH = 1
LABEL_SIZE = 11
EXIT_MARKER_SIZE = 7
EXIT_COLOR = "#2962ff"
EXIT_OUTLINE = 2


# --- the order -----------------------------------------------------------------------------------


def _utc(t: datetime) -> datetime:
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t.astimezone(UTC)


def _text(t: datetime) -> str:
    return _utc(t).strftime("%Y-%m-%dT%H:%M:%SZ")


def _time(text) -> datetime | None:
    try:
        return _utc(datetime.fromisoformat(str(text)))
    except ValueError:
        return None


def make_order(
    symbol: str,
    direction: str,
    entry_time: datetime,
    entry: float,
    sl: float,
    tp: float | None = None,
    exit_time: datetime | None = None,
    exit_price: float | None = None,
) -> dict:
    """The order as a JSON dict. `entry_time` / `exit_time`: close times (UTC) of the entry / exit
    candle; no exit: the trade is still open."""
    return {
        "symbol": symbol,
        "direction": direction,
        "entry_time": _text(entry_time),
        "entry": float(entry),
        "sl": float(sl),
        "tp": None if tp is None else float(tp),
        "exit_time": None if exit_time is None or exit_price is None else _text(exit_time),
        "exit": None if exit_time is None or exit_price is None else float(exit_price),
    }


def trade_order(trade: TradeRecord) -> dict:
    """The order of a backtest trade: its initial SL, the furthest take profit, its exit (a trade
    closed only by the end of the data is still open)."""
    tp = trade.take_profit_3 or trade.take_profit_2 or trade.take_profit
    closed = getattr(trade.exit_reason, "value", trade.exit_reason) != "end_of_data"
    direction = getattr(trade.direction, "value", trade.direction)
    direction = {"bullish": "long", "bearish": "short"}.get(direction, direction)
    return make_order(
        trade.symbol, direction, trade.entry_time, trade.entry, trade.initial_stop, tp,
        trade.exit_time if closed else None, trade.exit_price if closed else None,
    )  # fmt: skip


def inspection_order(trade):
    """Recorded setup levels and reason, in addition to the stable order-link schema."""
    order = trade_order(trade)
    order["tps"] = [
        p
        for p in (trade.take_profit, trade.take_profit_2, getattr(trade, "take_profit_3", None))
        if p is not None
    ]
    order["reason"] = getattr(trade, "reason", "")
    return order


def live_order(row: dict) -> dict | None:
    """The order of a live trade: a closed one from the bot's trades.csv row (side, entry_time,
    entry_fill, sl, exit_time, exit_price) or an open position from status.json (side, entry, sl,
    since). The bot records no take profit (the opening-range breakout exits at the session end),
    so there is none. None when the row is not an order."""
    direction = _SIDES.get(str(row.get("side")))
    when = _time(row.get("entry_time") or row.get("since"))
    entry = _number(row.get("entry_fill", row.get("entry")))
    sl = _number(row.get("sl"))
    if not (row.get("symbol") and direction and when and entry is not None and sl is not None):
        return None
    exit_time, exit_price = _time(row.get("exit_time")), _number(row.get("exit_price"))
    if exit_time is None or exit_price is None:
        exit_time = exit_price = None
    return make_order(row["symbol"], direction, when, entry, sl, None, exit_time, exit_price)


def _valid(order: dict) -> bool:
    """The order's numbers make sense: a stop away from the entry (R is measured in it), an exit
    not before the entry."""
    if order["sl"] == order["entry"]:
        return False
    exit_time = order["exit_time"]
    return exit_time is None or _time(exit_time) >= _time(order["entry_time"])


def chip_text(order: dict, note: str | None = None) -> str:
    """The chip on the chart: "Trade: NAS100 long 2026-10-02 14:36" (+ a note, e.g. not cached)."""
    when = _time(order["entry_time"])
    text = f"Trade: {order['symbol']} {order['direction']} {when:%Y-%m-%d %H:%M}"
    return f"{text} ({note})" if note else text


# --- link and focus ------------------------------------------------------------------------------


def order_query(order: dict, timeframe: str | None) -> str:
    query = {"symbol": order["symbol"], "dir": order["direction"], "entry": order["entry_time"]}
    if timeframe:
        query["tf"] = timeframe
    query["ep"], query["sl"] = repr(order["entry"]), repr(order["sl"])
    if order["tp"] is not None:
        query["tp"] = repr(order["tp"])
    if order["exit_time"] is not None:
        query["exit"], query["xp"] = order["exit_time"], repr(order["exit"])
    return urlencode(query)


def order_link(order: dict, timeframe: str | None) -> str:
    """Chart URL that opens the order on `timeframe` (None: the chart keeps its timeframe)."""
    return "/?" + order_query(order, timeframe)


def trade_link(trade: TradeRecord, timeframe: str | None) -> str:
    return order_link(trade_order(trade), timeframe)


def live_link(row: dict) -> str | None:
    """Chart link of a live trade / position (the bot's timeframe), None if it is no order."""
    order = live_order(row)
    return None if order is None else order_link(order, LIVE_TIMEFRAME)


def margin_days(timeframe: Timeframe) -> int:
    return max(MIN_MARGIN_DAYS, -(-MARGIN_CANDLES * timeframe.value // 1440))


def _entry_day(order: dict) -> date:
    return (_time(order["entry_time"]) - timedelta(seconds=1)).date()  # the candle's own day


def _exit_day(order: dict) -> date:
    when = _time(order["exit_time"] or order["entry_time"])
    return (when - timedelta(seconds=1)).date()


def focus_from_order(order: dict, timeframe: str | None) -> dict:
    """The `chart-focus` store for an order: symbol, timeframe (None: keep), the days to show
    (from / to), the entry and exit times to scroll to (t0 / t1) and the order itself."""
    tf = Timeframe[timeframe] if timeframe in Timeframe.__members__ else Timeframe.M5
    margin = timedelta(days=margin_days(tf))
    return {
        "symbol": order["symbol"],
        "tf": timeframe if timeframe in Timeframe.__members__ else None,
        "from": (_entry_day(order) - margin).isoformat(),
        "to": (_exit_day(order) + margin).isoformat(),
        "t0": order["entry_time"],
        "t1": order["exit_time"] or order["entry_time"],
        "order": order,
    }


def focus_from_query(search: str | None) -> dict | None:
    """The trade focus of a chart URL query, or None. With `dir` it is an order link (see the
    module docstring); without it the older form (symbol, from, to, t0, t1)."""
    query = {k: v[0] for k, v in parse_qs((search or "").lstrip("?")).items()}
    if "dir" in query:
        return _order_focus(query)
    try:
        focus = {
            "symbol": query["symbol"],
            "from": date.fromisoformat(query["from"]).isoformat(),
            "to": date.fromisoformat(query["to"]).isoformat(),
            "t0": datetime.fromisoformat(query["t0"]).isoformat(),
            "t1": datetime.fromisoformat(query["t1"]).isoformat(),
        }
    except (KeyError, ValueError):
        return None
    return focus if focus["from"] <= focus["to"] else None


def _order_focus(query: dict) -> dict | None:
    entry_time = _time(query.get("entry"))
    entry, sl = _number(query.get("ep")), _number(query.get("sl"))
    tp = _number(query["tp"]) if "tp" in query else None
    if not (query.get("symbol") and query["dir"] in (LONG, SHORT) and entry_time):
        return None
    if entry is None or sl is None or ("tp" in query and tp is None):
        return None
    exit_time = exit_price = None
    if "exit" in query:
        exit_time, exit_price = _time(query["exit"]), _number(query.get("xp"))
        if exit_time is None or exit_price is None:
            return None
    order = make_order(
        query["symbol"], query["dir"], entry_time, entry, sl, tp, exit_time, exit_price
    )
    if not _valid(order):
        return None
    return focus_from_order(order, query.get("tf"))


# --- timeframe of a run --------------------------------------------------------------------------


def run_settings(folder: Path) -> str:
    """The saved run's strategy inputs, so inspecting another strategy cannot invent a setup."""
    try:
        return to_json(from_dict(json.loads((folder / "settings.json").read_text("utf-8"))))
    except (OSError, ValueError, KeyError, TypeError):
        return ""


@lru_cache(maxsize=32)
def _run_timeframe(folder: str, mtime_ns: int, symbol: str) -> str:
    try:
        settings = from_dict(json.loads((Path(folder) / "settings.json").read_text("utf-8")))
        base = None
        try:
            base = make_strategy(symbol, settings.strategy, settings.detectors).base_timeframe
        except (ValueError, KeyError, TypeError):  # e.g. no sessions for this symbol
            spec = next(s for s in REGISTRY.values() if isinstance(settings.strategy, s.config_cls))
            base = getattr(spec.strategy_cls, "base_timeframe", None)
        if base is not None and supported(base):
            return base.name
    except (OSError, ValueError, KeyError, StopIteration, TypeError):
        pass
    return DEFAULT_TIMEFRAME


def run_timeframe(folder: Path, symbol: str) -> str:
    """Timeframe a trade of the run is shown on: the strategy's base timeframe from the run's
    settings.json (re-read when it changed); `DEFAULT_TIMEFRAME` when it can't be told."""
    try:
        mtime = (Path(folder) / "settings.json").stat().st_mtime_ns
    except OSError:
        mtime = 0
    return _run_timeframe(str(folder), mtime, symbol)


# --- days to load --------------------------------------------------------------------------------


def focus_dates(cached: Sequence[date], focus: dict, config: ChartConfig) -> tuple[str, str] | None:
    """(first, last) ISO days to load for an order focus, or None when the entry's day is not in
    the cache. Cut to the run of consecutive cached days around the entry; above the chart's
    candle limit the margin shrinks (the trade's own days always stay)."""
    order = focus["order"]
    cached_set = set(cached)
    entry_day, exit_day = _entry_day(order), _exit_day(order)
    if entry_day not in cached_set:
        return None
    block_first, block_last = cached_block(cached_set, entry_day)
    tf = Timeframe[focus["tf"]] if focus.get("tf") else Timeframe.M5
    trade_first, trade_last = entry_day, min(max(exit_day, entry_day), block_last)
    first = max(date.fromisoformat(focus["from"]), block_first)
    last = min(date.fromisoformat(focus["to"]), block_last)
    left, right = (trade_first - first).days, (last - trade_last).days
    while ((trade_last - trade_first).days + left + right + 1) * 1440 // tf.value > (
        config.max_candles
    ) and (left or right):
        left, right = left // 2, right // 2
    return (
        (trade_first - timedelta(days=left)).isoformat(),
        (trade_last + timedelta(days=right)).isoformat(),
    )


def latest_dates(
    cached: Sequence[date], timeframe: str, config: ChartConfig
) -> tuple[str, str] | None:
    """The newest days (about half the candle limit, within the last run of cached days): what the
    chart shows for a trade whose day is not cached. None without cached days."""
    if not cached:
        return None
    cached_set = set(cached)
    last = max(cached_set)
    block_first, _ = cached_block(cached_set, last)
    days = max(1, config.max_candles // 2 * Timeframe[timeframe].value // 1440)
    return max(last - timedelta(days=days - 1), block_first).isoformat(), last.isoformat()


# --- the drawing ---------------------------------------------------------------------------------


def _containing(opens: Sequence[datetime], close: datetime) -> int:
    """Index of the candle that closed at `close` (the last one opening before it)."""
    lo, hi = 0, len(opens)
    while lo < hi:  # bisect_left on open times
        mid = (lo + hi) // 2
        if opens[mid] < close:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


def _r(order: dict, price: float) -> float:
    risk = abs(order["entry"] - order["sl"])
    sign = 1 if order["direction"] == LONG else -1
    return sign * (price - order["entry"]) / risk


def order_drawings(
    order: dict,
    opens: Sequence[datetime],
    timeframe: Timeframe,
    digits: int,
    config: ChartConfig,
    light: bool = False,
) -> list[Drawing]:
    """The order on the loaded candles (`opens`: their open times, UTC; x = candle index): the
    take-profit box green, the stop box red, level lines, labels and a marker at the exit. Nothing
    when the entry is not on the loaded candles. Open order (or an exit after the last candle): to
    the last candle, no exit marker. The stop and the take profit are on their sides of the entry
    by their prices alone, so a short is the mirror of a long. `light` (the run's many trades
    without a focused one): the two boxes and the entry line only, no labels, no exit marker."""
    if not opens:
        return []
    entry_time = _time(order["entry_time"])
    last_close = opens[-1] + timeframe.duration
    if not opens[0] < entry_time <= last_close:
        return []
    x0 = _containing(opens, entry_time)
    last = len(opens) - 1
    exit_time = _time(order["exit_time"]) if order["exit_time"] else None
    exited = exit_time is not None and exit_time <= last_close
    x1 = max(x0, _containing(opens, exit_time)) if exited else last
    entry, sl, tp = order["entry"], order["sl"], order["tp"]

    def fmt(price: float) -> str:
        return f"{price:.{digits}f}"

    fill = config.trade_box_opacity
    out: list[Drawing] = []
    if tp is not None:
        out.append(
            Box(x0, x1, min(entry, tp), max(entry, tp), "Order target",
                fill=config.trade_profit_color, fill_opacity=fill)
        )  # fmt: skip
    out.append(
        Box(x0, x1, min(entry, sl), max(entry, sl), "Order risk",
            fill=config.trade_loss_color, fill_opacity=fill)
    )  # fmt: skip
    levels = [(entry, config.trade_entry_color, f"Entry {fmt(entry)}", "top right")]
    above = entry > sl  # a long's entry is above its stop: the stop label goes below its line
    levels.append(
        (sl, config.trade_loss_color, f"SL {fmt(sl)} ({_r(order, sl):+.2f}R)",
         "bottom right" if above else "top right")
    )  # fmt: skip
    for target in dict.fromkeys(order.get("tps", [tp])):
        if target is None:
            continue
        levels.append(
            (target, config.trade_profit_color, f"TP {fmt(target)} ({_r(order, target):+.2f}R)",
             "top right" if above else "bottom right")
        )  # fmt: skip
    for price, color, text, anchor in levels[: 1 if light else None]:
        out.append(Line(x0, x1, price, price, "Order level", color, LINE_WIDTH))
        if not light:
            out.append(Label(x0, price, text, "Order label", color, LABEL_SIZE, anchor))
    if exited and not light:
        price = order["exit"]
        out.append(
            Marker(x1, price, "Order exit", "circle", EXIT_COLOR, EXIT_MARKER_SIZE,
                   f"Exit {fmt(price)} ({_r(order, price):+.2f}R)", EXIT_OUTLINE)
        )  # fmt: skip
    return out


def order_payload(
    order: dict,
    opens: Sequence[datetime],
    timeframe: Timeframe,
    digits: int,
    config: ChartConfig,
    light: bool = False,
) -> list[dict]:
    """`order_drawings` as the JSON objects the browser draws (`chart_data.encode`)."""
    drawn = order_drawings(order, opens, timeframe, digits, config, light)
    return [encode(OVERLAY, d) for d in drawn]
