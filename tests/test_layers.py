"""Layer rules (docs/ARCHITECTURE.md › Layers, CLAUDE.md › Layout), checked on the imports.

A layered package may import only itself and the layers before it in `LAYERS` (plus the
two util modules). The app level (runner, run, presets, settings, tools, ui) may import
anything; no layered package may import it. Imports under `if TYPE_CHECKING:` are only
names for type hints and are not counted.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "backtester"
LAYERS = [
    "core", "data", "detectors", "sessions", "strategy", "engine", "analytics", "risk", "live",
]  # fmt: skip
UTIL = {"paths", "cli", "filelock"}  # import nothing from backtester
APP = {"runner", "run", "presets", "settings", "tools", "ui", "jobs"}


def runtime_imports(path: Path) -> set[str]:
    """Top-level backtester package names (`data`, `runner`, ...) the file imports."""
    tree = ast.parse(path.read_text(encoding="utf8"))
    skipped: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
            skipped.update(id(n) for n in ast.walk(node))
    out: set[str] = set()
    for node in ast.walk(tree):
        if id(node) in skipped:
            continue
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
            if node.module == "backtester":  # `from backtester import cli`
                names = [f"backtester.{a.name}" for a in node.names]
        elif isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        else:
            continue
        for name in names:
            parts = name.split(".")
            if parts[0] == "backtester" and len(parts) > 1:
                out.add(parts[1])
    return out


def package_of(path: Path) -> str:
    rel = path.relative_to(SRC)
    return rel.parts[0] if len(rel.parts) > 1 else rel.stem


FILES = sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.relative_to(SRC).as_posix())
def test_imports_follow_the_layers(path):
    own = package_of(path)
    imported = runtime_imports(path) - {own}
    if own in UTIL:
        assert not imported, f"{own} is a util module, imports {sorted(imported)}"
    elif own in LAYERS:
        allowed = set(LAYERS[: LAYERS.index(own)]) | UTIL
        assert imported <= allowed, f"{own} must not import {sorted(imported - allowed)}"
    else:
        assert own in APP or own == "__init__", f"{own}: put it in LAYERS, UTIL or APP"


def test_every_package_is_classified():
    packages = {package_of(p) for p in FILES} - {"__init__"}
    assert packages <= set(LAYERS) | UTIL | APP
