"""Resolve stylesheet tokens for chart libraries that require literal colours."""

import re
from functools import cache
from pathlib import Path

DEFAULT_MODE = "dark"
LIGHT_BLOCK = 'html[data-theme="light"]'


def toggled(mode: str | None) -> str:
    """The other mode ("dark" / "light"); anything unknown counts as the dark default."""
    return "dark" if mode == "light" else "light"


@cache
def color(name: str, mode: str = DEFAULT_MODE) -> str:
    """Read the same source used by CSS; no duplicate Python palette.

    "light" reads the bright override block of theme.css; the dark tokens are the `:root` ones.
    """
    css = (Path(__file__).parent / "assets/theme.css").read_text(encoding="utf-8")
    if mode == "light":
        start = css.index(LIGHT_BLOCK)
        css = css[start : css.index("}", start)]
    else:
        css = css[: css.index(LIGHT_BLOCK)] if LIGHT_BLOCK in css else css
    match = re.search(r"--" + re.escape(name) + r":\s*([^;]+);", css)
    if match is None:
        raise ValueError(f"Unknown theme token: {name}")
    return match[1].strip()
