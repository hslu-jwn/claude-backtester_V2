"""Research grid file: load, validate and expand to variants. Spec: research-runner.md > Grid file.

    strategy = "opening_range"          # a strategy/registry.py name
    symbols = ["US500", "NAS100"]
    min_trades = 100                    # optional: development trades needed to be ranked
    max_variants = 200                  # optional: above it a seeded random sample is run
    seed = 1                            # optional: seed of that sample

    [base]                              # optional: start values, else the config defaults
    entry_mode = "range"

    [grid]                              # setting -> list of values; variants = the full product
    range_minutes = [5, 15, 30]
    target_r = [0, 1]

Setting names are the strategy config's field names (dotted for nested fields, e.g.
"strong_move.atr_period"); shared run settings are swept by their full path (`warmup_days`,
`engine.costs.swap_enabled`, `detectors.fvg.strong_move_filter`, ...). Values are checked against
the field's type (the same kinds as the settings menu, `settings.py`); an unknown name or a wrong
type raises `GridError` with the valid names. A combination the config itself rejects (e.g. an
entry window not longer than the range) also raises `GridError`, naming the variant.

Variant ids follow the full product (`v0000` ...), so a sample keeps the ids of the full grid.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
import tomllib
from dataclasses import dataclass, field
from datetime import date, time
from pathlib import Path

from backtester.runner import RunSettings
from backtester.settings import Leaf, SettingsError, leaves, settings_from_values
from backtester.strategy.registry import REGISTRY, default_config

TOP_LEVEL = (
    "strategy",
    "symbols",
    "min_trades",
    "max_variants",
    "seed",
    "base",
    "grid",
    "grids",
    "shocks",
    "sensitivity",
    "walk_forward",
    "train_years",
)
ID_HASH_LENGTH = 8


class GridError(ValueError):
    """The grid file is unreadable or invalid; the message says what to change."""


@dataclass(frozen=True, slots=True)
class ResearchConfig:
    min_trades: int = 100  # spec: development trades needed to be ranked
    max_variants: int = 200  # above this many variants a seeded random sample is run
    seed: int = 1  # seed of that sample
    cutoff: date = date(2021, 9, 14)  # first test day (data split rule of 2026-10-15)
    live_expectation_range: tuple[float, float] = (0.50, 0.75)

    def __post_init__(self) -> None:
        if self.min_trades < 0:
            raise ValueError("min_trades must be >= 0")
        if self.max_variants < 1:
            raise ValueError("max_variants must be >= 1")
        bounds = self.live_expectation_range
        if (
            len(bounds) != 2
            or not all(math.isfinite(v) for v in bounds)
            or not (0 <= bounds[0] <= bounds[1] <= 1)
        ):
            raise ValueError("live_expectation_range must have finite bounds 0 <= low <= high <= 1")


@dataclass(frozen=True, slots=True)
class GridSpec:
    name: str  # the file name without .toml
    strategy: str
    symbols: tuple[str, ...]
    base: dict  # setting name -> value (as written in the file, enums normalised)
    grid: dict  # setting name -> list of values
    min_trades: int
    max_variants: int
    seed: int
    path: Path | None = None
    grids: tuple[Family, ...] = ()
    shocks: bool = True
    duplicates: list[dict] = field(default_factory=list, compare=False)
    sensitivity: bool = True
    walk_forward: str | None = None
    train_years: int = 3


@dataclass(frozen=True, slots=True)
class Family:
    name: str
    base: dict
    grid: dict
    compare_to: str | None = None


@dataclass(frozen=True, slots=True)
class Variant:
    id: str  # v0000: the index in the full product
    name: str  # "range_minutes=15 target_r=1" (the grid's own settings only)
    overrides: dict  # base + this variant's grid values, setting name -> value
    family: str = "grid"


# --- setting names and values -------------------------------------------------------------


def _shared(leaf: Leaf) -> bool:
    return not leaf.path.startswith("strategy.")


def _name_of(leaf: Leaf) -> str:
    return leaf.path if _shared(leaf) else leaf.path.removeprefix("strategy.")


def _leaf_table(strategy: str) -> dict[str, Leaf]:
    """{setting name: leaf} for the strategy's config and the shared run settings."""
    base = RunSettings(strategy=default_config(strategy))
    return {_name_of(leaf): leaf for leaf in leaves(base)}


