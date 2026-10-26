"""Test cases: exact former sweep settings, no sampling, valid command headers.
Oracle exported from old sweep functions before creating replacement grids.
"""

import json
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import time
from enum import Enum
from pathlib import Path

import pytest

from backtester.tools.research_grid import expand, load_grid, variant_settings

ORACLE = json.loads(
    (Path(__file__).parent / "fixtures/gm3_sweeps.json").read_text(encoding="utf-8")
)


def normalize(value):
    if is_dataclass(value):
        return normalize(asdict(value))
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(normalize(v) for v in value)
    if isinstance(value, (tuple, list)):
        return [normalize(v) for v in value]
    return value


@pytest.mark.parametrize("name", ORACLE)
def test_replacement_matches_old_sweep(name):
    path = Path("research/grids") / f"{name}.toml"
    spec = load_grid(path)
    variants, _, sampled = expand(spec)
    assert not sampled
    actual = [normalize(variant_settings(spec, v).strategy) for v in variants]
    assert sorted(json.dumps(x, sort_keys=True) for x in actual) == sorted(
        json.dumps(x, sort_keys=True) for x in ORACLE[name]
    )
    header = path.read_text(encoding="utf-8").split("strategy =", 1)[0]
    assert "Old tool:" in header and "Default command:" in header
    assert "not carried over" in header
