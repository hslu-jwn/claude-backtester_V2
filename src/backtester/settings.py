"""Run settings as plain values, for the settings menu (ROADMAP.md › 4.1) and presets (4.2).

Everything is generated from the config dataclasses (`runner.RunSettings`: strategy 1's
`SessionZoneSweepConfig` with its detector configs, `EngineConfig` with the costs, the
warm-up), so a new field shows up in the menu by itself:

- `leaves(settings)` walks the dataclasses and lists every editable value (`Leaf`): its
  path (e.g. "strategy.min_rr", "engine.costs.symbols.XAUUSD.spread"), kind, spec default
  and help text, taken from the field's comment in the source (trailing, else the comment
  lines right above it).
- `form_values` / `settings_from_values` convert between a `RunSettings` and the flat
  {path: value} dict the menu edits (JSON values: enums by name, sets as lists, times as
  "HH:MM", None = off). Invalid values raise `SettingsError` with the field's path.
- `to_dict` / `from_dict` / `to_json` / `from_json`: the nested JSON form (settings.json of
  a run, presets). `from_json` is cached, so it can key caches (the chart's Trades overlay).

Linked and hidden values: the engine's session starts always follow the strategy's
(`engine.sessions`, one setting for both), and `strategy.strong_move.atr_mult` is not
shown because nothing reads it (the strong-move multipliers are per FVG / OB).
"""

from __future__ import annotations

import inspect
import json
import re
import types
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import time
from enum import Enum
from functools import cache, lru_cache
from typing import Any, Union, get_args, get_origin, get_type_hints

from backtester.runner import RunSettings, jsonable

HIDDEN = frozenset({"engine.sessions", "strategy.strong_move.atr_mult"})


class SettingsError(ValueError):
    """An invalid setting; `path` names the field (None: a rule across several fields)."""

    def __init__(self, message: str, path: str | None = None):
        super().__init__(message)
        self.path = path


@dataclass(frozen=True)
class Leaf:
    path: str
    kind: str  # bool, int, float, optional_int, optional_float, enum, enum_set, time, text
    default: Any  # form value (see the module docstring)
    help: str = ""
    options: tuple[str, ...] = ()  # enum / enum_set: the member names


# --- help text from the source ---------------------------------------------------------

_FIELD = re.compile(r"^\s+(\w+)\s*:(?!\s*\Z)(.*)$")


@cache
def field_comments(cls: type) -> dict[str, str]:
    """{field name: its comment}: the trailing comment, else the comment lines right above."""
    names = {f.name for f in fields(cls)}
    out: dict[str, str] = {}
    block: list[str] = []
    try:
        source = inspect.getsource(cls)
    except (OSError, TypeError):
        return out
    for line in source.splitlines()[1:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            block.append(stripped.lstrip("#").strip())
            continue
        m = _FIELD.match(line)
        if m and m.group(1) in names and m.group(1) not in out:
            trailing = m.group(2).split("  #", 1)
            text = trailing[1].strip() if len(trailing) > 1 else " ".join(block)
            out[m.group(1)] = text
        block = []
    return out


# --- walking the dataclasses -----------------------------------------------------------


def _optional(hint) -> Any | None:
    """X for `X | None`, else None."""
    if get_origin(hint) in (Union, types.UnionType):
        args = [a for a in get_args(hint) if a is not type(None)]
        if len(args) == 1 and len(get_args(hint)) == 2:
            return args[0]
    return None


def _is_mapping(hint) -> bool:
    return get_origin(hint) is Mapping


def _kind(hint) -> tuple[str, tuple[str, ...]]:
    inner = _optional(hint)
    if inner is not None:
        kind, options = _kind(inner)
        return f"optional_{kind}", options
    if get_origin(hint) is frozenset:
        (member,) = get_args(hint)
        return "enum_set", tuple(m.name for m in member)
    if isinstance(hint, type) and issubclass(hint, Enum):
        return "enum", tuple(m.name for m in hint)
    simple = {bool: "bool", int: "int", float: "float", str: "text", time: "time"}
    if hint in simple:
        return simple[hint], ()
    raise TypeError(f"no settings kind for {hint!r}")


def to_form(value) -> Any:
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, frozenset | set):
        return sorted(v.name for v in value)
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return value