def valid_names(strategy: str) -> list[str]:
    return list(_leaf_table(strategy))


def _collapse(names: list[str]) -> list[str]:
    """Names with every symbol key (an all-capitals path segment) written as <SYMBOL>, once."""
    out = {}
    for name in names:
        parts = ["<SYMBOL>" if p.isupper() else p for p in name.split(".")]
        out.setdefault(".".join(parts), None)
    return list(out)


def _unknown(name: str, strategy: str, where: str) -> GridError:
    names = valid_names(strategy)
    own = [n for n in names if not n.startswith(("engine.", "detectors.", "warmup_days"))]
    shared = _collapse([n for n in names if n not in own])
    return GridError(
        f"{where}: unknown setting {name!r} for strategy {strategy}.\n"
        f"  {strategy} settings: {', '.join(own)}\n"
        f"  shared settings: {', '.join(shared)}"
    )


def _coerce(leaf: Leaf, value, name: str, where: str):
    """The value in the settings form (see settings.py), or GridError for a wrong type."""
    kind = leaf.kind.removeprefix("optional_")

    def bad(expected: str) -> GridError:
        return GridError(f"{where}: {name} = {value!r}: expected {expected}")

    if kind == "bool":
        if not isinstance(value, bool):
            raise bad("true or false")
        return value
    if kind in ("int", "float"):
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise bad("a number")
        if kind == "int" and value != int(value):
            raise bad("a whole number")
        return int(value) if kind == "int" else value
    if kind == "enum":
        if not isinstance(value, str):
            raise bad(f"one of {', '.join(leaf.options)}")
        match = {o.lower(): o for o in leaf.options}.get(value.lower())
        if match is None:
            raise bad(f"one of {', '.join(leaf.options)}")
        return match
    if kind == "enum_set":
        lower = {o.lower(): o for o in leaf.options}
        if not isinstance(value, list) or not all(
            isinstance(v, str) and v.lower() in lower for v in value
        ):
            raise bad(f"a list of {', '.join(leaf.options)}")
        return [lower[v.lower()] for v in value]
    if kind == "float_list":
        if not isinstance(value, list) or not all(
            isinstance(v, int | float) and not isinstance(v, bool) for v in value
        ):
            raise bad("a list of numbers")
        return list(value)
    if kind == "time":
        try:
            time.fromisoformat(value)
        except (TypeError, ValueError):
            raise bad('a time like "09:30"') from None
        return value
    if not isinstance(value, str):  # text
        raise bad("text")
    return value


def _check_table(
    table: dict, strategy: str, where: str, leaves_by_name: dict[str, Leaf], as_lists: bool
) -> dict:
    out = {}
    for name, raw in table.items():
        leaf = leaves_by_name.get(name)
        if leaf is None:
            raise _unknown(name, strategy, where)
        if not as_lists:
            out[name] = _coerce(leaf, raw, name, where)
            continue
        if not isinstance(raw, list) or not raw:
            raise GridError(f"{where}: {name} must be a non-empty list of values")
        values = [_coerce(leaf, v, name, where) for v in raw]
        if len({json.dumps(v) for v in values}) != len(values):
            raise GridError(f"{where}: {name} has a duplicate value")
        out[name] = values
    return out


# --- loading ---------------------------------------------------------------------------------


def _number(data: dict, key: str, default: int, minimum: int) -> int:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise GridError(f"{key} must be a whole number >= {minimum}, got {value!r}")
    return value


