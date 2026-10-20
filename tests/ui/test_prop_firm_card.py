"""The "Prop firm" card and the "Full Monte Carlo" block of the results page
(ui/prop_firm_card.py). Spec: risk-management.md > Prop-firm field (where it shows).
Jobs are faked: no process starts, no data is read."""

from __future__ import annotations

import csv
import json

import pytest
from dash import no_update

from backtester.risk import prop_card
from backtester.runner import TRADE_COLUMNS
from backtester.ui import monte_carlo_job as mj
from backtester.ui import prop_card_job as pj
from backtester.ui import prop_firm_card as pf
from backtester.ui.pages import results

RUN = "20261008-120000_XAUUSD"

OK_CARD = {
    "status": "ok", "label": "FTMO 2-Step", "trades": 400, "days": 300, "runs": 1000, "seed": 42,
    "funded_days": 126, "adaptive": {"floor": 0.25, "daily_budget": 0.03},
    "rows": [
        {"risk": 0.005, "attempts": 200, "passes": 50, "pass_probability": 0.25, "fail_daily": 40,
         "fail_max": 110, "median_days_to_pass": 31.0, "funded_observed": 40,
         "funded_lost_probability": 0.5},
        {"risk": 0.01, "attempts": 400, "passes": 40, "pass_probability": 0.1, "fail_daily": 300,
         "fail_max": 60, "median_days_to_pass": 12.0, "funded_observed": 30,
         "funded_lost_probability": 0.9},
        {"risk": 0.015, "attempts": 0, "passes": 0, "pass_probability": 0.0, "fail_daily": 0,
         "fail_max": 0, "median_days_to_pass": None, "funded_observed": 0,
         "funded_lost_probability": None},
    ],
    "adaptive_rows": [
        {"risk": 0.005, "attempts": 200, "passes": 120, "pass_probability": 0.6, "fail_daily": 0,
         "fail_max": 80, "median_days_to_pass": 44.0, "average_days_to_pass": 47.4,
         "skipped_trades": 50, "trades_seen": 1000, "funded_observed": 40,
         "funded_lost_probability": 0.125},
        {"risk": 0.01, "attempts": 400, "passes": 100, "pass_probability": 0.25, "fail_daily": 0,
         "fail_max": 300, "median_days_to_pass": 20.0, "average_days_to_pass": 22.6,
         "skipped_trades": 0, "trades_seen": 2000, "funded_observed": 30,
         "funded_lost_probability": 0.3},
        {"risk": 0.015, "attempts": 0, "passes": 0, "pass_probability": 0.0, "fail_daily": 0,
         "fail_max": 0, "median_days_to_pass": None, "average_days_to_pass": None,
         "skipped_trades": 0, "trades_seen": 0, "funded_observed": 0,
         "funded_lost_probability": None},
    ],
}  # fmt: skip
TOO_FEW = {"status": "too_few", "label": "FTMO 2-Step", "trades": 5, "days": 20,
           "reason": "Too little data for a meaningful estimate: 5 trades (at least 100 needed)."}  # fmt: skip


def text(component) -> str:
    return str(component)


@pytest.fixture(autouse=True)
def clean():
    mj.reset()
    pj.reset()
    yield
    mj.reset()
    pj.reset()


@pytest.fixture
def results_dir(tmp_path):
    folder = tmp_path / RUN
    folder.mkdir()
    row = dict.fromkeys(TRADE_COLUMNS, "")
    row.update(
        id=1, symbol="XAUUSD", direction="long", session="", entry_time="2026-09-02T08:05:00+00:00",
        entry_candle="2026-09-02T08:00:00+00:00", entry=100.0, initial_stop=99.0, tp1_share=1.0,
        take_profit=101.0, planned_rr=1.0, exit_time="2026-09-02T09:00:00+00:00", exit_price=101.0,
        exit_reason="take_profit", r_gross=1.0, r_net=1.0, confluence="fvg",
        parts=json.dumps([{"share": 1.0, "reason": "take_profit"}]),
    )  # fmt: skip
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRADE_COLUMNS)
        w.writeheader()
        w.writerow(row)
    (folder / "summary.json").write_text(
        json.dumps({"symbols": ["XAUUSD"], "start": "2026-09-01", "end": "2026-09-30"})
    )
    (folder / "settings.json").write_text("{}")
    return tmp_path


def ids(component) -> set[str]:
    found = set()

    def walk(c):
        if hasattr(c, "id") and c.id:
            found.add(c.id)
        kids = getattr(c, "children", None)
        for k in kids if isinstance(kids, list | tuple) else [kids]:
            if hasattr(k, "to_plotly_json"):
                walk(k)

    walk(component)
    return found


# ---- the card ----------------------------------------------------------------------------


