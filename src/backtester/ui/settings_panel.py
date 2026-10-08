"""Strategy settings panel (a modal opened from the strategy popover). Spec: ROADMAP.md › 4.1.

The fields are generated from the config dataclasses (`backtester/settings.py` `leaves`):
every value with its spec default and the help text from its source comment. This module
only adds presentation: the group each value is shown in (`group_of`), a readable label
(`label_of`, falling back to the field name) and the sub-heading inside a group
(`section_of`, e.g. the symbol of a cost). A new config field appears by itself (under
"Other" until it gets a group here; a test keeps "Other" empty).

Each field: label, help, input, "↺" (reset to default) and a dot when it differs from the
default. Changes apply at once when valid: the store `settings-current` (browser local
storage) keeps {"preset", "values" (path -> value), "key" (hash of the settings)}; the
Trades overlay and the backtest popover read it. An invalid value is named in the
panel's status line and the store keeps the last valid settings.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.data.resample import supported
from backtester.runner import RunSettings
from backtester.settings import (
    Leaf,
    SettingsError,
    leaves,
    settings_from_values,
    to_json,
)

GROUPS = (
    "Entry",
    "Confluences",
    "Stop loss",
    "Take profit",
    "Session zones",
    "Sessions & filters",
    "Detectors",
    "Costs",
    "Backtest",
)
OTHER = "Other"
DEFAULT_PRESET = "Default"

# (path or path prefix ending in ".", group), first match wins
_GROUP_RULES = (
    ("strategy.entry_bos_with_trend", "Entry"),
    ("strategy.confluence_kinds", "Confluences"),
    ("strategy.use_equilibrium", "Confluences"),
    ("strategy.sl_buffer_atr_mult", "Stop loss"),
    ("strategy.small_confluence_atr_mult", "Stop loss"),
    ("strategy.max_sl_atr_mult", "Stop loss"),
    ("strategy.min_sl_atr_mult", "Stop loss"),
    ("strategy.strong_move.", "Stop loss"),
    ("engine.break_even_at_next_session", "Stop loss"),
    ("strategy.tp_cap_r", "Take profit"),
    ("strategy.min_rr", "Take profit"),
    ("strategy.obstacles_passable", "Take profit"),
    ("strategy.obstacle_cluster_r", "Take profit"),
    ("strategy.obstacle_timeframe", "Take profit"),
    ("strategy.limit_timeframe", "Take profit"),
    ("strategy.tp_buffer_atr_mult", "Take profit"),
    ("strategy.tp1_share", "Take profit"),
    ("strategy.break_even_after_tp1", "Take profit"),
    ("strategy.zone_timeframe", "Session zones"),
    ("strategy.zone_kill", "Session zones"),
    ("strategy.zone_kill_breaks", "Session zones"),
    ("strategy.sessions.", "Sessions & filters"),
    ("strategy.tag_last_minutes_before_next_session", "Sessions & filters"),
    ("strategy.include_last_minutes_trades", "Sessions & filters"),
    ("strategy.skip_tokyo", "Sessions & filters"),
    ("strategy.friday_ny_carries_to_monday_tokyo", "Sessions & filters"),
    ("strategy.fvg.", "Detectors"),
    ("strategy.order_block.", "Detectors"),
    ("strategy.swings.", "Detectors"),
    ("engine.costs.", "Costs"),
    ("warmup_days", "Backtest"),
)

LABELS = {
    "strategy.entry_bos_with_trend": "Step 3 with the 5m trend",
    "strategy.confluence_kinds": "Entry confluence types",
    "strategy.use_equilibrium": "Equilibrium entry",
    "strategy.sl_buffer_atr_mult": "SL buffer (× ATR)",
    "strategy.small_confluence_atr_mult": "Small confluence (× ATR)",
    "strategy.max_sl_atr_mult": "Max SL size (× ATR)",
    "strategy.min_sl_atr_mult": "Min SL size (× ATR)",
    "strategy.strong_move.atr_period": "ATR period (5m)",
    "engine.break_even_at_next_session": "Break-even at the next session",
    "strategy.tp_cap_r": "TP cap (R)",
    "strategy.min_rr": "Minimum R:R (TP1)",
    "strategy.obstacles_passable": "Levels TP2 may pass",
    "strategy.obstacle_cluster_r": "Level cluster (R)",
    "strategy.obstacle_timeframe": "Level timeframe",
    "strategy.limit_timeframe": "Hard limit timeframe (OBs)",
    "strategy.tp_buffer_atr_mult": "TP buffer (× ATR)",
    "strategy.tp1_share": "TP1 share",
    "strategy.break_even_after_tp1": "Break-even after TP1",
    "strategy.zone_timeframe": "Zone timeframe",
    "strategy.zone_kill": "Kill zones after breaks",
    "strategy.zone_kill_breaks": "Breaks that kill a zone",
    "strategy.sessions.weekend_zone": "Weekend in time zone",
    "strategy.tag_last_minutes_before_next_session": "Tag minutes before next session",
    "strategy.include_last_minutes_trades": "Take tagged trades",
    "strategy.skip_tokyo": "Skip Tokyo",
    "strategy.friday_ny_carries_to_monday_tokyo": "Friday NY → Monday Tokyo",
    "engine.costs.spread_enabled": "Spread",
    "engine.costs.commission_enabled": "Commission",
    "warmup_days": "Warm-up days",
}
LEAF_LABELS = {  # by the last part of the path
    "local_time": "Start (local time)",
    "zone": "Time zone",
    "strong_move_filter": "Strong-move filter",
    "atr_period": "ATR period",
    "atr_mult": "ATR multiplier (k)",
    "spread": "Spread (price)",
    "commission_per_lot": "Commission per lot (USD)",
    "contract_size": "Contract size",
    "quote_to_usd": "Quote currency → USD",
}
SECTIONS = {
    "strategy.fvg.": "FVG",
    "strategy.order_block.": "Order block",
    "strategy.swings.doji_max_body.": "Doji threshold (max body, price units)",
    "strategy.sessions.tokyo.": "Tokyo",
    "strategy.sessions.london.": "London",
    "strategy.sessions.new_york.": "New York",
}
# choices not offered: breakers aren't built (ROADMAP 2.7), the equilibrium has its switch
HIDDEN_OPTIONS = {"strategy.confluence_kinds": {"BREAKER", "EQUILIBRIUM"}}


def group_of(path: str) -> str:
    for rule, group in _GROUP_RULES:
        if path == rule or (rule.endswith(".") and path.startswith(rule)):
            return group
    return OTHER


def section_of(path: str) -> str:
    """Sub-heading inside the group ("" = none)."""
    if path.startswith("engine.costs.symbols."):
        return path.split(".")[3]
    for prefix, title in SECTIONS.items():
        if path.startswith(prefix):
            return title
    return ""


def label_of(path: str) -> str:
    if path in LABELS:
        return LABELS[path]
    if path.startswith("strategy.swings.doji_max_body."):
        return path.rsplit(".", 1)[1]
    last = path.rsplit(".", 1)[1]
    return LEAF_LABELS.get(last, last.replace("_", " ").capitalize())


def options_of(leaf: Leaf) -> list[str]:
    hidden = HIDDEN_OPTIONS.get(leaf.path, set())
    names = [o for o in leaf.options if o not in hidden]
    if leaf.kind == "enum" and set(names) <= set(Timeframe.__members__):
        names = [n for n in names if supported(Timeframe[n])]
    return names


# --- widgets <-> form values -----------------------------------------------------------


def to_widget(kind: str, value: Any) -> Any:
    if kind == "bool":
        return ["on"] if value else []
    return value


def from_widget(kind: str, value: Any) -> Any:
    if kind == "bool":
        return bool(value)
    if kind == "enum_set":
        return list(value or [])
    if kind.startswith("optional_") and value == "":
        return None
    return value


def settings_key(settings: RunSettings) -> str:
    return hashlib.sha1(to_json(settings).encode()).hexdigest()[:12]


def store_for(settings: RunSettings, values: Mapping, preset: str = DEFAULT_PRESET) -> dict:
    return {"preset": preset, "values": dict(values), "key": settings_key(settings)}


def store_settings(store: Mapping | None) -> RunSettings:
    """The settings in the store (the spec defaults if empty or no longer valid)."""
    if not store or not store.get("values"):
        return RunSettings()
    try:
        return settings_from_values(store["values"])
    except SettingsError:
        return RunSettings()


def store_json(store: Mapping | None) -> str:
    """Canonical JSON of the store's settings ("" = the defaults), for caches."""
    settings = store_settings(store)
    return "" if settings == RunSettings() else to_json(settings)


