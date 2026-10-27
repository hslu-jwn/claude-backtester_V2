"""Side panel of the chart page (ROADMAP 7.4): Backtest result and Trades in view.

Pure helpers (tested in `tests/ui/test_chart_side.py`) and the panel's layout; the callbacks
live in `pages/chart.py`. Numbers come from the newest run's files through the results page's
own readers and `analytics/metrics.py` `summarize` (nothing is computed twice).

- **Backtest result**: the newest run in `results/` (`newest_run`), its net R, win rate, trades
  and max drawdown in R, the run id and a link to its results page. No run: "No backtest yet".
- The overlay switches are not here: they sit in the Settings popover (`pages/chart.py`
  `overlay_controls`, user 2026-10-19).
- **Trades in view**: the newest run's trades of the shown symbol whose entry candle is inside
  the visible range (`trades_in_view`); a click on one goes to it (`chart-goto`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from dash import dcc, html

from backtester.analytics.metrics import summarize
from backtester.analytics.records import TradeRecord, read_trades
from backtester.ui.layout import key_strip
from backtester.ui.pages import results

MAX_LISTED = 40  # trades listed in the card; more are counted ("+N more: zoom in")
NO_RUN_TEXT = "No backtest yet"
RESULTS_PREFIX = "/results/"


@lru_cache(maxsize=4)
def _read_cached(folder: str, mtime_ns: int) -> tuple[TradeRecord, ...]:
    return tuple(read_trades(Path(folder)))


def run_trades(folder: Path) -> tuple[TradeRecord, ...]:
    """The run's trades (read again only when trades.csv changed)."""
    path = folder / "trades.csv"
    try:
        mtime = path.stat().st_mtime_ns
    except OSError:
        return ()
    return _read_cached(str(folder), mtime)


def newest_run(results_dir: Path = results.RESULTS_DIR) -> Path | None:
    """Folder of the newest run (run ids start with their UTC start time), or None."""
    runs = results.list_runs(results_dir)
    return results.run_folder(runs[0]["value"], results_dir) if runs else None


def run_summary(results_dir: Path = results.RESULTS_DIR) -> dict | None:
    """What the Backtest result card shows for the newest run, or None without a run."""
    folder = newest_run(results_dir)
    if folder is None:
        return None
    trades = run_trades(folder)
    s = summarize(trades)
    return {
        "run_id": folder.name,
        "href": f"{RESULTS_PREFIX}{folder.name}",
        "trades": s["trades"],
        "net_r": s["net_r_net"],
        "win_rate": s["win_rate"],
        "max_drawdown_r": s["max_drawdown_r_net"],
    }


def utc(t: datetime) -> datetime:
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t


def trades_in_view(
    trades,
    symbol: str | None,
    start: datetime,
    end: datetime,
) -> list[TradeRecord]:
    """Trades of `symbol` whose entry candle opens in start <= t < end (the visible range, UTC;
    `end` is the close of the last visible candle, so a trade on it is in view), in time order."""
    start, end = utc(start), utc(end)
    found = [t for t in trades if t.symbol == symbol and start <= utc(t.entry_candle) < end]
    return sorted(found, key=lambda t: utc(t.entry_candle))


def view_times(rng: dict | None) -> tuple[datetime, datetime] | None:
    """(start, end) of the browser's visible range {from, to} (UTC seconds), or None."""
    try:
        return datetime.fromtimestamp(rng["from"], UTC), datetime.fromtimestamp(rng["to"], UTC)
    except (TypeError, KeyError, ValueError, OSError):
        return None


def is_open(trade: TradeRecord) -> bool:
    """A trade still running when the data ended (closed by the end of the data)."""
    return trade.exit_reason == "end_of_data"


# --- layout ----------------------------------------------------------------------------


def _card(title: str, body, id_: str) -> html.Div:
    """A card whose title folds it (a checklist with one option, the title; pure CSS:
    `.ch-fold:has(input:checked) ~ .ch-card-body`)."""
    return html.Div(
        [
            dcc.Checklist(
                id=f"{id_}-fold",
                options=[{"label": title, "value": "fold"}],
                value=[],
                persistence=True,
                className="ch-fold",
            ),
            html.Div(body, className="ch-card-body"),
        ],
        id=id_,
        className="ch-card",
    )


def _stat(label: str, value: str, cls: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(label, className="ch-stat-label"),
            html.Div(value, className=f"ch-stat-value {cls}"),
        ],
        className="ch-stat",
    )


def result_body(summary: dict | None) -> list:
    """Content of the Backtest result card."""
    if summary is None:
        return [html.Div(NO_RUN_TEXT, className="ch-empty")]
    net, dd = summary["net_r"], summary["max_drawdown_r"]
    return [
        html.Div(
            [
                _stat(
                    "Net result",
                    "0.0 R" if abs(net) < 0.05 else f"{net:+.1f} R",
                    "ch-pos" if net >= 0.05 else "ch-neg" if net <= -0.05 else "",
                ),
                _stat("Win rate", results.fmt_pct(summary["win_rate"])),
                _stat("Trades", str(summary["trades"])),
                _stat(
                    "Max drawdown",
                    f"-{dd:.1f} R" if dd >= 0.05 else "0.0 R",
                    "ch-neg" if dd >= 0.05 else "",
                ),
            ],
            className="ch-stats",
        ),
        html.Div(
            [
                html.Span(summary["run_id"], className="ch-run-id", title=summary["run_id"]),
                dcc.Link("Results →", href=summary["href"], className="ch-link"),
            ],
            className="ch-run",
        ),
    ]


