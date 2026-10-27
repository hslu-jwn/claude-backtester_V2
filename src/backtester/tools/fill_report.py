"""Real fills of the demo bot against the backtest's cost model (ROADMAP V2.4b / V2.6d).

    python -m backtester.tools.fill_report [--live-dir results/live] [--since 2026-10-27T16:00]
        [--comment-prefix fp] [--deals deals.csv] [--out results/fill_report] [--target-r 1.0]

Read-only: reads `<live-dir>/<date>/paper.csv` and `trades.csv` (and optionally a deals CSV
made by `deals_to_csv` from MT5 `history_deals_get`), writes `fills.csv` (one row per fill)
and `report.md` into `--out`. Never connects to MT5 and never writes into the live folder.

Which rows: paper.csv rows with status filled, comment starting with `--comment-prefix`
(default "fp", the fill probe; the earlier "orb" trades are excluded) and time_utc >= `--since`;
trades.csv rows whose ticket is one of those fills.

Sign convention: slippage is positive when adverse (buy filled above, sell filled below the
reference price). Reference prices:
- entry: `signal_entry` (the bar close, a bid). A buy fills at the ask, so its raw difference
  contains the spread; `slip` is the raw difference minus the bar's spread for buys (what the
  model calls slippage, the spread is charged separately); `slip_raw` is the plain difference.
- exit stop_loss: `sl`; take_profit: the TP rebuilt as signal +/- target_r x |signal - sl|
  (the fill probe's TP; trades.csv has no TP column; limit-like, the model has no slippage
  there); signal (market close): `sim_exit` (the exit bar's close, a bid); closing a short
  buys at the ask, so for it the spread is removed like for a buy entry (the entry bar's
  spread; the exit bar's spread is not logged).
Slippage also in units of the bar's spread (`slip_spreads`) and of the model's slippage
(`slip_model_units`, `CostConfig().slippage(symbol, price)`).
"""

from __future__ import annotations

import argparse
import csv
import io
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtester.cli import utf8_output
from backtester.engine.costs import CostConfig
from backtester.paths import RESULTS_DIR

DEFAULT_SINCE = "2026-10-27T16:00"
DEFAULT_PREFIX = "fp"
DEFAULT_TARGET_R = 1.0  # FillProbeConfig.target_r
FLAG_PCT = 10.0  # commission differences above this many percent are flagged
# UTC hour buckets: (name, first hour, end hour); Asia wraps midnight
ASIA, LONDON, NEW_YORK = "Asia", "London", "New York"
SESSIONS = ((ASIA, 22, 7), (LONDON, 7, 13), (NEW_YORK, 13, 22))
KIND_ENTRY, KIND_SL, KIND_TP, KIND_SIGNAL = "entry", "stop_loss", "take_profit", "signal"
FILL_COLUMNS = [
    "kind", "symbol", "side", "ticket", "time_utc", "session", "ref_price", "fill_price",
    "slip_raw", "slip", "bar_spread", "slip_spreads", "model_slip", "slip_model_units",
    "worse_than_model", "model_spread_table", "model_spread_fixed", "spread_vs_table",
    "spread_vs_fixed", "spread_source",
]  # fmt: skip
DEAL_COLUMNS = [
    "ticket", "position_id", "symbol", "time", "type", "entry", "volume", "price",
    "commission", "fee", "swap", "profit", "comment", "magic",
]  # fmt: skip
_DEAL_TYPES = {0: "buy", 1: "sell"}
_DEAL_ENTRIES = {0: "in", 1: "out", 2: "inout", 3: "out_by"}


def session_of(hour: int) -> str:
    """UTC hour -> Asia 22-07, London 07-13, New York 13-22."""
    for name, start, end in SESSIONS:
        if (start <= hour < end) if start < end else (hour >= start or hour < end):
            return name
    raise ValueError(f"hour out of range: {hour}")