# --- the panel's logic (pure, tested without Dash) -------------------------------------


def form_update(
    trigger: Any,
    widgets: Mapping[str, Any],
    store: Mapping | None,
    leaf_list: Sequence[Leaf] | None = None,
) -> dict:
    """What the panel shows after `trigger`: None (panel built: show the store),
    {"reset": path}, "reset-all", or a field change. Returns {"widgets": {path: widget
    value} or None (unchanged), "store": new store or None (unchanged), "changed": paths
    differing from the default, "error": (path, message) or None}."""
    leaf_list = list(leaf_list or leaves())
    by_path = {leaf.path: leaf for leaf in leaf_list}
    preset = (store or {}).get("preset", DEFAULT_PRESET)
    if trigger is None:
        saved = dict((store or {}).get("values") or {})
        values = {p: saved.get(p, leaf.default) for p, leaf in by_path.items()}
        new_widgets = {p: to_widget(by_path[p].kind, v) for p, v in values.items()}
    else:
        values = {p: from_widget(by_path[p].kind, w) for p, w in widgets.items() if p in by_path}
        new_widgets = None
        if trigger == "reset-all":
            values = {p: leaf.default for p, leaf in by_path.items()}
        elif isinstance(trigger, Mapping) and trigger.get("reset") in by_path:
            values[trigger["reset"]] = by_path[trigger["reset"]].default
        if new_widgets is None and trigger != "field":
            new_widgets = {p: to_widget(by_path[p].kind, v) for p, v in values.items()}
    changed = [p for p, v in values.items() if v != by_path[p].default]
    try:
        settings = settings_from_values(values)
    except SettingsError as e:
        return {"widgets": new_widgets, "store": None, "changed": changed, "error": _error(e)}
    new_store = store_for(settings, values, preset)
    same = store and store.get("values") == new_store["values"]
    return {
        "widgets": new_widgets,
        "store": None if same else new_store,
        "changed": changed,
        "error": None,
    }


