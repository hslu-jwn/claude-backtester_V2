"""Settings of the template strategy: every tunable value lives here with its spec default.

Spec: docs/strategy-<name>.md (write it first, CLAUDE.md › Specs are the source of truth).
Put only what THIS strategy needs here; costs, break-even and the warm-up are the shared
`RunSettings` (`runner.py`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TemplateConfig:
    min_rr: float = 2.0  # smallest reward:risk a signal needs (example setting)

    def __post_init__(self) -> None:
        if self.min_rr <= 0:
            raise ValueError("min_rr must be > 0")