def result_strip(summary: dict | None) -> html.Div:
    """Newest-run numbers. Spec: design/ui-proposal.md › Page: Chart."""
    s = summary or {}
    items = [
        {"label": "Net R", "value": results.fmt_r(s.get("net_r"))},
        {"label": "Win rate", "value": results.fmt_pct(s.get("win_rate"))},
        {"label": "Trades", "value": str(s["trades"]) if s else "—"},
        {"label": "Max drawdown", "value": results.fmt_r(s.get("max_drawdown_r"), False)},
    ]
    if s:
        items[0]["sign"] = "green" if s["net_r"] > 0 else "red" if s["net_r"] < 0 else ""
    return html.Div(
        [
            html.Div(key_strip(items), id="ch-card-result"),
            dcc.Link(
                "Results →",
                href=s.get("href", ""),
                className="ch-link",
                id="chart-result-link",
                style={} if s else {"display": "none"},
            ),
        ],
        id="chart-key-strip",
        title=s.get("run_id", NO_RUN_TEXT),
        className="ch-key-row",
    )


def trade_item(trade: TradeRecord, kind: str = "side-trade") -> html.Button:
    """One row of "Trades in view": direction badge, date · setup, result in R or "open"."""
    long = trade.direction == "long"
    when = utc(trade.entry_candle)
    setup = results.name(trade.confluence) if trade.confluence else "—"
    if is_open(trade):
        outcome = html.Span("open", className="ch-trade-r ch-muted")
    else:
        cls = "ch-pos" if trade.r_net > 0 else "ch-neg" if trade.r_net < 0 else "ch-muted"
        outcome = html.Span(f"{trade.r_net:+.2f}R", className=f"ch-trade-r {cls}")
    return html.Button(
        [
            html.Span(
                "LONG" if long else "SHORT",
                className=f"ch-badge {'ch-long' if long else 'ch-short'}",
            ),
            html.Span(
                f"{trade.symbol} · {when:%Y-%m-%d %H:%M} · {setup}"
                if kind == "run-trade"
                else f"{when:%b %d} · {setup}",
                className="ch-trade-what",
            ),
            outcome,
        ],
        id={"type": kind, "index": trade.id},
        className="ch-trade",
        title=f"{trade.symbol} {when:%Y-%m-%d %H:%M} UTC",
        n_clicks=0,
    )


def trades_body(found: list[TradeRecord], has_run: bool = True) -> list:
    """Content of the Trades in view card."""
    if not has_run:
        return [html.Div(NO_RUN_TEXT, className="ch-empty")]
    if not found:
        return [html.Div("No trades in view", className="ch-empty")]
    items = [trade_item(t) for t in found[:MAX_LISTED]]
    if len(found) > MAX_LISTED:
        items.append(html.Div(f"+{len(found) - MAX_LISTED} more: zoom in", className="ch-empty"))
    return items


def collapsed_after(clicks: int | None, collapsed: bool | None) -> bool:
    """The panel's collapsed state after a click on its toggle (a first call is no click)."""
    return (not collapsed) if clicks else bool(collapsed)


def sort_run_trades(trades, by: str | None):
    """The run's trades for the list under the chart (user, 2026-10-27): "pair" = by symbol
    A..Z, each pair's trades in time order; otherwise (default "time") by entry time."""
    if by == "pair":
        return tuple(sorted(trades, key=lambda t: (t.symbol, t.entry_candle, t.id)))
    return tuple(sorted(trades, key=lambda t: (t.entry_candle, t.id)))


def run_trades_class(sort: str | None) -> str:
    """Class of the list under the chart: "pair" reorders its rows with CSS `order` (each row
    carries `--pair-rank`), so switching never re-renders the pattern-matched rows."""
    return "ch-by-pair" if sort == "pair" else ""


def run_trades_style(collapsed: bool | None) -> dict:
    """The list under the chart, minimized or shown."""
    return {"display": "none"} if collapsed else {}


def run_trades_toggle_label(collapsed: bool | None) -> str:
    return "Show" if collapsed else "Minimize"


def main_class(collapsed: bool | None) -> str:
    return "ch-main ch-collapsed" if collapsed else "ch-main"


def panel(summary: dict | None) -> html.Div:
    """The whole side panel (cards are collapsible; the toolbar button hides the panel)."""
    return html.Div(
        [
            _card(
                "Trades in view",
                html.Div(trades_body([], summary is not None), id="side-trades"),
                "ch-card-trades",
            ),
        ],
        id="chart-side",
        className="ch-side",
    )