def _error(e: SettingsError) -> tuple[str | None, str]:
    where = label_of(e.path) if e.path and "." in e.path else (e.path or "settings")
    return e.path, f"{where}: {e}"


def status_text(store: Mapping | None, changed: Sequence[str], error) -> str:
    if error:
        return f"Not applied, {error[1]}"
    n = len(changed)
    return (
        "All settings at the spec defaults."
        if not n
        else f"{n} setting(s) differ from the defaults."
    )


# --- layout ----------------------------------------------------------------------------


def _widget(leaf: Leaf):
    id_ = {"type": "st-field", "path": leaf.path}
    if leaf.kind == "bool":
        return dcc.Checklist(
            id=id_, options=[{"label": "", "value": "on"}], value=[], className="st-switch"
        )
    if leaf.kind == "enum":
        return dcc.Dropdown(
            id=id_, options=options_of(leaf), clearable=False, searchable=False, className="st-dd"
        )
    if leaf.kind == "enum_set":
        return dcc.Checklist(id=id_, options=options_of(leaf), value=[], className="st-set")
    if leaf.kind in ("time", "text"):
        return dcc.Input(id=id_, type="text", debounce=True, className="st-input")
    optional = leaf.kind.startswith("optional_")
    return dcc.Input(
        id=id_,
        type="number",
        step="any",
        debounce=True,
        placeholder="off" if optional else "",
        className="st-input",
    )


def _default_text(leaf: Leaf) -> str:
    value = leaf.default
    if leaf.kind == "bool":
        return "on" if value else "off"
    if value is None:
        return "off"
    if isinstance(value, list):
        return ", ".join(value)
    return f"{value:g}" if isinstance(value, float) else str(value)


def _row(leaf: Leaf) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(label_of(leaf.path), className="st-label"),
                    html.Div(leaf.help, className="st-help") if leaf.help else None,
                ],
                className="st-text",
            ),
            html.Div(_widget(leaf), className="st-control"),
            html.Button(
                "↺",
                id={"type": "st-reset", "path": leaf.path},
                title=f"Reset to default ({_default_text(leaf)})",
                className="st-reset",
                n_clicks=0,
            ),
        ],
        id={"type": "st-row", "path": leaf.path},
        className="st-row",
    )


