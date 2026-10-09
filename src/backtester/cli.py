"""Helpers for the command-line tools."""

from __future__ import annotations

import contextlib
import sys


def utf8_output() -> None:
    """Print →, −, ⚙ … also when the output is piped on Windows (cp1252 by default)."""
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")
