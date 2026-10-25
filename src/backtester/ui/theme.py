"""Resolve stylesheet tokens for chart libraries that require literal colours."""

import re
from functools import cache
from pathlib import Path


@cache
def color(name: str) -> str:
    """Read the same source used by CSS; no duplicate Python palette."""
    css = (Path(__file__).parent / "assets/theme.css").read_text(encoding="utf-8")
    match = re.search(r"--" + re.escape(name) + r":\s*([^;]+);", css)
    if match is None:
        raise ValueError(f"Unknown theme token: {name}")
    return match[1].strip()
