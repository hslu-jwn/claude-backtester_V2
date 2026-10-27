"""V2.7 dark / bright switch: colours only (briefs/v27-theme-switch.md)."""

import re
from pathlib import Path

from dash import dcc, html

from backtester.ui import nav, theme
from backtester.ui.chart_config import ChartConfig
from backtester.ui.pages.chart import chart_settings

UI = Path(__file__).resolve().parents[2] / "src/backtester/ui"


def walk(node):
    if isinstance(node, (list, tuple)):
        for child in node:
            yield from walk(child)
    elif hasattr(node, "to_plotly_json"):
        yield node
        yield from walk(getattr(node, "children", None))


def test_switch_sits_right_after_update_data_in_the_top_bar():
    actions = next(n for n in walk(nav.layout()) if getattr(n, "className", "") == "nav-actions")
    ids = [getattr(c, "id", None) for c in actions.children]
    assert ids.index("update-tick") < ids.index("theme-btn") < ids.index("nav-settings")
    assert ids.count("theme-btn") == 1
    button = next(n for n in walk(nav.layout()) if getattr(n, "id", None) == "theme-btn")
    assert isinstance(button, html.Button) and "tb-btn" in button.className
    assert "bright" in button.title.lower() and "dark" in button.title.lower()


def test_theme_store_defaults_to_dark_and_is_remembered_per_browser():
    store = next(n for n in walk(nav.layout()) if getattr(n, "id", None) == "theme-mode")
    assert isinstance(store, dcc.Store)
    assert store.data == "dark" and store.storage_type == "local"


def test_toggle():
    assert theme.toggled("dark") == "light"
    assert theme.toggled("light") == "dark"
    assert theme.toggled(None) == "light"  # unknown counts as the dark default


def test_bright_tokens_define_a_white_background_and_dark_text():
    assert theme.color("bg") == "#101113"  # dark stays the default
    assert theme.color("bg", "light").lower() == "#ffffff"
    for name in ("panel", "raised", "line", "text", "muted", "green", "red", "accent"):
        assert theme.color(name, "light")
    css = (UI / "assets/theme.css").read_text(encoding="utf-8")
    assert 'html[data-theme="light"]' in css
    assert re.search(r"color-scheme:\s*light", css)
    text = theme.color("text", "light").lstrip("#")
    assert sum(int(text[i : i + 2], 16) for i in (0, 2, 4)) < 3 * 128  # dark text


def test_candle_palettes():
    themes = chart_settings()["themes"]
    assert set(themes) == {"dark", "light"}
    for key in ("up_body", "down_body", "edge_color", "wick_color"):
        assert key in themes["dark"] and key in themes["light"]
    dark = themes["dark"]
    assert dark["up_body"] == "#22c55e"
    assert (dark["down_body"], dark["edge_color"], dark["wick_color"]) == ("#ef4444",) * 3
    # edge and wick of up candles: same green (body, border and wick alike)
    light = themes["light"]
    assert light["up_body"] == "#6f9ceb"
    assert (light["down_body"], light["edge_color"], light["wick_color"]) == ("#000000",) * 3
    assert dark["background"] == theme.color("bg")
    assert light["background"].lower() == "#ffffff"
    assert light["text_color"] == theme.color("text", "light")


def test_chart_config_defaults_unchanged_and_flat_keys_kept():
    config = ChartConfig()
    assert config.up_body == "#6f9ceb" and config.down_body == "#000000"
    flat = chart_settings()
    assert flat["background"] == theme.color("bg")  # existing readers keep working


def test_javascript_follows_the_switch():
    js = (UI / "assets/chart.js").read_text(encoding="utf-8")
    assert "applyTheme" in js and "cfg.themes" in js
    switch = (UI / "assets/theme.js").read_text(encoding="utf-8")
    assert "data-theme" in switch or "dataset.theme" in switch


def test_app_registers_the_switch():
    from backtester.data.sources import SymbolSources
    from backtester.ui import app as app_module

    app = app_module.create_app(SymbolSources({}))
    keys = " ".join(app.callback_map)
    assert "theme-mode.data" in keys


def test_theme_js_recolours_plotly_figures_from_css_tokens():
    js = (UI / "assets/theme.js").read_text(encoding="utf-8")
    assert "Plotly.relayout" in js and ".js-plotly-plot" in js
    assert "plotly_afterplot" in js and "MutationObserver" in js
    for name in ("panel", "text", "line"):
        assert f'token("{name}")' in js
    for key in ("paper_bgcolor", "plot_bgcolor", "font.color", "hoverlabel.bgcolor"):
        assert key in js
    assert "gridcolor" in js and "zerolinecolor" in js
    # the dark figure is restored exactly from what was saved before the first recolour
    assert "_themeOrig" in js
