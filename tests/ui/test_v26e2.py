"""Look/layout regressions; callbacks tested without starting an app."""

import pytest
from dash import Dash
from test_chart_page import cache  # noqa: F401
from test_live_page import NOW, status, text_of

from backtester.ui import live_model as lm
from backtester.ui import trades_overlay
from backtester.ui.pages import chart, live, research


def nodes(value):
    if isinstance(value, (list, tuple)):
        for child in value:
            yield from nodes(child)
    elif hasattr(value, "to_plotly_json"):
        yield value
        yield from nodes(getattr(value, "children", None))


@pytest.mark.parametrize("age", [0, 300])
def test_fresh_live_unchanged(age):
    view = {"status": status(age), "state": "running", "age": age, "log": []}
    cards = text_of(live.render_cards(view))
    assert "MT5 connected" in cards
    assert "last session" not in cards


@pytest.mark.parametrize("heartbeat", ["2026-01-11T23:30:00Z", None, "broken"])
def test_stale_live_retains_numbers_without_connected_claim(heartbeat):
    saved = status(heartbeat=heartbeat, symbols=["US500"])
    view = {"status": saved, "state": "stale", "age": 600, "log": []}
    pieces = live.render(view, NOW)
    cards = text_of(pieces["cards"])
    assert "Not running · last seen" in cards
    assert "connected" not in cards.lower()
    assert "$100,000" in cards and "-1.00 %" in cards
    assert "last session 2026-01-12" in cards
    assert "last session 2026-01-12" in text_of(pieces["setup"])
    muted = [n for n in nodes(pieces["cards"]) if "lv-last-session" in getattr(n, "className", "")]
    assert len(muted) >= 2


def test_live_display_threshold_and_empty_state(tmp_path):
    assert lm.DISPLAY_STALE_MINUTES == 5
    assert not lm.display_stale(status(301), NOW, 10)
    assert lm.display_stale(status(301), NOW, 5)
    assert not lm.display_stale(None, NOW)
    cards = text_of(live.render_cards(live.live_view(tmp_path, NOW)))
    assert "Not running · last seen" not in cards
    assert "last session" not in cards


@pytest.mark.parametrize("filled", [False, True])
def test_research_partition_counts_order_and_no_loss(filled):
    fields = (*research.CHIPS, *research.TILES)
    row = {"href": "/results/x", "source": "x", "trades": 0, "net_r": 2}
    if filled:
        row.update({key: (1 if digits is not None else "value") for _, key, digits, _ in fields})
        row.update(n=5, n_eff=4)
    component = research.card(row)
    body = component.children[1]
    shown = body.children[0].children
    folds = [
        n
        for n in nodes(body)
        if getattr(n, "open", None) is False
        and str(getattr(n, "children", "")).find("Not computed yet") >= 0
    ]
    missing = [] if filled else [f[0] for f in fields if f[1] not in row] + ["N / N_eff"]
    labels = [n.children[0].children for n in shown]
    assert labels == (
        [f[0] for f in fields if f[0] not in missing] + ([] if missing else ["N / N_eff"])
    )
    if missing:
        assert len(folds) == 1
        assert folds[0].children[0].children == f"Not computed yet ({len(missing)})"
        hidden = folds[0].children[1].children
        assert [n.children[0].children for n in hidden] == missing
        assert len(shown) + len(hidden) == len(fields) + 1
        assert body.children[-1] is folds[0]
    else:
        assert not folds
    chips = [n for n in nodes(component.children[0]) if getattr(n, "className", "") == "rr-chip"]
    assert len(chips) == len(research.CHIPS)


def test_candles_do_not_load_trade_runs_or_higher_series(cache, monkeypatch):  # noqa: F811
    def forbidden(*args, **kwargs):
        pytest.fail("candle delivery waited for strategy/higher-timeframe work")

    monkeypatch.setattr(trades_overlay, "registered_run", forbidden)
    monkeypatch.setattr(trades_overlay, "chart_run", forbidden)
    monkeypatch.setattr(chart, "_higher_series", forbidden)
    monkeypatch.setattr(chart, "_overall_series", forbidden)
    chart._cached_replay.cache_clear()
    payload, _ = chart.base_payload(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02")
    assert len(payload["candles"]["t"]) == 3


def test_chart_outputs_are_separate(cache):  # noqa: F811
    app = Dash(__name__, suppress_callback_exceptions=True)
    chart.register_callbacks(app, cache)
    base = next(v for k, v in app.callback_map.items() if "chart-base.data" in k)
    assert not any(
        i["id"] in {"chart-ovl", "chart-need", "settings-current"} for i in base["inputs"]
    )
    assert any("chart-ovl.data" in k for k in app.callback_map)
    # the strip shows the newest saved run (layout, as before V2.6 step 5); no callback may
    # overwrite it with chart-run numbers (Opus browser check 2026-10-27: it stayed blank)
    assert not any("ch-card-result.children" in k for k in app.callback_map)


def test_last_seen_uses_swiss_date():
    saved = status(heartbeat="2026-07-01T22:30:00Z")
    text = lm.last_seen_text(saved, 600)
    assert "2026-07-02 00:30 CH" in text and "10 min" in text


def test_partial_effective_count_is_visible_and_invalid_tiles_are_folded():
    body = research.card({"href": "/x", "n": 5, "net_r": "bad", "source": "-"}).children[1]
    labels = [n.children[0].children for n in body.children[0].children]
    assert labels == ["N / N_eff"]
    folded = body.children[-1].children[1].children
    assert {n.children[0].children for n in folded} >= {"Net R", "Source"}


def test_live_display_setting_updates_without_changing_control_state(tmp_path):
    from backtester.live.status import write_status

    write_status(tmp_path / "status.json", status(301))
    recent = live.live_view(tmp_path, NOW, stale_minutes=10)
    old = live.live_view(tmp_path, NOW, stale_minutes=5)
    assert recent["state"] == old["state"]
    assert "MT5 connected" in text_of(live.render_cards(recent))
    assert "connected" not in text_of(live.render_cards(old)).lower()