def load_grid(path: Path | str, config: ResearchConfig | None = None) -> GridSpec:
    cfg = config or ResearchConfig()
    path = Path(path)
    if not path.is_file():
        raise GridError(f"no grid file {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise GridError(f"{path.name} is not valid TOML: {e}") from e
    unknown = [k for k in data if k not in TOP_LEVEL]
    if unknown:
        raise GridError(
            f"unknown entry {unknown[0]!r} in {path.name} (valid: {', '.join(TOP_LEVEL)})"
        )
    strategy = data.get("strategy")
    if strategy not in REGISTRY:
        raise GridError(f"strategy {strategy!r} is not registered (known: {', '.join(REGISTRY)})")
    symbols = data.get("symbols")
    if (
        not isinstance(symbols, list)
        or not symbols
        or not all(isinstance(s, str) and s for s in symbols)
    ):
        raise GridError("symbols must be a non-empty list of symbol names")
    table = _leaf_table(strategy)
    base = data.get("base", {})
    grid = data.get("grid", {})
    if not isinstance(base, dict) or not isinstance(grid, dict):
        raise GridError("[base] and [grid] must be tables")
    if not isinstance(data.get("shocks", True), bool):
        raise GridError("shocks must be true or false")
    if not isinstance(data.get("sensitivity", True), bool):
        raise GridError("sensitivity must be true or false")
    if "walk_forward" in data and data["walk_forward"] not in ("anchored", "rolling"):
        raise GridError("walk_forward must be anchored or rolling")
    train_years = _number(data, "train_years", 3, 1)
    families = []
    if "grids" in data:
        raw = data["grids"]
        if "grid" in data or not isinstance(raw, list) or not raw:
            raise GridError("use either [grid] or non-empty [[grids]] tables")
        for i, item in enumerate(raw, 1):
            where = f"grids[{i}]"
            if not isinstance(item, dict) or set(item) - {"name", "base", "grid", "compare_to"}:
                raise GridError(f"{where}: only name, base, grid and compare_to are allowed")
            name = item.get("name", f"grid{i}")
            if not isinstance(name, str) or not name.strip() or name == "all":
                raise GridError(f"{where}: name must be non-empty and cannot be 'all'")
            if any(f.name == name for f in families):
                raise GridError(f"{where}: duplicate family name {name!r}")
            if not all(isinstance(item.get(k, {}), dict) for k in ("base", "grid")):
                raise GridError(f"{where}: base and grid must be tables")
            families.append(
                Family(
                    name,
                    _check_table(item.get("base", {}), strategy, where, table, False),
                    _check_table(item.get("grid", {}), strategy, where, table, True),
                    item.get("compare_to"),
                )
            )
    for family in families:
        if family.compare_to is not None and (
            not isinstance(family.compare_to, str)
            or family.compare_to == family.name
            or family.compare_to not in {f.name for f in families}
        ):
            raise GridError(f"{family.name}: compare_to must name another existing family")
    spec = GridSpec(
        name=path.stem,
        strategy=strategy,
        symbols=tuple(dict.fromkeys(s.upper() for s in symbols)),
        base=_check_table(base, strategy, "[base]", table, as_lists=False),
        grid=_check_table(grid, strategy, "[grid]", table, as_lists=True),
        min_trades=_number(data, "min_trades", cfg.min_trades, 0),
        max_variants=_number(data, "max_variants", cfg.max_variants, 1),
        seed=_number(data, "seed", cfg.seed, 0),
        path=path,
        grids=tuple(families),
        shocks=data.get("shocks", True),
        sensitivity=data.get("sensitivity", True),
        walk_forward=data.get("walk_forward"),
        train_years=train_years,
    )
    return spec


# --- expansion ---------------------------------------------------------------------------------


def grid_size(spec: GridSpec) -> int:
    if spec.grids:
        return sum(math.prod(len(v) for v in f.grid.values()) for f in spec.grids)
    return math.prod(len(v) for v in spec.grid.values())


def _fmt(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, list):
        return "[" + ",".join(_fmt(v) for v in value) + "]"
    return str(value)


def _combination(spec: GridSpec | Family, index: int) -> dict:
    """The index-th combination of the product (first setting varies slowest)."""
    picks = {}
    for name in reversed(list(spec.grid)):
        index, i = divmod(index, len(spec.grid[name]))
        picks[name] = spec.grid[name][i]
    return {name: picks[name] for name in spec.grid}


def families(spec: GridSpec) -> tuple[Family, ...]:
    return spec.grids or (Family("grid", {}, spec.grid),)


def family_variants(spec: GridSpec):
    """Full products, in file order. Spec: research-runner.md > Combined grids."""
    offset = 0
    for family in families(spec):
        size = math.prod(len(v) for v in family.grid.values())
        for index in range(size):
            combo = _combination(family, index)
            name = " ".join(f"{k}={_fmt(v)}" for k, v in combo.items()) or "base"
            yield Variant(
                f"v{offset + index:04d}", name, {**spec.base, **family.base, **combo}, family.name
            )
        offset += size


def resolved_values(spec: GridSpec, variant: Variant) -> dict:
    return {_name_of(leaf): leaf.default for leaf in leaves(variant_settings(spec, variant))}


def resolved_key(spec: GridSpec, variant: Variant) -> str:
    return json.dumps(resolved_values(spec, variant), sort_keys=True, default=str)


def variant_settings(spec: GridSpec, variant: Variant) -> RunSettings:
    """The run settings of a variant: the strategy's spec defaults with `overrides` applied."""
    table = _leaf_table(spec.strategy)
    values = {table[name].path: value for name, value in variant.overrides.items()}
    base = RunSettings(strategy=default_config(spec.strategy))
    try:
        return settings_from_values(values, base)
    except SettingsError as e:
        raise GridError(f"variant {variant.name}: {e}") from e


def expand(spec: GridSpec) -> tuple[list[Variant], int, bool]:
    """(variants, size of the full grid, sampled). Above `max_variants` a seeded random sample
    of the full product (kept in product order)."""
    size = grid_size(spec)
    if spec.grids:
        unique = {}
        spec.duplicates.clear()
        for variant in family_variants(spec):
            key = resolved_key(spec, variant)
            if key in unique:
                spec.duplicates.append(
                    {"id": variant.id, "family": variant.family, "retained": unique[key].id}
                )
            else:
                unique[key] = variant
        variants = list(unique.values())
        sampled = len(variants) > spec.max_variants
        if sampled:
            indexes = sorted(
                random.Random(spec.seed).sample(range(len(variants)), spec.max_variants)
            )
            variants = [variants[i] for i in indexes]
        return variants, size, sampled
    sampled = size > spec.max_variants
    indexes = (
        sorted(random.Random(spec.seed).sample(range(size), spec.max_variants))
        if sampled
        else range(size)
    )
    variants = []
    for i in indexes:
        combo = _combination(spec, i)
        name = " ".join(f"{k}={_fmt(v)}" for k, v in combo.items()) or "base"
        variant = Variant(f"v{i:04d}", name, {**spec.base, **combo})
        variant_settings(spec, variant)  # a combination the config rejects stops here
        variants.append(variant)
    return variants, size, sampled


def grid_id(spec: GridSpec, variants: list[Variant]) -> str:
    """`<file name>_<hash>`: the hash covers strategy, symbols, base and the variants run, so the
    same idea gets the same folder (resume, retest guard) and a changed grid a new one."""
    key = json.dumps(
        [spec.strategy, sorted(spec.symbols), spec.base, [(v.id, v.overrides) for v in variants]],
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:ID_HASH_LENGTH]
    safe = re.sub(r"[^A-Za-z0-9_.-]", "-", spec.name)
    return f"{safe}_{digest}"
