"""I-145 fill model: hand-built trade frames only (knowledge/ideas.md › I-145)."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_PATH = Path(__file__).resolve().parents[2] / "research" / "screens" / "2026-11-26_i145_fill_model.py"
_spec = importlib.util.spec_from_file_location("i145_fill_model", _PATH)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

WAIT = 10_000


def frame(rows):
    """(ms after Monday 00:00, price, aggressor) with aggressor 'b' = buyer takes (is_buyer_maker False)."""
    return pd.DataFrame(
        {
            "transact_time": [r[0] for r in rows],
            "price": [r[1] for r in rows],
            "is_buyer_maker": [r[2] == "s" for r in rows],
        }
    )


def test_taker_skips_trade_inside_latency():
    d = frame([(500, 100.0, "b"), (1000, 101.0, "b"), (1500, 99.0, "s")])
    tk, _, _ = m.fill_order(d, 1, 100.0, 0, WAIT, 1, 1.0)
    assert tk == pytest.approx(100.0)  # buys at 101, the 00:00:00.500 print is skipped
    tk, _, _ = m.fill_order(d, -1, 100.0, 0, WAIT, 1, 1.0)
    assert tk == pytest.approx(100.0)  # sell at 99 is 100 bp worse than P0


def test_print_exactly_at_p0_does_not_fill():
    d = frame([(2000, 100.0, "s"), (WAIT + 1, 101.0, "b")])
    _, mk, filled = m.fill_order(d, 1, 100.0, 0, WAIT, 1, 0.5)
    assert not filled
    assert mk == pytest.approx(100.0)  # taker after the window at 101


def test_one_tick_through_fills_and_two_tick_rule_does_not():
    d = frame([(2000, 99.5, "s"), (WAIT + 1, 101.0, "b")])
    _, mk, filled = m.fill_order(d, 1, 100.0, 0, WAIT, 1, 0.5)
    assert filled and mk == 0.0
    _, mk2, filled2 = m.fill_order(d, 1, 100.0, 0, WAIT, 2, 0.5)
    assert not filled2 and mk2 == pytest.approx(100.0)


def test_sell_maker_needs_price_above_p0():
    d = frame([(2000, 100.5, "b"), (WAIT + 1, 99.0, "s")])
    _, mk, filled = m.fill_order(d, -1, 100.0, 0, WAIT, 1, 0.5)
    assert filled and mk == 0.0


def test_fill_before_latency_or_after_window_does_not_count():
    d = frame([(500, 99.0, "s"), (WAIT, 99.0, "s"), (WAIT + 5, 101.0, "b")])
    _, _, filled = m.fill_order(d, 1, 100.0, 0, WAIT, 1, 1.0)
    assert not filled  # 0.5 s is inside the latency, the print at WAIT is outside the window


def test_unfilled_maker_without_later_trade_is_nan():
    d = frame([(2000, 100.0, "s")])
    _, mk, filled = m.fill_order(d, 1, 100.0, 0, WAIT, 1, 0.5)
    assert not filled and np.isnan(mk)


def test_tick_inferred_from_price_steps():
    assert m.tick_of(pd.Series([100.0, 100.3, 100.1, 100.1, 100.4])) == pytest.approx(0.1)
    assert m.tick_of(pd.Series([5.0, 5.0])) != m.tick_of(pd.Series([5.0, 5.0]))  # NaN: no step


def test_cost_sign_for_buys_and_sells():
    assert m.slip_bp(1, 101.0, 100.0) == pytest.approx(100.0)  # buy above P0 costs
    assert m.slip_bp(1, 99.0, 100.0) == pytest.approx(-100.0)
    assert m.slip_bp(-1, 99.0, 100.0) == pytest.approx(100.0)  # sell below P0 costs
    assert m.slip_bp(-1, 101.0, 100.0) == pytest.approx(-100.0)


def test_orders_leave_enter_flip_stay():
    prev = {"A": 1, "B": -1, "C": 1, "D": 1, "E": -1}
    cur = {"A": 0, "B": 0, "C": -1, "D": 1, "F": 1, "G": -1}
    got = m.derive_orders(prev, cur)
    assert got == {"A": -1, "B": 1, "C": -1, "E": 1, "F": 1, "G": -1}  # D stays: no order


def test_book_from_legs_maps_sides_and_weeks():
    mon = pd.Timestamp("2023-01-02", tz="UTC")
    legs = [
        {"week": mon, "symbol": "A", "side": "long"},
        {"week": mon, "symbol": "B", "side": "short"},
    ]
    assert m.books(legs) == {mon.date(): {"A": 1, "B": -1}}


def test_mondays_cover_2023_and_2026_window():
    ms = m.mondays()
    assert len(ms) == 78
    assert ms[0].isoformat() == "2023-01-02" and ms[-1].isoformat() == "2026-10-19"
    assert all(d.weekday() == 0 for d in ms)


def test_clustered_t_is_by_monday():
    r = pd.DataFrame({"monday": [1, 1, 2, 2, 3, 3], "saving": [2.0, 2.0, 4.0, 4.0, 3.0, 3.0]})
    mean, t = m.clustered(r)
    assert mean == pytest.approx(3.0)
    assert t == pytest.approx(3.0 / (1.0 / np.sqrt(3)))


def test_read_trades_filters_window_and_columns(tmp_path):
    p = tmp_path / "x.csv"
    t0 = 1_000_000
    pd.DataFrame(
        {
            "agg_trade_id": [1, 2, 3],
            "price": [1.0, 2.0, 3.0],
            "quantity": [1, 1, 1],
            "transact_time": [t0, t0 + 1000, t0 + m.READ_MS],
            "is_buyer_maker": [True, False, True],
        }
    ).to_csv(p, index=False)
    d = m.read_trades(p, t0)
    assert list(d.columns) == ["price", "transact_time", "is_buyer_maker"]
    assert list(d.price) == [1.0, 2.0]