def grouped(leaf_list: Sequence[Leaf]) -> dict[str, list[Leaf]]:
    out: dict[str, list[Leaf]] = {g: [] for g in (*GROUPS, OTHER)}
    for leaf in leaf_list:
        out[group_of(leaf.path)].append(leaf)
    return {g: ls for g, ls in out.items() if ls}


def _group_body(group: str, leaf_list: list[Leaf], shown: bool) -> html.Div:
    children, section = [], ""
    for leaf in leaf_list:
        s = section_of(leaf.path)
        if s and s != section:
            children.append(html.Div(s, className="st-section"))
        section = s
        children.append(_row(leaf))
    return html.Div(
        children,
        id={"type": "st-group-body", "group": group},
        style={"display": "block" if shown else "none"},
    )


def layout(preset_controls: list | None = None) -> html.Div:
    """The modal (hidden until a button with data-modal="st-modal" opens it)."""
    groups = grouped(leaves())
    first = next(iter(groups))
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            "Strategy 1 · Session zone sweep · Settings", className="st-title"
                        ),
                        html.Button("✕", className="st-close", **{"data-modal-close": "st-modal"}),
                    ],
                    className="st-head",
                ),
                html.Div(preset_controls or [], className="st-presets"),
                html.Div(
                    [
                        dcc.RadioItems(
                            id="st-group",
                            options=list(groups),
                            value=first,
                            className="st-nav",
                        ),
                        html.Div(
                            [_group_body(g, ls, g == first) for g, ls in groups.items()],
                            className="st-fields",
                        ),
                    ],
                    className="st-main",
                ),
                html.Div(
                    [
                        html.Div(id="st-status", className="st-status"),
                        html.Button(
                            "Reset all to defaults",
                            id="st-reset-all",
                            className="st-btn",
                            n_clicks=0,
                        ),
                        html.Button(
                            "Close",
                            className="st-btn st-primary",
                            **{"data-modal-close": "st-modal"},
                        ),
                    ],
                    className="st-foot",
                ),
            ],
            className="st-dialog",
        ),
        id="st-modal",
        className="st-backdrop",
    )


def register_callbacks(app: Dash) -> None:
    app.clientside_callback(
        """function (group, ids) {
            return ids.map((id) => ({display: id.group === group ? "block" : "none"}));
        }""",
        Output({"type": "st-group-body", "group": ALL}, "style"),
        Input("st-group", "value"),
        State({"type": "st-group-body", "group": ALL}, "id"),
    )

    @app.callback(
        Output({"type": "st-field", "path": ALL}, "value"),
        Output({"type": "st-row", "path": ALL}, "className"),
        Output("settings-current", "data"),
        Output("st-status", "children"),
        Input({"type": "st-field", "path": ALL}, "value"),
        Input({"type": "st-reset", "path": ALL}, "n_clicks"),
        Input("st-reset-all", "n_clicks"),
        State("settings-current", "data"),
    )
    def _settings(values, _resets, _reset_all, store):
        paths = [item["id"]["path"] for item in ctx.inputs_list[0]]
        widgets = dict(zip(paths, values, strict=True))
        trigger = _trigger()
        result = form_update(trigger, widgets, store)
        error_path = result["error"][0] if result["error"] else None
        classes = [
            "st-row"
            + (" st-changed" if p in result["changed"] else "")
            + (" st-error" if p == error_path else "")
            for p in paths
        ]
        new = result["widgets"]
        return (
            [new[p] for p in paths] if new is not None else [no_update] * len(paths),
            classes,
            result["store"] if result["store"] is not None else no_update,
            status_text(store, result["changed"], result["error"]),
        )


def _trigger():
    """The panel trigger (see `form_update`) from Dash's callback context."""
    tid = ctx.triggered_id
    if tid is None:
        return None
    if tid == "st-reset-all":
        return "reset-all"
    if isinstance(tid, Mapping) and tid.get("type") == "st-reset":
        return {"reset": tid["path"]}
    return "field"
