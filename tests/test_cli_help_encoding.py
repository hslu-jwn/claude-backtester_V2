"""`--help` must print on a Windows console (cp1252). Found in the V2.6 full check (2026-10-27):
`python -m backtester.data.histdata --help` crashed on a Unicode minus sign in its docstring."""

import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
HELP_MODULES = sorted(
    ".".join(p.relative_to(SRC).with_suffix("").parts)
    for p in (SRC / "backtester").rglob("*.py")
    if "description=__doc__" in p.read_text(encoding="utf-8")
)


def test_some_modules_use_their_docstring_as_help():
    assert "backtester.data.histdata" in HELP_MODULES


@pytest.mark.parametrize("name", HELP_MODULES)
def test_help_text_encodes_on_a_windows_console(name):
    doc = importlib.import_module(name).__doc__ or ""
    bad = sorted({c for c in doc if c.encode("cp1252", "replace") == b"?" and c != "?"})
    assert not bad, f"{name}: characters a cp1252 console cannot print: {bad}"