def deals_to_csv(
    deals: Iterable[Any], path: Path | str | None = None, time_offset_s: int = 0
) -> str:
    """MT5 `history_deals_get` result -> the deals CSV text (also written to `path`).

    Columns `DEAL_COLUMNS`; time = UTC ISO (`deal.time` epoch seconds minus `time_offset_s`:
    pass the server's UTC offset in seconds if the epoch is server time); type buy / sell
    (others: the number); entry in / out / inout / out_by; commission, fee, swap, profit as
    MT5 reports them (account currency, costs negative)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(DEAL_COLUMNS)
    for d in deals:
        when = datetime.fromtimestamp(int(d.time) - time_offset_s, UTC).isoformat()
        writer.writerow([
            d.ticket, d.position_id, d.symbol, when, _DEAL_TYPES.get(d.type, d.type),
            _DEAL_ENTRIES.get(d.entry, d.entry), d.volume, d.price, d.commission,
            getattr(d, "fee", 0.0), d.swap, d.profit, d.comment, d.magic,
        ])  # fmt: skip
    text = buf.getvalue()
    if path is not None:
        Path(path).write_text(text, encoding="utf-8", newline="")
    return text


def _read(path: Path) -> pd.DataFrame | None:
    if not path.is_file() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        return None


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _ticket(value: Any) -> str:
    n = _num(value)
    return "" if np.isnan(n) else str(int(n))


def _parse_time(text: str) -> datetime:
    t = pd.Timestamp(text)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    return t.to_pydatetime()


def load_live(
    live_dir: Path, since: datetime, prefix: str
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """(filled paper rows, trades of those tickets, notes) over all `<live_dir>/*/` dates."""
    notes: list[str] = []
    papers, trades = [], []
    days = sorted(p for p in live_dir.iterdir() if p.is_dir()) if live_dir.is_dir() else []
    if not days:
        notes.append(f"no date folders in {live_dir}")
    for day in days:
        if day.name[:4].isdigit() and day.name < since.date().isoformat():
            continue  # a date before --since cannot hold a fill of it
        paper, trade = _read(day / "paper.csv"), _read(day / "trades.csv")
        if paper is None:
            notes.append(f"{day.name}: paper.csv missing or empty")
        else:
            papers.append(paper)
        if trade is None:
            notes.append(f"{day.name}: trades.csv missing or empty")
        else:
            trades.append(trade)
    paper = pd.concat(papers, ignore_index=True) if papers else pd.DataFrame()
    trade = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    if paper.empty:
        return paper, trade, notes
    keep = paper["comment"].str.startswith(prefix) & (paper["status"] == "filled")
    keep &= pd.to_datetime(paper["time_utc"], utc=True, format="ISO8601") >= since
    paper = paper[keep].copy()
    paper["ticket"] = paper["ticket"].map(_ticket)
    if not trade.empty:
        trade = trade.copy()
        trade["ticket"] = trade["ticket"].map(_ticket)
        trade = trade[trade["ticket"].isin(set(paper["ticket"]))]
    return paper, trade, notes


def _models(costs: CostConfig, symbol: str, at: datetime, price: float) -> tuple[float, float, float]:
    """(model slippage, table spread, fixed price-scaled spread); NaN for an unknown symbol."""
    if symbol not in costs.symbols:
        return float("nan"), float("nan"), float("nan")
    fixed = CostConfig(spread_table=None, symbols=costs.symbols).spread(symbol, None, price)
    return costs.slippage(symbol, price), costs.spread(symbol, at, price), fixed


def _row(
    costs: CostConfig, kind: str, symbol: str, side: str, ticket: str, at: datetime,
    ref: float, fill: float, bar_spread: float, model_slip_applies: bool, remove_spread: bool,
) -> dict[str, Any]:  # fmt: skip
    """One fill of the order `side`; adverse: buy +(fill - ref), sell +(ref - fill)."""
    sign = 1.0 if side == "buy" else -1.0
    raw = sign * (fill - ref)
    slip = raw - bar_spread if remove_spread and not np.isnan(bar_spread) else raw
    model_slip, tab, fixed = _models(costs, symbol, at, fill)
    applied = model_slip if model_slip_applies else 0.0
    return {
        "kind": kind, "symbol": symbol, "side": side, "ticket": ticket,
        "time_utc": at.isoformat(), "session": session_of(at.hour), "ref_price": ref,
        "fill_price": fill, "slip_raw": raw, "slip": slip, "bar_spread": bar_spread,
        "slip_spreads": slip / bar_spread if bar_spread > 0 else float("nan"),
        "model_slip": applied,
        "slip_model_units": slip / applied if applied and not np.isnan(applied) else float("nan"),
        "worse_than_model": bool(slip > applied) if not np.isnan(applied) else False,
        "model_spread_table": tab, "model_spread_fixed": fixed,
        "spread_vs_table": bar_spread / tab if tab and not np.isnan(tab) else float("nan"),
        "spread_vs_fixed": bar_spread / fixed if fixed and not np.isnan(fixed) else float("nan"),
        "spread_source": "entry bar",
    }  # fmt: skip


def build_fills(
    paper: pd.DataFrame, trades: pd.DataFrame, costs: CostConfig, target_r: float = DEFAULT_TARGET_R
) -> tuple[pd.DataFrame, list[str]]:
    """One row per entry fill and per exit fill (see the module docstring)."""
    notes: list[str] = []
    rows: list[dict[str, Any]] = []
    by_ticket = {r["ticket"]: r for r in paper.to_dict("records")}
    for r in by_ticket.values():
        fill = _num(r["real_fill"])
        if np.isnan(fill):
            notes.append(f"ticket {r['ticket']}: filled without real_fill, skipped")
            continue
        rows.append(_row(
            costs, KIND_ENTRY, r["symbol"], r["side"], r["ticket"], _parse_time(r["time_utc"]),
            _num(r["signal_entry"]), fill, _num(r["spread"]), True, r["side"] == "buy",
        ))  # fmt: skip
    skipped_tp = 0
    for t in trades.to_dict("records") if not trades.empty else []:
        p = by_ticket.get(t["ticket"])
        if p is None:
            continue
        side = "sell" if t["side"] == "buy" else "buy"  # the closing order's side
        kind = t["exit_reason"]
        if kind == KIND_SL:
            ref, applies, remove = _num(t["sl"]), True, False
        elif kind == KIND_SIGNAL:
            ref, applies, remove = _num(t["sim_exit"]), True, side == "buy"
        elif kind == KIND_TP:
            sig, sl = _num(p["signal_entry"]), _num(p["sl"])
            if np.isnan(sig) or np.isnan(sl):
                skipped_tp += 1
                continue
            sgn = 1.0 if t["side"] == "buy" else -1.0
            ref, applies, remove = sig + sgn * target_r * abs(sig - sl), False, False
        else:
            notes.append(f"ticket {t['ticket']}: unknown exit_reason {kind!r}, skipped")
            continue
        rows.append(_row(
            costs, kind, t["symbol"], side, t["ticket"], _parse_time(t["exit_time"]), ref,
            _num(t["exit_price"]), _num(p["spread"]), applies, remove,
        ))  # fmt: skip
    if skipped_tp:
        notes.append(f"{skipped_tp} take_profit exits skipped: signal_entry / sl missing")
    return pd.DataFrame(rows, columns=FILL_COLUMNS), notes


def _stats(df: pd.DataFrame, price_units: bool) -> dict[str, float]:
    s = df["slip"] if price_units else df["slip_model_units"].dropna()
    return {
        "n": len(df), "mean": s.mean(), "median": s.median(), "p90": s.quantile(0.9),
        "share_worse": df["worse_than_model"].mean(),
    }  # fmt: skip


def group_table(fills: pd.DataFrame, key: str | list[str], price_units: bool = False) -> pd.DataFrame:
    rows = {k: _stats(g, price_units) for k, g in fills.groupby(key)}
    df = pd.DataFrame.from_dict(rows, orient="index")
    if isinstance(key, list):
        df.index = [" / ".join(k) for k in df.index]
    return df


def symbol_table(fills: pd.DataFrame, costs: CostConfig) -> pd.DataFrame:
    """Per symbol over the market fills (entries, stop_loss, signal exits; take_profit is a
    limit-like fill and left out): price-unit stats, the model slippage and the suggestion
    (median and p90 of the adverse slippage, floored at 0)."""
    mkt = fills[fills["kind"] != KIND_TP]
    rows = {}
    for sym, g in mkt.groupby("symbol"):
        s = g["slip"]
        model = costs.symbols[sym].slippage if sym in costs.symbols else float("nan")
        rows[sym] = {
            "n": len(g), "mean": s.mean(), "median": s.median(), "p90": s.quantile(0.9),
            "model_slip": model, "share_worse": g["worse_than_model"].mean(),
            "suggest_median": max(0.0, s.median()), "suggest_p90": max(0.0, s.quantile(0.9)),
            "spread_mean": g["bar_spread"].mean(),
            "spread_vs_table": g["spread_vs_table"].median(),
            "spread_vs_fixed": g["spread_vs_fixed"].median(),
        }  # fmt: skip
    return pd.DataFrame.from_dict(rows, orient="index")


def commission_table(
    deals: pd.DataFrame, tickets: set[str], costs: CostConfig, prefix: str
) -> pd.DataFrame:
    """Commission (+ fee) per lot per side, real against the model, per symbol. Model per
    side: commission_per_lot / 2 plus commission_pct_per_side x notional per lot (deal price
    x contract size x quote_to_usd). Deals of our tickets (position_id) or our comment."""
    d = deals.copy()
    for col in ("volume", "price", "commission", "fee"):
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0.0) if col in d else 0.0
    pos = d["position_id"] if "position_id" in d else d["ticket"]
    comment = d["comment"] if "comment" in d else pd.Series("", index=d.index)
    d = d[pos.map(_ticket).isin(tickets) | comment.str.startswith(prefix)]
    d = d[d["entry"].isin(["in", "out"]) & (d["volume"] > 0)]
    rows = {}
    for sym, g in d.groupby("symbol"):
        if sym not in costs.symbols:
            continue
        c = costs.symbols[sym]
        per_lot = (g["commission"] + g["fee"]).abs() / g["volume"]
        model = c.commission_per_lot / 2 + c.commission_pct_per_side * g["price"] * c.value_per_price_unit
        real, mod = float(per_lot.mean()), float(model.mean())
        diff = (real / mod - 1) * 100 if mod else float("nan")
        rows[sym] = {
            "deals": len(g), "real_per_lot_side": real, "model_per_lot_side": mod,
            "diff_pct": diff,
            "flag": bool(abs(diff) > FLAG_PCT) if mod else real > 0,
        }  # fmt: skip
    return pd.DataFrame.from_dict(rows, orient="index")


def _md(df: pd.DataFrame, floatfmt: str = "{:.4g}") -> str:
    if df.empty:
        return "_no data_\n"
    lines = ["| | " + " | ".join(str(c) for c in df.columns) + " |",
             "|" + "---|" * (len(df.columns) + 1)]  # fmt: skip
    for idx, row in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join([str(idx), *cells]) + " |")
    return "\n".join(lines) + "\n"


def build_report(
    fills: pd.DataFrame, costs: CostConfig, notes: list[str], commissions: pd.DataFrame | None,
    since: datetime,
) -> str:  # fmt: skip
    kinds = ", ".join(f"{k} {v}" for k, v in fills["kind"].value_counts().items())
    out = [f"# Fill report (since {since.isoformat()})\n", f"{len(fills)} fills: {kinds}\n"]
    out.append(
        "Slippage: positive = adverse. `slip` removes the spread of a buy entry and of a "
        "short's market close (bid-based reference). Symbol table in price units, over the "
        "market fills (entries, stop_loss, signal exits); session / type tables in units of "
        "the model slippage (take_profit has no model slippage and is excluded from those "
        "units). Spread columns: median of bar spread / model spread.\n"
    )
    if notes:
        out.append("## Notes\n" + "\n".join(f"- {n}" for n in notes) + "\n")
    if fills.empty:
        return "\n".join(out)
    out.append("## By symbol (price units)\n" + _md(symbol_table(fills, costs)))
    out.append("## By session (UTC)\n" + _md(group_table(fills, "session")))
    out.append("## By fill type\n" + _md(group_table(fills, "kind")))
    out.append("## Session x fill type\n" + _md(group_table(fills, ["session", "kind"])))
    if commissions is not None:
        out.append(f"## Commission per lot per side (flag: > {FLAG_PCT:.0f} % off)\n" + _md(commissions))
    else:
        out.append("## Commission\nno deals file given.\n")
    return "\n".join(out)


def run(
    live_dir: Path, since: datetime, prefix: str, deals: Path | None, out: Path,
    target_r: float = DEFAULT_TARGET_R,
) -> tuple[pd.DataFrame, str]:  # fmt: skip
    costs = CostConfig()
    paper, trades, notes = load_live(live_dir, since, prefix)
    if paper.empty:
        fills = pd.DataFrame(columns=FILL_COLUMNS)
        notes.append("no filled paper rows match --since / --comment-prefix")
    else:
        fills, more = build_fills(paper, trades, costs, target_r)
        notes += more
    commissions = None
    if deals is not None:
        deal_df = _read(deals)
        if deal_df is None:
            notes.append(f"deals file {deals} missing or empty")
        else:
            tickets = set(paper["ticket"]) if not paper.empty else set()
            commissions = commission_table(deal_df, tickets, costs, prefix)
    report = build_report(fills, costs, notes, commissions, since)
    out.mkdir(parents=True, exist_ok=True)
    fills.to_csv(out / "fills.csv", index=False)
    (out / "report.md").write_text(report, encoding="utf-8")
    return fills, report


def main(argv: list[str] | None = None) -> int:
    utf8_output()
    ap = argparse.ArgumentParser(description="Real fills against the backtest cost model.")
    ap.add_argument("--live-dir", type=Path, default=RESULTS_DIR / "live")
    ap.add_argument("--since", default=DEFAULT_SINCE, help="UTC, ISO (default %(default)s)")
    ap.add_argument("--comment-prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--deals", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=RESULTS_DIR / "fill_report")
    ap.add_argument("--target-r", type=float, default=DEFAULT_TARGET_R)
    args = ap.parse_args(argv)
    fills, _ = run(
        args.live_dir, _parse_time(args.since), args.comment_prefix, args.deals, args.out,
        args.target_r,
    )  # fmt: skip
    print(f"{len(fills)} fills -> {args.out}")
    if not fills.empty:
        fmt = {"float_format": lambda v: f"{v:.3g}"}
        print("\nby fill type (units of model slippage)\n" + group_table(fills, "kind").to_string(**fmt))
        print("\nby session\n" + group_table(fills, "session").to_string(**fmt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
