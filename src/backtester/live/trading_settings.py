"""The non-secret trading settings. Spec: ROADMAP.md › 0.4, 7.1.

Saved in `results/trading.json` (git-ignored with results/): platform, terminal path, the
broker's symbol names (our name → the server's, e.g. a suffix) and the measured server
clock (`data/mt5_info.py`). Login, password and server are NOT here: they are only in the
Windows Credential Manager (`live/credentials.py`).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType

from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.runner import RESULTS_DIR

TRADING_FILE = RESULTS_DIR / "trading.json"
PLATFORMS = ("MT5",)  # others later
SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY")


@dataclass(frozen=True)
class TradingSettings:
    platform: str = "MT5"
    terminal_path: str = ""  # terminal64.exe; empty: the installed / running terminal
    symbols: Mapping[str, str] = field(default_factory=lambda: {s: s for s in SYMBOLS})
    server_clock: ServerClock | None = None  # None: not measured yet
    server_clock_note: str = ""  # how and when it was measured

    def __post_init__(self) -> None:
        if self.platform not in PLATFORMS:
            raise ValueError(f"unknown platform {self.platform!r} ({', '.join(PLATFORMS)})")
        given = {s: (n or "").strip() or s for s, n in self.symbols.items()}
        names = {**{s: s for s in SYMBOLS}, **given}  # unmapped: the same name
        object.__setattr__(self, "symbols", MappingProxyType(names))

    def with_symbols(self, symbols: Mapping[str, str]) -> TradingSettings:
        return replace(self, symbols={**self.symbols, **symbols})

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "terminal_path": self.terminal_path,
            "symbols": dict(self.symbols),
            "server_clock": self.server_clock.to_dict() if self.server_clock else None,
            "server_clock_note": self.server_clock_note,
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> TradingSettings:
        return cls(
            platform=data.get("platform", "MT5"),
            terminal_path=data.get("terminal_path", ""),
            symbols=data.get("symbols") or {},
            server_clock=ServerClock.from_dict(data.get("server_clock")),
            server_clock_note=data.get("server_clock_note", ""),
        )


def load_trading_settings(path: Path = TRADING_FILE) -> TradingSettings:
    """The saved settings, or the defaults when there is no (readable) file."""
    try:
        return TradingSettings.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError):
        return TradingSettings()


def save_trading_settings(settings: TradingSettings, path: Path = TRADING_FILE) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
