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

Presets (ROADMAP.md › 4.2, `backtester/presets.py`): the bar at the top of the panel picks
a preset (loads its settings), saves the current settings into it, reverts to it, saves
them as a new one, renames or deletes it; "Default" (the spec defaults) can't be
overwritten. The backtest popover has the same preset dropdown; a run records the
preset's name ("<name> (modified)" when the settings differ from it, `preset_label`).
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.data.resample import supported
from backtester.presets import (
    DEFAULT,
    PRESETS_DIR,
    PresetError,
    delete_preset,
    list_presets,
    load_preset,
    rename_preset,
    save_preset,
)
from backtester.runner import RunSettings
from backtester.settings import (
    Leaf,
    SettingsError,
    form_values,
    leaves,
    settings_from_values,
    to_json,
)
from backtester.strategy.registry import REGISTRY, default_config, strategy_name

GROUPS = (
    "Entry",
    "Windows",
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
DEFAULT_PRESET = DEFAULT

# (path or path prefix ending in ".", group), first match wins
_GROUP_RULES = (
    ("strategy.entry_bos_with_trend", "Entry"),
    ("strategy.max_trades_per_session", "Entry"),
    ("strategy.sweep_lookback", "Entry"),
    ("strategy.stop_atr_mult", "Stop loss"),
    ("strategy.sweep_close_beyond_counts", "Entry"),
    ("strategy.sweep_equal_highs", "Entry"),
    ("strategy.sweep_equal_tolerance_atr", "Entry"),
    ("strategy.sweep_breakout_closes", "Entry"),
    ("strategy.sweep_breakout_wick_first", "Entry"),
    ("strategy.bos_before_top", "Entry"),
    ("strategy.bos_within_am", "Entry"),
    ("strategy.bos_within_pm", "Entry"),
    ("strategy.tap_timeout", "Entry"),
    ("strategy.entry_tf_confluence", "Entry"),
    ("strategy.timeframe", "Entry"),
    ("strategy.trend_source", "Entry"),
    ("strategy.entry_mode", "Entry"),
    ("strategy.max_wick_share", "Entry"),
    ("strategy.order_expiry_candles", "Entry"),
    ("strategy.signal", "Entry"),
    ("strategy.breakout_period", "Entry"),
    ("strategy.sma_period", "Entry"),
    ("strategy.sma_band_atr", "Entry"),
    ("strategy.momentum_period", "Entry"),
    ("strategy.kama_er_period", "Entry"),
    ("strategy.kama_fast", "Entry"),
    ("strategy.kama_slow", "Entry"),
    ("strategy.kama_filter", "Entry"),
    ("strategy.kama_filter_period", "Entry"),
    ("strategy.rr", "Take profit"),
    ("strategy.windows.", "Windows"),
    ("strategy.include_best_time_trades", "Windows"),
    ("strategy.confluence_kinds", "Confluences"),
    ("strategy.use_equilibrium", "Confluences"),
    ("strategy.sl_buffer_atr_mult", "Stop loss"),
    ("strategy.small_confluence_atr_mult", "Stop loss"),
    ("strategy.narrow_confluence_atr_mult", "Stop loss"),
    ("strategy.sl_buffer", "Stop loss"),
    ("strategy.atr_period", "Stop loss"),
    ("strategy.max_sl_atr_mult", "Stop loss"),
    ("strategy.min_sl_atr_mult", "Stop loss"),
    ("detectors.equilibrium.", "Stop loss"),
    ("strategy.strong_move.", "Stop loss"),
    ("engine.break_even_at_next_session", "Stop loss"),
    ("strategy.tp_cap_r", "Take profit"),
    ("strategy.cluster_r", "Take profit"),
    ("strategy.min_tp1_r", "Take profit"),
    ("strategy.ath_mode", "Take profit"),
    ("strategy.fib_levels", "Take profit"),
    ("strategy.fixed_r_levels", "Take profit"),
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
    ("detectors.fvg.", "Detectors"),
    ("detectors.order_block.", "Detectors"),
    ("detectors.swings.", "Detectors"),
    ("engine.costs.", "Costs"),
    ("warmup_days", "Backtest"),
)

LABELS = {
    "detectors.swings.doji_range_share": (
        "Doji: body up to this share of the candle's own range (0 = off: use the price "
        "amounts below)"
    ),
    "strategy.max_trades_per_session": "Max trades per window and index",
    "strategy.sweep_lookback": "Sweep: last N swings",
    "strategy.sweep_close_beyond_counts": "Sweep: a close beyond counts",
    "strategy.sweep_equal_highs": "Sweep: the most extreme of last N must be taken",
    "strategy.sweep_equal_tolerance_atr": "Sweep: same-height tolerance (x ATR, 0 = none)",
    "strategy.sweep_breakout_closes": "Sweep: this many closes beyond = breakout (0 = off)",
    "strategy.sweep_breakout_wick_first": "Sweep: breakout needs only wicks before the last close",
    "strategy.bos_before_top": "BoS must break a swing made before the sweep extreme",
    "strategy.bos_within_am": "BOS within X candles (AM)",
    "strategy.bos_within_pm": "BOS within X candles (PM)",
    "strategy.tap_timeout": "Tap within X candles of the BOS",
    "strategy.entry_tf_confluence": "Entry-TF confluence",
    "strategy.include_best_time_trades": "Take best-time trades",
    "strategy.windows.zone": "Time zone of the windows",
    "strategy.sl_buffer": "SL buffer (share of the 3rd confluence)",
    "strategy.narrow_confluence_atr_mult": "Narrow confluence (× ATR)",
    "strategy.atr_period": "ATR period (narrow confluence)",
    "strategy.cluster_r": "Level cluster (R)",
    "strategy.min_tp1_r": "Minimum R for TP1",
    "strategy.ath_mode": "ATH fallback levels",
    "strategy.fib_levels": "Fib extensions (ATH fallback)",
    "strategy.fixed_r_levels": "Fixed R levels (ATH fallback)",
    "strategy.entry_bos_with_trend": "Step 3 with the 5m trend",
    "strategy.confluence_kinds": "Entry confluence types",
    "strategy.use_equilibrium": "Equilibrium entry",
    "strategy.sl_buffer_atr_mult": "SL buffer (× ATR)",
    "strategy.small_confluence_atr_mult": "Small confluence (× ATR)",
    "strategy.max_sl_atr_mult": "Max SL size (× ATR)",
    "strategy.min_sl_atr_mult": "Min SL size (× ATR)",
    "detectors.equilibrium.sl_buffer": "EQ SL buffer (share of leg low → deepest wick)",
    "detectors.equilibrium.sl_at_deepest_wick": "EQ SL beyond the deepest wick",
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
    "start": "Start",
    "end": "End",
    "open": "Open (first candle)",
    "best_start": "Best time from",
    "best_end": "Best time to",
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
    "strategy.windows.am.": "AM window",
    "strategy.windows.pm.": "PM window",
    "detectors.fvg.": "FVG",
    "detectors.order_block.": "Order block",
    "detectors.swings.doji_max_body.": "Doji threshold (max body, price units)",
    "strategy.sessions.tokyo.": "Tokyo",
    "strategy.sessions.london.": "London",
    "strategy.sessions.new_york.": "New York",
}
# shown first in their group (the doji threshold is used by every detector)
FIRST_IN_GROUP = ("detectors.swings.doji_max_body.",)
# one explanation under the section heading instead of the same help on every row
SECTION_HELP = {
    "detectors.swings.doji_max_body.": (
        "Max |close − open| of a doji / thin candle, per symbol, in price units. Used by "
        "every detector (swings, BOS, sweeps, FVG, OB, BPR, session zones) in backtests "
        "and on the chart. Gold's 0.065 is set by the user; the pairs' defaults are the "
        "same share of their median 5m range."
    ),
}
# choices not offered: strategy 1's equilibrium has its own switch (strategy 2 ranks it)
HIDDEN_OPTIONS = {("session_zone_sweep", "strategy.confluence_kinds"): {"EQUILIBRIUM"}}
DEFAULT_STRATEGY = "session_zone_sweep"
# settings a strategy does not use (shown for no widget): strategy 2 has no break-even at
# the next session start (`Strategy.uses_session_break_even`)
UNUSED = {
    "ny_index_sweep": {"engine.break_even_at_next_session"},
    "no_wick": {"engine.break_even_at_next_session"},
    "trend_following": {"engine.break_even_at_next_session"},
}


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
    if path.startswith("detectors.swings.doji_max_body."):
        return path.rsplit(".", 1)[1]
    last = path.rsplit(".", 1)[1]
    return LEAF_LABELS.get(last, last.replace("_", " ").capitalize())


def options_of(leaf: Leaf, strategy: str = DEFAULT_STRATEGY) -> list[str]:
    hidden = HIDDEN_OPTIONS.get((strategy, leaf.path), set())
    names = [o for o in leaf.options if o not in hidden]
    if leaf.kind == "enum" and set(names) <= set(Timeframe.__members__):
        names = [n for n in names if supported(Timeframe[n])]
    return names


# --- widgets <-> form values -----------------------------------------------------------


def to_widget(kind: str, value: Any) -> Any:
    if kind == "bool":
        return ["on"] if value else []
    if kind == "float_list":
        return ", ".join(f"{v:g}" for v in value)
    return value


def from_widget(kind: str, value: Any) -> Any:
    if kind == "bool":
        return bool(value)
    if kind == "enum_set":
        return list(value or [])
    if kind == "float_list":
        out: list = []
        for token in str(value or "").split(","):
            token = token.strip()
            if token:
                try:
                    out.append(float(token))
                except ValueError:
                    out.append(token)  # reported by the settings: "numbers needed"
        return out
    if kind.startswith("optional_") and value == "":
        return None
    return value


def strategy_leaves(strategy: str = DEFAULT_STRATEGY) -> list[Leaf]:
    """The settings the panel shows for `strategy` (its defaults), in field order."""
    base = RunSettings(strategy=default_config(strategy))
    return [leaf for leaf in leaves(base) if leaf.path not in UNUSED.get(strategy, ())]


def real_path(widget_path: str) -> str:
    """The settings path of a widget id path ("<strategy>:<path>" for a strategy's own
    widget of a path both strategies have with different defaults)."""
    return widget_path.partition(":")[2] or widget_path


def panel_fields() -> list[tuple[str, Leaf, set[str]]]:
    """(widget id path, leaf, the strategies that show it) for every widget of the panel.
    A path two strategies share with the same kind, default and choices is one widget; one
    with different defaults (e.g. `strategy.confluence_kinds`) gets a widget per strategy."""
    found: dict[str, tuple[Leaf, set[str]]] = {}
    for name in REGISTRY:
        for leaf in strategy_leaves(name):
            same = found.get(leaf.path)
            key = leaf.path
            if same is not None:
                first = same[0]
                if (first.kind, first.default, first.options) == (
                    leaf.kind,
                    leaf.default,
                    leaf.options,
                ):
                    same[1].add(name)
                    continue
                key = f"{name}:{leaf.path}"
            found[key] = (leaf, {name})
    return [(key, leaf, owners) for key, (leaf, owners) in found.items()]


def settings_key(settings: RunSettings) -> str:
    return hashlib.sha1(to_json(settings).encode()).hexdigest()[:12]


def store_for(settings: RunSettings, values: Mapping, preset: str = DEFAULT_PRESET) -> dict:
    return {
        "preset": preset,
        "strategy": strategy_name(settings.strategy),
        "values": dict(values),
        "key": settings_key(settings),
    }


def store_strategy(store: Mapping | None) -> str:
    """The strategy the store is for (stores from before strategy 2: strategy 1)."""
    name = (store or {}).get("strategy")
    return name if name in REGISTRY else DEFAULT_STRATEGY


def store_settings(store: Mapping | None) -> RunSettings:
    """The settings in the store (the defaults of its strategy if empty or no longer
    valid)."""
    base = RunSettings(strategy=default_config(store_strategy(store)))
    if not store or not store.get("values"):
        return base
    try:
        return settings_from_values(store["values"], base)
    except SettingsError:
        return base


def store_json(store: Mapping | None) -> str:
    """Canonical JSON of the store's settings ("" = strategy 1's defaults), for caches."""
    settings = store_settings(store)
    return "" if settings == RunSettings() else to_json(settings)


# --- the panel's logic (pure, tested without Dash) -------------------------------------


def _values_of(settings: RunSettings) -> dict[str, Any]:
    """The form values of the settings the panel shows (not the unused ones)."""
    shown = {leaf.path for leaf in strategy_leaves(strategy_name(settings.strategy))}
    return {p: v for p, v in form_values(settings).items() if p in shown}


def preset_values(
    name: str, folder: Path, strategy: str = DEFAULT_STRATEGY
) -> dict[str, Any] | None:
    """The form values saved in preset `name` (None if it can't be read)."""
    try:
        return _values_of(load_preset(name, folder, strategy))
    except PresetError:
        return None


def preset_label(store: Mapping | None, folder: Path = PRESETS_DIR) -> str:
    """The preset name a run records: "<name>", or "<name> (modified)" when the store's
    settings differ from the preset's saved ones."""
    name = (store or {}).get("preset") or DEFAULT_PRESET
    saved = preset_values(name, folder, store_strategy(store))
    if saved is None:
        return f"{name} (missing)"
    current = _values_of(store_settings(store))
    return name if current == saved else f"{name} (modified)"


PRESET_ACTIONS = ("save", "save-as", "rename", "delete", "revert")


def form_update(
    trigger: Any,
    widgets: Mapping[str, Any],
    store: Mapping | None,
    leaf_list: Sequence[Leaf] | None = None,
    name: str | None = None,
    folder: Path = PRESETS_DIR,
    strategy: str = DEFAULT_STRATEGY,
) -> dict:
    """What the panel shows after `trigger` (`strategy`: the strategy the panel is for):
    - {"strategy": name}: another strategy picked: its defaults and the Default preset;
    - None: the panel was built, show the store;
    - "field": a field changed; {"reset": path}: one field back to its default;
      "reset-all": every field back to its default;
    - {"load": preset}: the preset's settings (picked in a preset dropdown);
      "revert": the current preset's saved settings again;
    - "save": the current settings into the current preset ("Default" can't be);
      "save-as" / "rename": into / the current preset to `name`; "delete": the current
      preset (then "Default" is loaded).
    Returns {"widgets": {path: widget value} or None (unchanged), "store": new store or
    None (unchanged), "changed": paths differing from the default, "error": (path,
    message) of an invalid field or None, "preset": the current preset, "modified": the
    settings differ from it, "presets": the preset names, "message": the preset action's
    result or None}."""
    switched = isinstance(trigger, Mapping) and "strategy" in trigger
    if switched and trigger["strategy"] == strategy:  # the dropdown just followed the store
        preset = (store or {}).get("preset") or DEFAULT_PRESET
        return {
            "widgets": None,
            "store": None,
            "changed": [],
            "error": None,
            "preset": preset,
            "modified": False,
            "presets": list_presets(folder, strategy),
            "message": None,
        }
    if switched:
        strategy = trigger["strategy"]
    base = RunSettings(strategy=default_config(strategy))
    by_path = {leaf.path: leaf for leaf in (leaf_list or strategy_leaves(strategy))}
    preset = (store or {}).get("preset") or DEFAULT_PRESET
    message = None

    def widgets_for(vals):
        return {p: to_widget(by_path[p].kind, v) for p, v in vals.items()}

    if trigger is None:
        saved = dict((store or {}).get("values") or {})
        values = {p: saved.get(p, leaf.default) for p, leaf in by_path.items()}
        new_widgets = widgets_for(values)
    else:
        values = {p: from_widget(by_path[p].kind, w) for p, w in widgets.items() if p in by_path}
        new_widgets = None
        if switched:
            preset, values = DEFAULT_PRESET, {p: leaf.default for p, leaf in by_path.items()}
            new_widgets = widgets_for(values)
        elif trigger == "reset-all":
            values = {p: leaf.default for p, leaf in by_path.items()}
            new_widgets = widgets_for(values)
        elif isinstance(trigger, Mapping) and trigger.get("reset") in by_path:
            values[trigger["reset"]] = by_path[trigger["reset"]].default
            new_widgets = widgets_for(values)
        elif (isinstance(trigger, Mapping) and "load" in trigger) or trigger == "revert":
            wanted = trigger["load"] if trigger != "revert" else preset
            loaded = preset_values(wanted or DEFAULT_PRESET, folder, strategy)
            if loaded is None:
                message = f"Preset {wanted!r} can't be read."
            else:
                preset, values = wanted or DEFAULT_PRESET, {**values, **loaded}
                new_widgets = widgets_for(values)
    changed = [p for p, v in values.items() if v != by_path[p].default]
    try:
        settings = settings_from_values(values, base)
    except SettingsError as e:
        error = _error(e)
        if trigger in PRESET_ACTIONS:
            message = "Fix the invalid setting first."
        return {
            "widgets": new_widgets,
            "store": None,
            "changed": changed,
            "error": error,
            "preset": preset,
            "modified": True,
            "presets": list_presets(folder, strategy),
            "message": message,
        }
    try:
        if trigger == "save":
            save_preset(preset, settings, folder)
            message = f"Saved preset {preset!r}."
        elif trigger == "save-as":
            preset = save_preset(name, settings, folder)
            message = f"Saved as preset {preset!r}."
        elif trigger == "rename":
            old, preset = preset, rename_preset(preset, name, folder)
            message = f"Renamed {old!r} to {preset!r}."
        elif trigger == "delete":
            delete_preset(preset, folder)
            message = f"Deleted preset {preset!r}; the defaults are loaded."
            preset, values = DEFAULT_PRESET, _values_of(base)
            settings, changed, new_widgets = base, [], widgets_for(values)
    except PresetError as e:
        message = str(e)[:1].upper() + str(e)[1:] + "."
    new_store = store_for(settings, values, preset)
    same = store and all(store.get(k) == new_store[k] for k in ("values", "preset", "strategy"))
    saved = preset_values(preset, folder, strategy)
    return {
        "widgets": new_widgets,
        "store": None if same else new_store,
        "changed": changed,
        "error": None,
        "preset": preset,
        "modified": saved is not None and saved != values,
        "presets": list_presets(folder, strategy),
        "message": message,
    }


def _error(e: SettingsError) -> tuple[str | None, str]:
    where = label_of(e.path) if e.path and "." in e.path else (e.path or "settings")
    return e.path, f"{where}: {e}"


def status_text(result: Mapping) -> str:
    if result["error"]:
        text = f"Not applied, {result['error'][1]}"
    else:
        n = len(result["changed"])
        preset = result["preset"] + (" (modified)" if result["modified"] else "")
        differ = "all at the spec defaults" if not n else f"{n} differ from the spec defaults"
        text = f"Preset {preset} · {differ}"
    return f"{result['message']} {text}" if result["message"] else text


def preset_options(names: Sequence[str]) -> list[dict]:
    return [{"label": n, "value": n} for n in names]


def preset_controls() -> list:
    """Preset bar of the panel: dropdown, name field and the actions."""

    def button(id_, text, title):
        return html.Button(text, id=id_, title=title, className="st-btn", n_clicks=0)

    return [
        html.Span("Preset", className="st-preset-label"),
        dcc.Dropdown(
            id="st-preset",
            options=preset_options([DEFAULT_PRESET]),
            value=DEFAULT_PRESET,
            clearable=False,
            searchable=False,
            className="st-preset",
        ),
        button("st-save", "Save", "Save the settings into this preset"),
        button("st-revert", "Revert", "Load this preset's saved settings again"),
        html.Div(className="tb-sep"),
        dcc.Input(id="st-name", type="text", placeholder="New name", className="st-input st-name"),
        button("st-save-as", "Save as", "Save the settings as a new preset with this name"),
        button("st-rename", "Rename", "Rename this preset"),
        button("st-delete", "Delete", "Delete this preset"),
    ]


# --- layout ----------------------------------------------------------------------------


def _widget(leaf: Leaf, widget_path: str):
    id_ = {"type": "st-field", "path": widget_path}
    owner = widget_path.partition(":")[0] if ":" in widget_path else DEFAULT_STRATEGY
    if leaf.kind == "bool":
        return dcc.Checklist(
            id=id_, options=[{"label": "", "value": "on"}], value=[], className="st-switch"
        )
    if leaf.kind == "enum":
        return dcc.Dropdown(
            id=id_,
            options=options_of(leaf, owner),
            clearable=False,
            searchable=False,
            className="st-dd",
        )
    if leaf.kind == "enum_set":
        return dcc.Checklist(id=id_, options=options_of(leaf, owner), value=[], className="st-set")
    if leaf.kind in ("time", "text", "float_list"):
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
        return ", ".join(f"{v:g}" if isinstance(v, float) else str(v) for v in value)
    return f"{value:g}" if isinstance(value, float) else str(value)


def _row(leaf: Leaf, widget_path: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(label_of(leaf.path), className="st-label"),
                    html.Div(leaf.help, className="st-help")
                    if leaf.help and not _section_help_of(leaf.path)
                    else None,
                ],
                className="st-text",
            ),
            html.Div(_widget(leaf, widget_path), className="st-control"),
            html.Button(
                "↺",
                id={"type": "st-reset", "path": widget_path},
                title=f"Reset to default ({_default_text(leaf)})",
                className="st-reset",
                n_clicks=0,
            ),
        ],
        id={"type": "st-row", "path": widget_path},
        className="st-row",
    )