def _walk(value, hint, path: str, help_: str, out: list[Leaf]) -> None:
    if path in HIDDEN:
        return
    if is_dataclass(hint):
        hints, comments = get_type_hints(hint), field_comments(hint)
        for f in fields(hint):
            sub = f"{path}.{f.name}" if path else f.name
            _walk(getattr(value, f.name), hints[f.name], sub, comments.get(f.name, ""), out)
        return
    if _is_mapping(hint):
        _, value_hint = get_args(hint)
        for key in value:
            _walk(value[key], value_hint, f"{path}.{key}", help_, out)
        return
    kind, options = _kind(hint)
    out.append(Leaf(path, kind, to_form(value), help_, options))


def leaves(settings: RunSettings | None = None) -> list[Leaf]:
    """Every editable value of `settings` (default: the spec defaults), in field order."""
    out: list[Leaf] = []
    _walk(settings or RunSettings(), RunSettings, "", "", out)
    return out


def form_values(settings: RunSettings | None = None) -> dict[str, Any]:
    return {leaf.path: leaf.default for leaf in leaves(settings)}


# --- back to dataclasses ---------------------------------------------------------------


def _convert(hint, value, path: str):
    inner = _optional(hint)
    if inner is not None:
        return None if value in (None, "") else _convert(inner, value, path)
    if is_dataclass(hint):
        return _build(hint, value, path)
    if _is_mapping(hint):
        _, value_hint = get_args(hint)
        return types.MappingProxyType(
            {k: _convert(value_hint, v, f"{path}.{k}") for k, v in value.items()}
        )
    if get_origin(hint) is frozenset:
        (member,) = get_args(hint)
        return frozenset(member[v] for v in value)
    if isinstance(hint, type) and issubclass(hint, Enum):
        return hint[value]
    if value is None or value == "":
        raise SettingsError("a value is needed", path)
    if hint is bool:
        return bool(value)
    if hint is int:
        number = float(value)
        if number != int(number):
            raise SettingsError(f"{value} is not a whole number", path)
        return int(number)
    if hint is float:
        return float(value)
    if hint is time:
        return time.fromisoformat(value)
    return str(value)


def _build(cls, data: Mapping, path: str = ""):
    if not isinstance(data, Mapping):
        raise SettingsError(f"expected a group of settings, got {data!r}", path or None)
    hints, kwargs = get_type_hints(cls), {}
    for f in fields(cls):
        if f.name in data:
            sub = f"{path}.{f.name}" if path else f.name
            try:
                kwargs[f.name] = _convert(hints[f.name], data[f.name], sub)
            except SettingsError:
                raise
            except (KeyError, TypeError, ValueError) as e:
                raise SettingsError(f"invalid value {data[f.name]!r} ({e})", sub) from e
    try:
        return cls(**kwargs)
    except (TypeError, ValueError) as e:
        raise SettingsError(str(e), path or None) from e


def to_dict(settings: RunSettings) -> dict:
    return jsonable(settings)


def from_dict(data: Mapping) -> RunSettings:
    """RunSettings from its nested JSON form; missing values keep their defaults."""
    return _build(RunSettings, data)


def to_json(settings: RunSettings) -> str:
    """Canonical JSON (sorted keys): equal settings give the same text."""
    normal = to_dict(from_dict(to_dict(settings)))  # e.g. an int default in a float field
    return json.dumps(normal, sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=64)
def from_json(text: str) -> RunSettings:
    return from_dict(json.loads(text)) if text else RunSettings()


def settings_from_values(values: Mapping[str, Any], base: RunSettings | None = None):
    """RunSettings with the menu's flat {path: value} applied to `base` (default: the
    spec defaults). Unknown paths are ignored (e.g. a preset from an older version)."""
    data = to_dict(base or RunSettings())
    known = {leaf.path for leaf in leaves(base)}
    for path, value in values.items():
        if path not in known:
            continue
        *parents, name = path.split(".")
        node = data
        for p in parents:
            node = node[p]
        node[name] = value
    settings = from_dict(data)
    return replace(settings, engine=replace(settings.engine, sessions=settings.strategy.sessions))
