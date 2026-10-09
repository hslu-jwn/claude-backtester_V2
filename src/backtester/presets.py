"""Named settings presets. Spec: ROADMAP.md › 4.2.

One JSON file per preset in `results/presets/` (git-ignored with results/):
{"name": …, "settings": <RunSettings as nested JSON, backtester/settings.py `to_dict`>}.
"Default" is not a file: it is always the spec defaults and can't be overwritten,
renamed or deleted. Names: 1-60 letters, digits, spaces and `_ - . ( ) +`; compared
without case (Windows file names), so "tight sl" and "Tight SL" are the same preset.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from backtester.runner import RESULTS_DIR, RunSettings
from backtester.settings import SettingsError, from_dict, to_dict

PRESETS_DIR = RESULTS_DIR / "presets"
DEFAULT = "Default"
_NAME = re.compile(r"^[A-Za-z0-9 _.()+-]{1,60}$")


class PresetError(ValueError):
    pass


def _check_name(name: str | None) -> str:
    name = (name or "").strip()
    if not _NAME.match(name) or name.strip(".") == "":
        raise PresetError(
            "a preset name is 1-60 letters, digits, spaces or _ - . ( ) +"
            if name
            else "enter a preset name"
        )
    return name


def _is_default(name: str) -> bool:
    return name.strip().lower() == DEFAULT.lower()


def _files(folder: Path) -> dict[str, Path]:
    """{name in the file: path}."""
    out = {}
    folder = Path(folder)
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            name = json.loads(path.read_text(encoding="utf-8"))["name"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        out[name] = path
    return out


def _find(name: str, folder: Path) -> Path | None:
    for found, path in _files(folder).items():
        if found.lower() == name.strip().lower():
            return path
    return None


def list_presets(folder: Path = PRESETS_DIR) -> list[str]:
    """The preset names: Default first, then the saved ones by name."""
    return [DEFAULT, *sorted(_files(folder), key=str.lower)]


def load_preset(name: str, folder: Path = PRESETS_DIR) -> RunSettings:
    if _is_default(name):
        return RunSettings()
    path = _find(name, folder)
    if path is None:
        raise PresetError(f"no preset {name!r}")
    try:
        return from_dict(json.loads(path.read_text(encoding="utf-8"))["settings"])
    except (OSError, ValueError, KeyError, SettingsError) as e:
        raise PresetError(f"preset {name!r} can't be read: {e}") from e


def save_preset(name: str, settings: RunSettings, folder: Path = PRESETS_DIR) -> str:
    """Save (or overwrite) `name`; returns the name as saved."""
    name = _check_name(name)
    if _is_default(name):
        raise PresetError('"Default" is the spec defaults and can\'t be overwritten: Save as …')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    existing = _find(name, folder)
    if existing is not None:  # the same preset (names ignore case): keep its spelling
        name = json.loads(existing.read_text(encoding="utf-8"))["name"]
    path = existing or folder / f"{name}.json"
    data = {"name": name, "settings": to_dict(settings)}
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return name


def rename_preset(old: str, new: str, folder: Path = PRESETS_DIR) -> str:
    new = _check_name(new)
    if _is_default(old) or _is_default(new):
        raise PresetError('"Default" can\'t be renamed or replaced')
    path = _find(old, folder)
    if path is None:
        raise PresetError(f"no preset {old!r}")
    other = _find(new, folder)
    if other is not None and other != path:
        raise PresetError(f"a preset {new!r} exists already")
    settings = load_preset(old, folder)
    path.unlink()
    return save_preset(new, settings, folder)


def delete_preset(name: str, folder: Path = PRESETS_DIR) -> None:
    if _is_default(name):
        raise PresetError('"Default" can\'t be deleted')
    path = _find(name, folder)
    if path is None:
        raise PresetError(f"no preset {name!r}")
    path.unlink()