def _section_help_of(path: str) -> str:
    return next((h for prefix, h in SECTION_HELP.items() if path.startswith(prefix)), "")


def grouped(leaf_list: Sequence[Leaf]) -> dict[str, list[Leaf]]:
    """The leaves by group, in `GROUPS` order, empty groups left out."""
    out: dict[str, list[Leaf]] = {g: [] for g in (*GROUPS, OTHER)}
    for leaf in leaf_list:
        out[group_of(leaf.path)].append(leaf)
    for leaves_ in out.values():
        leaves_.sort(key=lambda leaf: not leaf.path.startswith(FIRST_IN_GROUP))  # stable
    return {g: ls for g, ls in out.items() if ls}


def _group_body(group: str, fields: list[tuple[str, Leaf]], shown: bool) -> html.Div:
    children, section = [], ""
    for widget_path, leaf in fields:
        s = section_of(leaf.path)
        if s and s != section:
            children.append(html.Div(s, className="st-section"))
            if help_ := _section_help_of(leaf.path):
                children.append(html.Div(help_, className="st-help st-section-help"))
        section = s
        children.append(_row(leaf, widget_path))
    return html.Div(
        children,
        id={"type": "st-group-body", "group": group},
        style={"display": "block" if shown else "none"},
    )


def _fields_by_group() -> dict[str, list[tuple[str, Leaf]]]:
    """Every widget of the panel (all strategies) by group, in each strategy's field
    order; rows a strategy does not use are hidden by class (`row_classes`)."""
    out: dict[str, list[tuple[str, Leaf]]] = {}
    for widget_path, leaf, _ in panel_fields():
        out.setdefault(group_of(leaf.path), []).append((widget_path, leaf))
    for group_fields in out.values():  # stable: the doji thresholds first
        group_fields.sort(key=lambda f: not f[1].path.startswith(FIRST_IN_GROUP))
    return {g: out[g] for g in (*GROUPS, OTHER) if g in out}


