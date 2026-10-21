"""Rows of the Research page: one per research variant and per plain backtest run.

Spec: research-runner.md > Research page, Scorecard, Warning flags (ROADMAP 6.1 d2 / 6.2).
No Dash here (the page is pages/research.py).

- **Research variants:** `results/research/<id>/` (`research.json`, `variants.csv`, `test.csv`,
  written by tools/research.py). One row per variant with its development scorecard; the chosen
  variant's row also carries the latest test row (test net R, deflated Sharpe, verdict, and the
  test flags added to its flags). Its link opens the chosen development run copy
  (`results/<dev_run>`), every other variant opens its variant folder.
- **Plain runs:** every `results/<run id>/` folder with a readable `summary.json` and a
  `trades.csv`; the scorecard and flags are computed from the trade list
  (`analytics/scorecard.py`), development columns only. The chosen variant's dev copy and its
  test runs are not listed again (they are the research row), so nothing shows twice.
- **Cache:** per folder, keyed by the mtime and size of the files read, so a page with hundreds
  of runs stays fast; a folder is parsed again only when a file changed. The folder listing
  itself is read on every load, so new runs appear on "Reload".
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from backtester.analytics.records import read_trades
from backtester.analytics.scorecard import (
    FLAG_HALF,
    FLAG_HIGH_WIN_SMALL_EDGE,
    FLAG_LABELS,
    FLAG_STRESSED,
    FLAG_TEST_FAILED,
    FLAG_TOO_FEW,
    FLAG_WITHOUT_BEST,
    ScorecardConfig,
    flags,
    scorecard,
)
from backtester.paths import RESULTS_DIR

RESEARCH_DIR = "research"
VARIANT_PREFIX = "research~"  # results page id of a variant folder (pages/results.py)
RESULTS_PREFIX = "/results/"
FLAG_SHORT = {
    FLAG_TOO_FEW: "few trades",
    FLAG_HIGH_WIN_SMALL_EDGE: "win rate / small edge",
    FLAG_HALF: "one half",
    FLAG_STRESSED: "costs x1.5",
    FLAG_WITHOUT_BEST: "without best",
    FLAG_TEST_FAILED: "test failed",
}
VERDICT_ORDER = {"green": 0, "yellow": 1, "red": 2}  # anything else sorts after
NO_VERDICT_RANK = 3
FLAG_MARK = "⚠"
FLAG_SEPARATOR = " · "
FILTER_ALL, FILTER_UNFLAGGED, FILTER_FLAGGED = "all", "unflagged", "flagged"
PERCENT = 100.0

_cache: dict[str, tuple[tuple, object]] = {}


def clear_cache() -> None:
    _cache.clear()


# --- small readers -------------------------------------------------------------------------


def _signature(*paths: Path) -> tuple:
    out = []
    for p in paths:
        try:
            st = p.stat()
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


def _json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _csv(path: Path) -> list[dict]:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (OSError, ValueError, csv.Error):
        return []


def _num(value) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _split_flags(text) -> list[str]:
    return [f for f in str(text or "").split(";") if f]


def _strategy_label(name: str) -> str:
    from backtester.ui.pages import results  # late: the page imports this module's siblings

    return results.strategy_label({"strategy": {"name": name}}) if name else "—"


def _period(start, end) -> str:
    return f"{start} → {end}" if start and end else "—"


# --- flags text ----------------------------------------------------------------------------


def flag_text(keys: list[str]) -> str:
    """Short warning badges for the table: "⚠ few trades · ⚠ test failed"."""
    return FLAG_SEPARATOR.join(f"{FLAG_MARK} {FLAG_SHORT.get(k, k)}" for k in keys)


def flag_tooltip(keys: list[str]) -> str:
    """The full labels (analytics/scorecard.FLAG_LABELS), for the hover text."""
    return "; ".join(FLAG_LABELS.get(k, k) for k in keys)


# --- research folders ----------------------------------------------------------------------


def _research_rows(folder: Path) -> tuple[list[dict], set[str]]:
    """(rows, run folder names that belong to this research and must not be listed again)."""
    info = _json(folder / "research.json")
    variants = _csv(folder / "variants.csv")
    tests = _csv(folder / "test.csv")
    if not info or not variants:
        return [], set()
    rid = str(info.get("id") or folder.name)
    strategy = str(info.get("strategy") or "")
    symbols = [str(s) for s in info.get("symbols") or []]
    dev = (info.get("periods") or {}).get("development") or {}
    chosen = info.get("chosen") or {}
    hidden = {str(chosen["dev_run"])} if chosen.get("dev_run") else set()
    hidden |= {t["run_folder"] for t in tests if t.get("run_folder")}
    latest = {}
    for t in tests:  # the latest test run per variant
        n = _num(t.get("test_run")) or 0
        if t.get("variant_id") and n >= (
            _num(latest.get(t["variant_id"], {}).get("test_run")) or 0
        ):
            latest[t["variant_id"]] = t
    rows = []
    for v in variants:
        vid = v.get("variant_id") or ""
        trades, net = _num(v.get("trades")), _num(v.get("net_r"))
        if not vid or trades is None or net is None:
            continue
        keys = _split_flags(v.get("flags"))
        test = latest.get(vid) if chosen.get("id") == vid else None
        href_id = (
            str(chosen["dev_run"])
            if chosen.get("id") == vid and chosen.get("dev_run")
            else f"{VARIANT_PREFIX}{rid}~{vid}"
        )
        if test is not None:
            keys += [k for k in _split_flags(test.get("flags")) if k not in keys]
        win = _num(v.get("win_rate"))
        rows.append(
            {
                "source": f"{rid} {vid}", "strategy_name": strategy,
                "strategy": _strategy_label(strategy), "variant": v.get("variant") or vid,
                "symbols": ", ".join(symbols), "symbol_list": symbols,
                "period": _period(dev.get("start"), dev.get("end")), "trades": int(trades),
                "win_rate": None if win is None else win * PERCENT,
                "avg_r": _num(v.get("avg_r")), "net_r": net,
                "profit_factor": _num(v.get("profit_factor")), "max_dd_r": _num(v.get("max_dd_r")),
                "half_first_net_r": _num(v.get("half_first_net_r")),
                "half_second_net_r": _num(v.get("half_second_net_r")),
                "net_r_stressed": _num(v.get("net_r_stressed")),
                "net_r_without_best": _num(v.get("net_r_without_best")),
                "test_net_r": _num(test.get("net_r")) if test else None,
                "deflated_sharpe": _num(test.get("deflated_sharpe")) if test else None,
                "verdict": (test.get("verdict") or "") if test else "",
                "verdict_label": (test.get("verdict_label") or "") if test else "",
                "flag_keys": keys, "href": f"{RESULTS_PREFIX}{href_id}",
            }
        )  # fmt: skip
    return rows, hidden


def _research(results_dir: Path) -> tuple[list[dict], set[str]]:
    rows: list[dict] = []
    hidden: set[str] = set()
    base = results_dir / RESEARCH_DIR
    folders = sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
    for folder in folders:
        files = [folder / n for n in ("research.json", "variants.csv", "test.csv")]
        sig = _signature(*files)
        key = str(folder.resolve())
        cached = _cache.get(key)
        if cached is None or cached[0] != sig:
            cached = (sig, _research_rows(folder))
            _cache[key] = cached
        rows += cached[1][0]
        hidden |= cached[1][1]
    return rows, hidden


# --- plain runs ----------------------------------------------------------------------------


def _plain_row(folder: Path) -> dict | None:
    summary = _json(folder / "summary.json")
    if not summary or not (folder / "trades.csv").is_file():
        return None
    try:
        trades = read_trades(folder)
        card = scorecard(
            trades, ScorecardConfig(), _date(summary.get("start")), _date(summary.get("end"))
        )
        keys = flags({**card, "period": "development"}, ScorecardConfig())
    except Exception:  # noqa: BLE001 - a broken run folder is skipped, never stops the page
        return None
    settings = _json(folder / "settings.json")
    name = str((settings.get("strategy") or {}).get("name") or "session_zone_sweep")
    symbols = [str(s) for s in summary.get("symbols") or []]
    return {
        "source": folder.name, "strategy_name": name, "strategy": _strategy_label(name),
        "variant": settings.get("preset") or "—", "symbols": ", ".join(symbols),
        "symbol_list": symbols, "period": _period(summary.get("start"), summary.get("end")),
        "trades": card["trades"],
        "win_rate": None if card["win_rate"] is None else card["win_rate"] * PERCENT,
        "avg_r": card["avg_r"], "net_r": card["net_r"], "profit_factor": card["profit_factor"],
        "max_dd_r": card["max_dd_r"], "half_first_net_r": card["half_first_net_r"],
        "half_second_net_r": card["half_second_net_r"], "net_r_stressed": card["net_r_stressed"],
        "net_r_without_best": card["net_r_without_best"], "test_net_r": None,
        "deflated_sharpe": None, "verdict": "", "verdict_label": "", "flag_keys": keys,
        "href": f"{RESULTS_PREFIX}{folder.name}",
    }  # fmt: skip


def _plain(results_dir: Path, hidden: set[str]) -> list[dict]:
    rows = []
    folders = sorted(p for p in results_dir.iterdir() if p.is_dir()) if results_dir.is_dir() else []
    for folder in folders:
        if folder.name == RESEARCH_DIR or folder.name in hidden:
            continue
        sig = _signature(folder / "summary.json", folder / "trades.csv", folder / "settings.json")
        if sig[0] is None:
            continue
        key = str(folder.resolve())
        cached = _cache.get(key)
        if cached is None or cached[0] != sig:
            cached = (sig, _plain_row(folder))
            _cache[key] = cached
        if cached[1] is not None:
            rows.append(cached[1])
    return rows


def load_rows(results_dir: Path = RESULTS_DIR) -> list[dict]:
    """Every research variant and plain run as a row (unsorted; see `sort_rows`)."""
    results_dir = Path(results_dir)
    research, hidden = _research(results_dir)
    return research + _plain(results_dir, hidden)


# --- sorting, filtering, display -----------------------------------------------------------


def sort_rows(rows: list[dict]) -> list[dict]:
    """Default order: verdict (green first, no verdict last), then test net R, then development
    net R, both highest first (a missing test net R after the others)."""

    def key(r: dict):
        test = r.get("test_net_r")
        return (
            VERDICT_ORDER.get(r.get("verdict") or "", NO_VERDICT_RANK),
            test is None,
            -(test or 0.0),
            -(r.get("net_r") or 0.0),
        )

    return sorted(rows, key=key)


def filter_rows(
    rows: list[dict],
    strategy: str | None = None,
    symbol: str | None = None,
    flagged: str | None = None,
    min_trades: float | None = None,
) -> list[dict]:
    """Rows of one strategy / containing one symbol / (un)flagged / with at least `min_trades`."""
    out = []
    for r in rows:
        if strategy and r["strategy_name"] != strategy:
            continue
        if symbol and symbol not in r["symbol_list"]:
            continue
        if flagged == FILTER_UNFLAGGED and r["flag_keys"]:
            continue
        if flagged == FILTER_FLAGGED and not r["flag_keys"]:
            continue
        if min_trades and r["trades"] < min_trades:
            continue
        out.append(r)
    return out


def table_rows(rows: list[dict]) -> list[dict]:
    """The DataTable data: the row plus its display texts (`id` is the row id for clicks)."""
    out = []
    for r in rows:
        verdict = r["verdict"]
        label = f"{verdict} · {r['verdict_label']}" if verdict and r["verdict_label"] else verdict
        out.append(
            {
                **r, "id": r["source"], "verdict": label, "verdict_colour": verdict,
                "flags": flag_text(r["flag_keys"]), "flags_tooltip": flag_tooltip(r["flag_keys"]),
            }
        )  # fmt: skip
    return out
