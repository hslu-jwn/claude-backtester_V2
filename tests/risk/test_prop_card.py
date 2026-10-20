"""Prop-firm card numbers and cache. Spec: risk-management.md > Prop-firm field (where it
shows) and > Monte Carlo (A, FTMO 2-Step). Hand-built trade lists with obvious answers."""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.risk import prop_card as pc
from backtester.risk.monte_carlo import MonteCarloConfig, weekdays
from backtester.runner import TRADE_COLUMNS

FAST = pc.FirmPreset("FTMO 2-Step", MonteCarloConfig(runs=40, fan_paths=0))
CARD = pc.PropCardConfig(min_trades=20, min_days=40)
START, END = date(2026, 1, 5), date(2026, 8, 31)  # a Monday .. a Monday (> 126 + 8 days)


def daily(r_net: float, days: list[date] | None = None) -> list:
    """One trade per weekday, 10:00 -> 11:00 UTC, the same net R."""
    out = []
    for d in days or weekdays(START, END):
        t0 = datetime(d.year, d.month, d.day, 10, tzinfo=UTC)
        out.append(SimpleNamespace(entry_time=t0, exit_time=t0 + timedelta(hours=1), r_net=r_net))
    return out


def by_risk(card: dict) -> dict:
    return {row["risk"]: row for row in card["rows"]}


def test_always_winning_days_pass_every_attempt_in_a_known_number_of_days():
    # +2 R per day: 1 % risk = +2 % a day, so P1 (+10 %) takes 5 days and P2 (+5 %) 3 days, but
    # every phase needs at least 4 trading days: 5 + 4 = 9. At 0.5 %: 10 + 5, at 1.5 %: 4 + 4.
    card = pc.compute_card(daily(2.0), START, END, FAST, CARD)
    assert card["status"] == "ok"
    rows = by_risk(card)
    assert list(rows) == [0.005, 0.01, 0.015]
    for risk, days in ((0.005, 15), (0.01, 9), (0.015, 8)):
        row = rows[risk]
        assert row["pass_probability"] == 1.0
        assert row["fail_daily"] == row["fail_max"] == 0
        assert row["median_days_to_pass"] == days
        assert row["funded_observed"] > 0 and row["funded_lost_probability"] is not None


def test_always_losing_days_fail_on_max_loss_and_show_no_pass_numbers():
    card = pc.compute_card(daily(-1.0), START, END, FAST, CARD)
    for row in card["rows"]:
        assert row["passes"] == 0 and row["pass_probability"] == 0.0
        assert row["fail_daily"] == 0 and row["fail_max"] == row["attempts"] > 0
        assert row["median_days_to_pass"] is None
        assert row["funded_lost_probability"] is None  # no funded account was ever watched


def test_attempts_split_into_passes_and_both_fail_kinds():
    trades = daily(1.0)
    for t in trades[::7]:
        t.r_net = -4.0
    card = pc.compute_card(trades, START, END, FAST, CARD)
    for row in card["rows"]:
        assert row["attempts"] > 0
        assert row["passes"] + row["fail_daily"] + row["fail_max"] == row["attempts"]
        assert row["pass_probability"] == pytest.approx(row["passes"] / row["attempts"])


def test_same_seed_same_numbers():
    trades = daily(1.0)
    for t in trades[::5]:
        t.r_net = -2.0
    assert pc.compute_card(trades, START, END, FAST, CARD) == pc.compute_card(
        trades, START, END, FAST, CARD
    )


def test_too_few_trades_or_days_gives_a_message_and_no_numbers():
    few = pc.compute_card(daily(1.0)[:5], START, END, FAST, CARD)
    assert few["status"] == "too_few" and "5 trades" in few["reason"] and "rows" not in few
    days = weekdays(date(2026, 3, 2), date(2026, 3, 13))
    short = pc.compute_card(daily(1.0, days), date(2026, 3, 2), date(2026, 3, 13), FAST, CARD)
    assert short["status"] == "too_few" and "10 trading days" in short["reason"]
    assert pc.compute_card([], START, END, FAST, CARD)["status"] == "too_few"


