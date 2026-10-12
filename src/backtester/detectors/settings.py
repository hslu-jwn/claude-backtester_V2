"""Detector settings every strategy shares (swings, FVG, order block, equilibrium).

Spec: confluences.md. One group in `RunSettings.detectors`, so the settings menu and the
presets have one place for them; a strategy config (`strategy/<name>/config.py`) holds only
what belongs to that strategy. The defaults are the spec's.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtester.detectors.equilibrium import EquilibriumConfig
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.order_block import OrderBlockConfig
from backtester.detectors.swings import SwingConfig


@dataclass(frozen=True, slots=True)
class DetectorSettings:
    swings: SwingConfig = field(default_factory=SwingConfig)  # doji threshold per symbol
    fvg: FvgConfig = field(default_factory=FvgConfig)  # strong-move filter default off
    order_block: OrderBlockConfig = field(default_factory=OrderBlockConfig)  # filter on
    equilibrium: EquilibriumConfig = field(default_factory=EquilibriumConfig)


DEFAULT_DETECTORS = DetectorSettings()  # the spec defaults (frozen, safe as a default argument)
