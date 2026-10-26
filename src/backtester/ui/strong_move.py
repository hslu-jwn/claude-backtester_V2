"""UI-only mapping; persisted detector settings keep their existing keys."""

MODES = {"off": [], "fvg": ["fvg"], "ob": ["ob"], "both": ["fvg", "ob"]}
OPTIONS = [
    {"label": label, "value": mode}
    for mode, label in [("off", "Off"), ("fvg", "FVG"), ("ob", "OB"), ("both", "Both")]
]


def filter_values(mode):
    # Accept the persisted value of the previous checklist as well.
    return list(mode) if isinstance(mode, (list, tuple)) else list(MODES[mode or "off"])


def filter_mode(values):
    return next(mode for mode, items in MODES.items() if set(items) == set(values or []))