def test_card_table_shows_the_five_numbers_at_each_risk():
    body = text(pf.card_body({"state": "ready", "card": OK_CARD}))
    for label in ("0.5 % risk", "1 % risk", "1.5 % risk", "Pass probability (both phases)",
                  "Failed: daily loss", "Failed: max loss", "Median days to pass",
                  "Funded account lost within 126 days"):  # fmt: skip
        assert label in body
    assert "25.0 %" in body and "10.0 %" in body  # pass probabilities
    assert "20 %" in body and "55 %" in body  # fails at 0.5 %: 40/200, 110/200
    assert "31" in body and "12" in body
    assert "50.0 %" in body and "90.0 %" in body  # funded lost
    assert "1,000" in body  # the estimate's reshuffles
    assert "reshuffl" in body and "conservative" in body  # the one-line explanation


def test_card_has_a_fixed_and_an_adaptive_column_per_risk():
    card = pf.card_body({"state": "ready", "card": OK_CARD})
    body = text(card)
    assert body.count("'Fixed'") == 3 and body.count("'Adaptive'") == 3
    for label in ("Average days to pass", "Trades skipped by the daily budget"):
        assert label in body
    assert "60.0 %" in body and "12.5 %" in body  # adaptive pass probability, funded lost
    assert "47" in body and "23" in body  # average days (47.4, 22.6)
    assert "5 %" in body  # 50 of 1000 trades skipped
    assert "colSpan=2" in body
    assert "13 %" not in body  # a fixed column does not show the skipped share


def test_card_without_adaptive_rows_still_renders_the_fixed_lines():
    old = {k: v for k, v in OK_CARD.items() if k not in ("adaptive_rows", "adaptive")}
    body = text(pf.card_body({"state": "ready", "card": old}))
    assert "25.0 %" in body and "Trades skipped" not in body


def test_a_risk_without_a_finished_attempt_shows_dashes():
    body = text(pf.card_body({"state": "ready", "card": OK_CARD}))
    assert "—" in body


def test_too_few_trades_shows_the_reason_and_no_numbers():
    body = text(pf.card_body({"state": "ready", "card": TOO_FEW}))
    assert TOO_FEW["reason"] in body
    assert "Pass probability" not in body and "% risk" not in body


def test_running_queued_and_error_states():
    assert "Calculating" in text(pf.card_body({"state": "running", "elapsed": 65.0}))
    assert "1:05" in text(pf.card_body({"state": "running", "elapsed": 65.0}))
    assert "Waiting" in text(pf.card_body({"state": "queued", "elapsed": 0.0}))
    err = text(pf.card_body({"state": "error", "message": "KeyError: boom"}))
    assert "KeyError: boom" in err


def test_timer_runs_only_while_something_is_computing():
    assert pf.timer_disabled({"state": "ready", "card": OK_CARD}) is True
    assert pf.timer_disabled({"state": "error", "message": "x"}) is True
    assert pf.timer_disabled({"state": "running", "elapsed": 1.0}) is False
    assert pf.timer_disabled({"state": "queued", "elapsed": 0.0}) is False


def test_poll_card_asks_the_job_for_the_run_folder(results_dir, monkeypatch):
    seen = []

    def fake_request(folder, firm, **kw):
        seen.append((folder.name, firm))
        return {"state": "ready", "card": OK_CARD}

    monkeypatch.setattr(pj, "request", fake_request)
    body, disabled = pf.poll_card(RUN, prop_card.DEFAULT_FIRM, results_dir)
    assert seen == [(RUN, "ftmo_2step")] and disabled is True and "Pass probability" in text(body)
    assert pf.poll_card(None, "ftmo_2step", results_dir) == (no_update, True)
    assert pf.poll_card("missing", "ftmo_2step", results_dir) == (no_update, True)


def test_layout_has_the_card_with_a_firm_dropdown_and_its_ids(results_dir):
    layout = pf.layout(RUN, results_dir / RUN, results_dir)
    for id_ in ("pf-firm", "pf-body", "pf-timer"):
        assert id_ in ids(layout)
    page = text(layout)
    assert "Prop firm" in page and "FTMO 2-Step" in page


def test_layout_shows_a_cached_card_at_once_and_starts_no_process(results_dir, monkeypatch):
    def no_start(*a, **k):
        raise AssertionError("a page build must not start a process")

    monkeypatch.setattr(pj, "request", no_start)
    monkeypatch.setattr(pj, "peek", lambda *a, **k: OK_CARD)
    layout = pf.layout(RUN, results_dir / RUN, results_dir)
    assert "Pass probability" in text(layout)
    timer = next(c for c in _walk(layout) if getattr(c, "id", None) == "pf-timer")
    assert timer.disabled is True


def test_layout_without_a_cache_polls_to_start_the_calculation(results_dir, monkeypatch):
    monkeypatch.setattr(pj, "peek", lambda *a, **k: None)
    layout = pf.layout(RUN, results_dir / RUN, results_dir)
    timer = next(c for c in _walk(layout) if getattr(c, "id", None) == "pf-timer")
    assert timer.disabled is False and "Calculating" in text(layout)