def test_defaults_are_a_real_challenge_length():
    c = pc.PropCardConfig()
    assert c.min_trades >= 30 and c.min_days >= 60


def test_card_is_plain_json():
    card = pc.compute_card(daily(2.0), START, END, FAST, CARD)
    assert json.loads(json.dumps(card)) == card


def test_firm_presets_hold_ftmo_two_step_first():
    assert next(iter(pc.FIRMS)) == pc.DEFAULT_FIRM == "ftmo_2step"
    assert pc.FIRMS[pc.DEFAULT_FIRM].mc.risk_levels == (0.005, 0.01, 0.015)


# ---- cache -------------------------------------------------------------------------------


def write_run(folder, n=60, r=1.0, start=START, end=END):
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, t in enumerate(daily(r, weekdays(start, end))[:n], 1):
        row = dict.fromkeys(TRADE_COLUMNS, "")
        row.update(
            id=i, symbol="XAUUSD", direction="long", session="", entry_time=t.entry_time.isoformat(),
            entry_candle=t.entry_time.isoformat(), entry=100.0, initial_stop=99.0,
            take_profit=101.0, tp1_share=1.0, planned_rr=1.0, exit_time=t.exit_time.isoformat(),
            exit_price=101.0, exit_reason="take_profit", r_gross=r, r_net=r, confluence="fvg",
            parts=json.dumps([{"share": 1.0, "reason": "take_profit"}]),
        )  # fmt: skip
        rows.append(row)
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRADE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = {"start": start.isoformat(), "end": end.isoformat()}
    (folder / "summary.json").write_text(json.dumps(summary))
    return folder


@pytest.fixture
def counted(monkeypatch):
    calls = []
    real = pc.compute_card

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(pc, "compute_card", spy)
    return calls


def test_card_is_written_once_and_reused(tmp_path, counted):
    run = write_run(tmp_path / "run1")
    assert pc.cached_card(run, "ftmo_2step", FAST, CARD) is None
    first = pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    assert (run / "prop_firm.json").is_file() and len(counted) == 1
    assert first["status"] == "ok"
    assert pc.cached_card(run, "ftmo_2step", FAST, CARD) == first
    assert pc.ensure_card(run, "ftmo_2step", FAST, CARD) == first
    assert len(counted) == 1


def test_changed_settings_or_trades_recompute(tmp_path, counted):
    run = write_run(tmp_path / "run1")
    pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    other_mc = pc.FirmPreset("FTMO 2-Step", replace(FAST.mc, seed=7))
    assert pc.cached_card(run, "ftmo_2step", other_mc, CARD) is None
    pc.ensure_card(run, "ftmo_2step", other_mc, CARD)
    assert len(counted) == 2
    other_card = pc.PropCardConfig(min_trades=21, min_days=40)
    assert pc.cached_card(run, "ftmo_2step", other_mc, other_card) is None
    write_run(run, n=59)  # the trade list changed
    assert pc.cached_card(run, "ftmo_2step", other_mc, CARD) is None


def test_cache_holds_several_firms_side_by_side(tmp_path, monkeypatch):
    run = write_run(tmp_path / "run1")
    monkeypatch.setitem(pc.FIRMS, "other", FAST)
    pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    pc.ensure_card(run, "other", FAST, CARD)
    data = json.loads((run / "prop_firm.json").read_text())
    assert set(data["entries"]) == {"ftmo_2step", "other"}
    assert pc.cached_card(run, "ftmo_2step", FAST, CARD) is not None


