from backtester.ui import nav
from backtester.ui.pages import portfolio


def test_navigation_and_empty_layout(tmp_path):
    assert nav.section_of("/portfolio") == "portfolio"
    assert "active" in nav.link_classes("/portfolio", False)["portfolio"]
    text = str(portfolio.layout(tmp_path).to_plotly_json())
    assert "Find combinations" in text
    assert "Monte Carlo top 10" in text
    assert "--test" not in text and "--retest" not in text


def test_callbacks_register_without_app_start(tmp_path):
    from dash import Dash

    app = Dash(__name__, suppress_callback_exceptions=True)
    portfolio.register_callbacks(app, tmp_path)
    assert app.callback_map


def test_holdout_summary_never_shown(tmp_path):
    import json

    folder = tmp_path / "portfolio" / "abc"
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(
        json.dumps({"meta": {"source": "mt5", "end": "2026-01-01"}})
    )
    assert portfolio.monte_carlo_rows({"id": "abc"}, tmp_path) == []