def _walk(c):
    yield c
    kids = getattr(c, "children", None)
    for k in kids if isinstance(kids, list | tuple) else [kids]:
        if hasattr(k, "to_plotly_json"):
            yield from _walk(k)


# ---- Full Monte Carlo --------------------------------------------------------------------


def snap(**kw):
    base = {"state": "idle", "report": False, "href": None, "detail": "", "percent": None,
            "elapsed": "", "message": ""}  # fmt: skip
    return {**base, **kw}


def test_block_has_the_button_cancel_open_link_and_progress_ids(results_dir):
    layout = pf.layout(RUN, results_dir / RUN, results_dir)
    for id_ in ("mc-start", "mc-cancel", "mc-open", "mc-status", "mc-fill", "mc-timer"):
        assert id_ in ids(layout)
    start = next(c for c in _walk(layout) if getattr(c, "id", None) == "mc-start")
    assert "Full Monte Carlo" in text(start)


def test_idle_offers_the_run_and_hides_cancel_and_open():
    o = pf.mc_outputs(snap())
    assert o["start_label"] == "Full Monte Carlo" and o["start_disabled"] is False
    assert o["cancel_style"] == {"display": "none"} and o["open_style"] == {"display": "none"}
    assert o["timer_disabled"] is True


def test_ready_offers_open_report_in_a_new_tab_and_run_again():
    o = pf.mc_outputs(snap(state="ready", report=True, href="/monte-carlo/r/report.html"))
    assert o["start_label"] == "Run again" and o["open_href"] == "/monte-carlo/r/report.html"
    assert o["open_style"] == {} and o["timer_disabled"] is True


def test_running_shows_progress_cancel_and_disables_start():
    o = pf.mc_outputs(snap(state="running", detail="Kind D · random price paths · X path 3/20",
                           percent=15.0, elapsed="2:05"))  # fmt: skip
    assert o["start_disabled"] is True and o["cancel_style"] == {}
    assert o["timer_disabled"] is False
    assert "Kind D" in o["status"] and "2:05" in o["status"]
    assert o["fill_style"] == {"width": "15.0%"} and o["track_style"] == {}


def test_running_without_a_percent_shows_an_indeterminate_bar():
    o = pf.mc_outputs(snap(state="running", detail="Kind A", elapsed="0:10"))
    assert o["track_class"] == "mc-track mc-loading"


def test_busy_error_and_cancelled_texts():
    busy = pf.mc_outputs(snap(state="busy", message="Another Monte Carlo is running (x)."))
    assert busy["start_disabled"] is True and "Another Monte Carlo" in busy["status"]
    assert busy["timer_disabled"] is False  # follows the other run to its end
    err = pf.mc_outputs(snap(state="error", message="ValueError: no data"))
    assert "ValueError: no data" in err["status"] and err["start_disabled"] is False
    assert "cancelled" in pf.mc_outputs(snap(state="cancelled", message="Monte Carlo cancelled.")
                                        )["status"]  # fmt: skip


def test_press_start_starts_the_job_for_the_run(results_dir, monkeypatch):
    started = []
    monkeypatch.setattr(mj, "start", lambda run, rd, **kw: started.append((run, rd)))
    assert pf.press_start(1, RUN, results_dir) is True
    assert started == [(RUN, results_dir)]
    assert pf.press_start(0, RUN, results_dir) is False
    assert pf.press_start(None, RUN, results_dir) is False


def test_press_start_while_another_runs_or_for_a_bad_run_does_nothing(results_dir, monkeypatch):
    def refuse(*a, **k):
        raise mj.AlreadyRunning("busy")

    monkeypatch.setattr(mj, "start", refuse)
    assert pf.press_start(1, RUN, results_dir) is False

    def missing(*a, **k):
        raise mj.RunNotFound("no")

    monkeypatch.setattr(mj, "start", missing)
    assert pf.press_start(1, "nope", results_dir) is False


def test_press_cancel_stops_the_running_job(monkeypatch):
    calls = []
    monkeypatch.setattr(mj, "cancel", lambda: calls.append(1) or True)
    assert pf.press_cancel(1) is True and pf.press_cancel(0) is False and len(calls) == 1


# ---- on the results page -----------------------------------------------------------------


def test_every_results_page_has_the_prop_firm_card_and_the_button(results_dir, monkeypatch):
    monkeypatch.setattr(pj, "peek", lambda *a, **k: None)
    page = results.layout(RUN, results_dir)
    for id_ in ("pf-body", "pf-firm", "mc-start", "mc-open", "rs-tab", "rs-content"):
        assert id_ in ids(page)


def test_a_missing_run_has_no_card(results_dir):
    assert "pf-body" not in ids(results.layout("missing", results_dir))