@pytest.mark.parametrize(
    "junk", ["", "not json", "[]", '{"entries": 5}', '{"entries": {"ftmo_2step": 3}}']
)
def test_broken_cache_file_is_ignored_and_rewritten(tmp_path, counted, junk):
    run = write_run(tmp_path / "run1")
    (run / "prop_firm.json").write_text(junk)
    assert pc.cached_card(run, "ftmo_2step", FAST, CARD) is None
    card = pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    assert card["status"] == "ok" and len(counted) == 1
    assert pc.cached_card(run, "ftmo_2step", FAST, CARD) == card


def test_unknown_firm_is_an_error(tmp_path):
    run = write_run(tmp_path / "run1")
    with pytest.raises(KeyError):
        pc.ensure_card(run, "nope")


def test_cli_writes_the_cache(tmp_path, monkeypatch):
    run = write_run(tmp_path / "run1")
    monkeypatch.setitem(pc.FIRMS, "ftmo_2step", FAST)
    monkeypatch.setattr(pc, "DEFAULT_CARD", CARD)
    assert pc.main(["run1", "--results-dir", str(tmp_path)]) == 0
    assert (run / "prop_firm.json").is_file()
    assert pc.main(["missing", "--results-dir", str(tmp_path)]) == 1


# ---- fixed vs adaptive (ROADMAP 5.7) -----------------------------------------------------


def test_card_has_a_fixed_and_an_adaptive_line_per_base_risk():
    card = pc.compute_card(daily(2.0), START, END, FAST, CARD)
    fixed, adaptive = card["rows"], card["adaptive_rows"]
    assert [r["risk"] for r in adaptive] == [r["risk"] for r in fixed] == [0.005, 0.01, 0.015]
    for row in fixed + adaptive:
        assert row["average_days_to_pass"] == row["median_days_to_pass"]  # all attempts equal
    # always winning: the account is in profit, the factor is capped at 1, nothing is cut
    # (one trade a day, 2 % at most) -> adaptive equals fixed
    for f, a in zip(fixed, adaptive, strict=True):
        assert (a["pass_probability"], a["median_days_to_pass"]) == (
            f["pass_probability"], f["median_days_to_pass"])  # fmt: skip
        assert a["skipped_trades"] == 0 and a["trades_seen"] > 0
    assert card["adaptive"] == {"floor": 0.25, "daily_budget": 0.03}


def test_adaptive_slows_a_losing_account_down():
    card = pc.compute_card(daily(-1.0), START, END, FAST, CARD)
    for f, a in zip(card["rows"], card["adaptive_rows"], strict=True):
        assert f["attempts"] > 0 and a["attempts"] > 0
        assert a["attempts"] < f["attempts"]  # each attempt takes longer to fail


def test_adaptive_budget_skips_trades_and_is_reported():
    # three trades at the same time every day, 1.5 % risk: the 3 % budget lets two (and a
    # part of a third) through; the third is cut, not skipped, so skipped may stay 0 - use 4
    def four_a_day(r):
        out = []
        for d in weekdays(START, END):
            t0 = datetime(d.year, d.month, d.day, 10, tzinfo=UTC)
            out += [
                SimpleNamespace(entry_time=t0, exit_time=t0 + timedelta(hours=1), r_net=r)
                for _ in range(4)
            ]
        return out

    card = pc.compute_card(four_a_day(0.2), START, END, FAST, CARD)
    top = card["adaptive_rows"][2]  # 1.5 % risk: 4 x 1.5 % wants 6 % of the day
    assert top["skipped_trades"] > 0 and top["skipped_trades"] < top["trades_seen"]
    assert card["adaptive_rows"][0]["skipped_trades"] == 0  # 0.5 % x 4 = 2 % fits


def test_adaptive_settings_are_part_of_the_cache_key(tmp_path):
    from backtester.risk.adaptive import AdaptiveRisk

    run = write_run(tmp_path / "run1")
    base = pc.cache_key(run, "ftmo_2step", FAST, CARD)
    other = pc.FirmPreset(FAST.label, FAST.mc, AdaptiveRisk(floor=0.5))
    assert pc.cache_key(run, "ftmo_2step", other, CARD) != base
    assert pc.CARD_VERSION >= 3
