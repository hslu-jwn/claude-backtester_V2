"""utf8_output: tools print →, −, ⚙ even when stdout is a cp1252 pipe (Windows)."""

from __future__ import annotations

import io
import sys

from backtester.cli import utf8_output


def test_switches_streams_to_utf8_and_replaces_what_cannot_be_encoded(monkeypatch):
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", newline="
")
    err = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", newline="
")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    utf8_output()
    print("→ −1.5R ⚙")
    out.flush()
    assert out.buffer.getvalue().decode("utf-8") == "→ −1.5R ⚙\n"


def test_streams_without_reconfigure_are_left_alone(monkeypatch):
    class Plain:  # no .reconfigure, like a captured or replaced stream
        def write(self, s):
            return len(s)

    monkeypatch.setattr(sys, "stdout", Plain())
    monkeypatch.setattr(sys, "stderr", Plain())
    utf8_output()  # must not raise