def title_of(strategy: str) -> str:
    return f"{REGISTRY[strategy].label} · Settings"


def layout() -> html.Div:
    """The modal (hidden until a button with data-modal="st-modal" opens it)."""
    groups = _fields_by_group()
    first = next(iter(grouped(strategy_leaves(DEFAULT_STRATEGY))))
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.Div(title_of(DEFAULT_STRATEGY), id="st-title", className="st-title"),
                        html.Button("✕", className="st-close", **{"data-modal-close": "st-modal"}),
                    ],
                    className="st-head",
                ),
                html.Div(preset_controls(), className="st-presets"),
                html.Div(
                    [
                        dcc.RadioItems(
                            id="st-group",
                            options=list(grouped(strategy_leaves(DEFAULT_STRATEGY))),
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


def _picked(args) -> str | None:
    """The strategy the strategy popover was just changed to, if that was the trigger."""
    return args[4] if ctx.triggered_id == "chart-strategy" else None


def panel_widgets(
    widget_paths: Sequence[str], values: Sequence[Any], strategy: str, picked: str | None = None
) -> dict[str, Any]:
    """{settings path: widget value} of the widgets that belong to the strategy now shown
    (`picked`, else `strategy`)."""
    owners = {wp: o for wp, _, o in panel_fields()}
    active = picked or strategy
    return {
        real_path(wp): v
        for wp, v in zip(widget_paths, values, strict=True)
        if active in owners.get(wp, ())
    }


def row_classes(
    widget_paths: Sequence[str], mine: Sequence[bool], changed: Sequence[str], error: str | None
) -> list[str]:
    return [
        "st-row"
        + ("" if own else " st-hidden")
        + (" st-changed" if real_path(wp) in changed and own else "")
        + (" st-error" if real_path(wp) == error and own else "")
        for wp, own in zip(widget_paths, mine, strict=True)
    ]


def register_callbacks(app: Dash, presets_dir: Path = PRESETS_DIR) -> None:
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
        Output("st-preset", "options"),
        Output("st-preset", "value"),
        Output("bt-preset", "options"),
        Output("bt-preset", "value"),
        Output("bt-preset-note", "children"),
        Output("st-group", "options"),
        Output("st-group", "value"),
        Output("st-title", "children"),
        Input({"type": "st-field", "path": ALL}, "value"),
        Input({"type": "st-reset", "path": ALL}, "n_clicks"),
        Input("st-reset-all", "n_clicks"),
        Input("st-preset", "value"),
        Input("bt-preset", "value"),
        Input("chart-strategy", "value"),
        *[Input(f"st-{action}", "n_clicks") for action in PRESET_ACTIONS],
        State("st-name", "value"),
        State("settings-current", "data"),
        State("st-group", "value"),
    )
    def _settings(values, *args):
        name, store, group = args[-3:]
        widget_paths = [item["id"]["path"] for item in ctx.inputs_list[0]]
        strategy = store_strategy(store)
        result = form_update(
            _trigger(), panel_widgets(widget_paths, values, strategy, _picked(args)), store,
            name=name, folder=presets_dir, strategy=strategy,
        )  # fmt: skip
        now = result["store"]["strategy"] if result["store"] is not None else strategy
        if _picked(args) and result["store"] is None and not result["error"]:
            now = _picked(args)  # picked and unchanged: the same as the store's
        owners = {wp: o for wp, _, o in panel_fields()}
        mine = [now in owners.get(wp, ()) for wp in widget_paths]
        error_path = result["error"][0] if result["error"] else None
        classes = row_classes(widget_paths, mine, result["changed"], error_path)
        new = result["widgets"]
        options = preset_options(result["presets"])
        note = "Modified, not saved (see Settings…)." if result["modified"] else ""
        groups = list(grouped(strategy_leaves(now)))
        shown = [
            no_update if new is None or not own else new.get(real_path(wp), no_update)
            for wp, own in zip(widget_paths, mine, strict=True)
        ]
        return (
            shown,
            classes,
            result["store"] if result["store"] is not None else no_update,
            status_text(result),
            options,
            result["preset"],
            options,
            result["preset"],
            note,
            groups,
            group if group in groups else groups[0],
            title_of(now),
        )

    @app.callback(
        Output("chart-strategy", "value"),
        Input("settings-current", "data"),
        State("chart-strategy", "value"),
    )
    def _strategy_of_store(store, shown):
        """The strategy popover follows the store (a page load, a strategy 2 preset)."""
        name = store_strategy(store)
        return no_update if name == shown else name


def _trigger():
    """The panel trigger (see `form_update`) from Dash's callback context."""
    tid = ctx.triggered_id
    if tid is None:
        return None
    if tid == "st-reset-all":
        return "reset-all"
    if tid in ("st-preset", "bt-preset"):
        return {"load": ctx.triggered[0]["value"]}
    if tid == "chart-strategy":
        return {"strategy": ctx.triggered[0]["value"]}
    if isinstance(tid, str) and tid.removeprefix("st-") in PRESET_ACTIONS:
        return tid.removeprefix("st-")
    if isinstance(tid, Mapping) and tid.get("type") == "st-reset":
        return {"reset": tid["path"]}
    return "field"
