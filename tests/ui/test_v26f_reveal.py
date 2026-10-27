"""Full-check finding 1: reveal belongs to a complete selected trade identity."""

from types import SimpleNamespace

import pytest

from backtester.ui import review_callbacks as callbacks


@pytest.mark.parametrize("change", ["next", "symbol", "direction", "entry_time", "index"])
def test_reveal_resets_on_selection_identity_change(tmp_path, monkeypatch, change):
    order = {
        "symbol": "XAUUSD",
        "direction": "long",
        "entry_time": "2020-01-01T10:00:00Z",
        "entry": 100,
        "sl": 99,
        "tp": 102,
        "exit_time": "2020-01-01T11:00:00Z",
        "exit": 102,
    }
    orders = [order.copy(), order.copy()]  # simultaneous, even identical trade identities
    monkeypatch.setattr(
        callbacks, "review_orders", lambda *a: [SimpleNamespace(order=o, r_net=2) for o in orders]
    )
    monkeypatch.setattr(callbacks.trade_focus, "inspection_order", lambda t: t.order)
    args = ("XAUUSD", "2020-01-01", "2020-01-02", "{}", "gap_fade")
    state = callbacks.transition(None, "run", None, *args, folder=tmp_path)[0]
    state = callbacks.transition(None, "reveal", state, *args, folder=tmp_path)[0]
    assert state["revealed"]
    action = "next" if change == "next" else "settings"
    if change in {"symbol", "direction", "entry_time"}:
        orders[0][change] = {
            "symbol": "US500",
            "direction": "short",
            "entry_time": "2020-01-01T10:01:00Z",
        }[change]
    elif change == "index":
        state["index"] = 99  # clamped back to the last trade
    state = callbacks.transition(None, action, state, *args, folder=tmp_path)[0]
    assert not state["revealed"]
    # review.decision_order documents hidden outcomes as null fields.
    assert state["order"]["exit_time"] is None
    assert state["order"]["exit"] is None
