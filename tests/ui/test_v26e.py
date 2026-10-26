"""V2.6 step 5: review transport, labels, inspection and development heatmaps."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from backtester.ui import review
from backtester.ui.parameter_heatmap import heatmap, varied_parameters
from backtester.ui.strong_move import filter_mode, filter_values


def order(minute=0):
    return {
        "symbol": "XAUUSD",
        "direction": "LONG",
        "entry_time": f"2020-01-01T10:{minute:02}:00Z",
        "entry": 100.0,
        "sl": 99.0,
        "tp": 102.0,
        "exit_time": "2020-01-01T11:00:00Z",
        "exit": 102.0,
    }


def test_labels_round_trip_last_label_wins(tmp_path):
    a = review.label("gap_fade", order(), "a", "take", "first", 103)
    b = review.label("gap_fade", order(), "b", "skip", "changed")
    review.save_label(a, tmp_path)
    review.save_label(b, tmp_path)
    assert review.load_labels("gap_fade", tmp_path) == [b]
    assert len((tmp_path / "gap_fade.jsonl").read_text().splitlines()) == 2
    assert a["own_tp"] == 103 and a["reason"] == "first"
    assert a["label_time"].endswith("Z")
    assert review.key(a) == review.key(b)


@pytest.mark.parametrize(
    "choice,reason,tp", [("maybe", "", None), ("take", "x" * 201, None), ("skip", "", float("nan"))]
)
def test_invalid_labels(choice, reason, tp):
    with pytest.raises(ValueError):
        review.label("gap_fade", order(), "a", choice, reason, tp)


def test_agreement_rule_change_removes_one_take_and_one_skip():
    labels = [
        review.label("gap_fade", order(i), "old", choice)
        for i, choice in enumerate(["take", "take", "skip", "skip"])
    ]
    current = [order(0), order(2)]
    result = review.agreement(labels, "gap_fade", current)
    assert result == {"total": 4, "take_exists": 1, "skip_absent": 1, "agreed": 2, "percent": 50.0}
    assert review.agreement([], "gap_fade", [])["percent"] is None


def test_review_payload_never_serializes_future_candles(monkeypatch):
    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.pages import chart

    start = datetime(2020, 1, 1, 10, tzinfo=UTC)
    candles = [Candle(start + timedelta(minutes=5 * i), 100, 101 + i, 99, 100, 1) for i in range(4)]
    replay = Replay(CandleSeries("XAUUSD", Timeframe.M5, candles))
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))
    state = {"entry_time": "2020-01-01T10:10:00Z", "revealed": False}
    payload, _ = chart.base_payload(
        None, "XAUUSD", "M5", "2020-01-01", "2020-01-01", review_state=state
    )
    assert len(payload["candles"]["t"]) == 2
    assert "103" not in json.dumps(payload["candles"])
    state["revealed"] = True
    payload, _ = chart.base_payload(
        None, "XAUUSD", "M5", "2020-01-01", "2020-01-01", review_state=state
    )
    assert len(payload["candles"]["t"]) == 4


def test_review_navigation_and_decision_order():
    assert review.navigate(0, "previous", 3, set()) == 0
    assert review.navigate(2, "next", 3, set()) == 2
    assert review.navigate(2, "unlabelled", 3, {0, 2}) == 1
    assert review.navigate(0, "next", 0, set()) is None
    hidden = review.decision_order(order(), False)
    assert hidden["exit_time"] is None and hidden["exit"] is None
    assert review.decision_order(order(), True) == order()


def test_heatmap_fixes_third_parameter_and_preserves_holes():
    rows = [
        dict(variant_id=vid, **{"set.x": x, "set.y": y, "set.z": z}, net_r=r)
        for vid, x, y, z, r in [
            ("a", 1, 1, 0, -2),
            ("b", 2, 1, 0, 4),
            ("c", 1, 2, 0, 0),
            ("d", 2, 2, 1, 99),
        ]
    ]
    assert varied_parameters(rows) == ["set.x", "set.y", "set.z"]
    fig = heatmap(rows, "a", "set.x", "set.y", "net_r")
    assert list(map(list, fig.data[0].z)) == [[-2, 4], [0, None]]
    assert fig.data[0].zmid == 0
    assert "set.z" in fig.data[0].text[0][0]
    assert list(fig.data[1].x) == ["1"] and list(fig.data[1].y) == ["1"]
    with pytest.raises(ValueError):
        heatmap(rows, "a", "set.x", "set.x", "net_r")


@pytest.mark.parametrize(
    "mode,expected", [("off", []), ("fvg", ["fvg"]), ("ob", ["ob"]), ("both", ["fvg", "ob"])]
)
def test_dropdown_exact_mapping(mode, expected):
    from backtester.ui import settings_panel as sp

    assert filter_values(mode) == expected
    assert filter_mode(expected) == mode
    update = sp.form_update(
        "field",
        {
            "detectors.fvg.strong_move_filter": ["on"] if "fvg" in expected else [],
            "detectors.order_block.strong_move_filter": ["on"] if "ob" in expected else [],
        },
        None,
    )
    assert not update["error"]
    detectors = sp.store_settings(update["store"]).detectors
    assert detectors.fvg.strong_move_filter == ("fvg" in expected)
    assert detectors.order_block.strong_move_filter == ("ob" in expected)


def test_review_overlay_and_order_respect_entry_ceiling(monkeypatch):
    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.pages import chart

    start = datetime(2020, 1, 1, 10, tzinfo=UTC)
    replay = Replay(
        CandleSeries(
            "XAUUSD",
            Timeframe.M5,
            [Candle(start + timedelta(minutes=5 * i), 100, 101, 99, 100) for i in range(4)],
        )
    )
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))
    state = {
        "entry_time": "2020-01-01T10:10:00Z",
        "revealed": False,
        "order": review.decision_order(dict(order(10), direction="long"), False),
    }
    key = chart.review_key(chart.chart_key("XAUUSD", "M5", "2020-01-01", "2020-01-01"), state)
    payload = chart.overlay_payload(
        None,
        {"key": key, "cursor": 3, "types": [], "filters": "off"},
        "XAUUSD",
        "M5",
        "2020-01-01",
        "2020-01-01",
        [],
        review_state=state,
    )
    assert payload["cursor"] == 1
    drawn = chart.order_draw_payload(
        None, order(15), "XAUUSD", "M5", "2020-01-01", "2020-01-01", review_state=state
    )
    assert all(d.get("x1", 0) <= 1 for d in drawn["items"] if d.get("x1") is not None)
    assert all(i["order"]["exit_time"] is None for i in drawn["inspections"])
    assert (
        chart.replay_delta(None, {"key": key, "cursor": 1}, replay, 3, key, [], review_state=state)
        is None
    )


def test_inspection_draws_only_clicked_trade(monkeypatch):
    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.pages import chart

    start = datetime(2020, 1, 1, 10, tzinfo=UTC)
    replay = Replay(
        CandleSeries(
            "XAUUSD",
            Timeframe.M5,
            [Candle(start + timedelta(minutes=5 * i), 100, 104, 98, 100) for i in range(24)],
        )
    )
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))
    clicked = dict(order(10), direction="long", tps=[101, 102], reason="recorded reason")
    drawn = chart.order_draw_payload(
        None, clicked, "XAUUSD", "M5", "2020-01-01", "2020-01-01", run_trades=[object(), object()]
    )
    assert len(drawn["inspections"]) == 1
    assert drawn["inspections"][0]["order"] == clicked
    labels = [d.get("s", "") for d in drawn["items"] if d["k"] == "t"]
    assert any("101.00" in label for label in labels)
    assert any("102.00" in label for label in labels)


def test_review_transition_hides_outcome_resets_reveal_and_records_labels(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from backtester.ui import review_callbacks as callbacks
    from backtester.ui import trade_focus

    orders = [dict(order(i), direction="long") for i in [5, 10]]
    monkeypatch.setattr(
        callbacks, "review_orders", lambda *a: [SimpleNamespace(i=i, r_net=9) for i in range(2)]
    )
    monkeypatch.setattr(trade_focus, "inspection_order", lambda t: orders[t.i])
    args = ("XAUUSD", "2020-01-01", "2020-01-01", '{"x":1}', "gap_fade")
    result = callbacks.transition(None, "run", None, *args, folder=tmp_path)
    state = result[0]
    assert state["order"]["exit"] is None and "r_net" not in json.dumps(state)
    revealed = callbacks.transition(None, "reveal", state, *args, folder=tmp_path)[0]
    assert revealed["order"]["exit"] == 102
    next_state = callbacks.transition(None, "next", revealed, *args, folder=tmp_path)[0]
    assert not next_state["revealed"] and next_state["order"]["exit"] is None
    callbacks.transition(
        None, "skip", next_state, *args, reason="test", own_tp=104, folder=tmp_path
    )
    assert review.load_labels("gap_fade", tmp_path)[0]["choice"] == "skip"
    rows = review.history(
        "gap_fade",
        "second",
        {"total": 1, "take_exists": 0, "skip_absent": 0, "agreed": 0, "percent": 0.0},
        tmp_path,
    )
    assert len(rows) == 2


def test_inspection_replay_callback_starts_fifty_candles_before_entry(monkeypatch, tmp_path):
    from dash import Dash

    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.chart_config import DEFAULT_CONFIG
    from backtester.ui.pages import chart
    from backtester.ui.review_callbacks import register_callbacks

    start = datetime(2020, 1, 1, 10, tzinfo=UTC)
    replay = Replay(
        CandleSeries(
            "XAUUSD",
            Timeframe.M5,
            [Candle(start + timedelta(minutes=5 * i), 100, 104, 98, 100) for i in range(100)],
        )
    )
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))
    app = Dash(__name__)
    register_callbacks(app, None, DEFAULT_CONFIG, tmp_path)
    callback = next(
        c["callback"].__wrapped__
        for c in app.callback_map.values()
        if any(i["id"] == "inspection-replay" for i in c["inputs"])
    )
    selected = dict(order(), entry_time=review.utc(replay.close_time(70)))
    state, mode, _style = callback(1, 50, selected, "XAUUSD", "M5", {}, None)
    assert state["now"] == review.utc(replay.close_time(20))
    assert state["start"] == state["now"] and mode == {"on": True, "picking": False}
    state, _, _ = callback(1, 10, selected, "XAUUSD", "M5", {}, None)
    assert state["now"] == review.utc(replay.close_time(60))


def test_unavailable_trade_overlay_still_returns_chart_message(monkeypatch):
    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.overlays import OverlayUnavailable
    from backtester.ui.pages import chart

    replay = Replay(
        CandleSeries(
            "XAUUSD", Timeframe.M5, [Candle(datetime(2020, 1, 1, tzinfo=UTC), 100, 101, 99, 100)]
        )
    )
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))

    def unavailable(*args):
        raise OverlayUnavailable("Pick a shorter range")

    monkeypatch.setattr(chart, "_cached_events", unavailable)
    key = chart.chart_key("XAUUSD", "M5", "2020-01-01", "2020-01-01")
    payload = chart.overlay_payload(
        None,
        {"key": key, "cursor": 0, "types": ["trades"], "filters": []},
        "XAUUSD",
        "M5",
        "2020-01-01",
        "2020-01-01",
        [],
    )
    assert "Pick a shorter range" in str(payload["messages"])
    assert payload["inspections"] == []
