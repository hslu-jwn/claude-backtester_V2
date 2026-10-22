"""Exact trade references, without market data. Spec: ROADMAP V2.4, step 1."""

import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction
from backtester.engine.trade import ExitReason, PartialExit, TradeResult
from backtester.runner import RunSettings
from backtester.strategy.registry import REGISTRY, default_config
from backtester.tools import golden


def trade():
    now = datetime(2023, 1, 3, 12, 15, 0, 123456, UTC)
    return TradeResult(
        symbol="XAUUSD",
        direction=Direction.BULLISH,
        entry_time=now,
        entry_candle=now,
        entry=1900.1234567890124,
        entry_fill=1900.2234567890123,
        initial_stop=1890.0,
        take_profit=None,
        exit_time=now,
        exit_candle=now,
        exit_price=1910.0,
        exit_fill=1910.0,
        exit_reason=ExitReason.SIGNAL,
        r_gross=0.9876543210987654,
        r_net=0.8765432109876543,
        spread_r=1e-20,
        commission_r=0.1,
        break_even_time=None,
        break_even_stop=None,
        mae_r=-0.0,
        mfe_r=1e20,
        tags=frozenset({"z", "a"}),
        reason="hand-built",
        swap_r=-0.12345678901234567,
        parts=(PartialExit(1.0, now, now, 1910.0, 1910.0, ExitReason.SIGNAL, 1.0, 0.9),),
    )


def test_serialization_round_trip_every_field():
    original = trade()
    line = golden.serialize_trade(original)
    record = json.loads(line)
    assert set(record) == {f.name for f in fields(TradeResult)}
    assert record["direction"] == "BULLISH"
    assert record["exit_reason"] == "SIGNAL"
    assert record["entry_time"] == "2023-01-03T12:15:00.123456+00:00"
    assert record["tags"] == ["a", "z"]
    for f in fields(original):
        value = getattr(original, f.name)
        if isinstance(value, float):
            assert record[f.name].hex() == value.hex()
    for name in ("entry_time", "entry_candle", "exit_time", "exit_candle"):
        record[name] = datetime.fromisoformat(record[name])
    record["direction"] = Direction[record["direction"]]
    record["exit_reason"] = ExitReason[record["exit_reason"]]
    record["tags"] = frozenset(record["tags"])
    for part in record["parts"]:
        part["reason"] = ExitReason[part["reason"]]
        for name in ("time", "candle"):
            part[name] = datetime.fromisoformat(part[name])
    record["parts"] = tuple(PartialExit(**p) for p in record["parts"])
    assert TradeResult(**record) == original
    assert repr(original.entry) in line


def test_first_differing_field_including_nested_parts():
    old = json.loads(golden.serialize_trade(trade()))
    new = json.loads(golden.serialize_trade(replace(trade(), entry=1901.0, r_net=-1.0)))
    report = golden.compare_trades([old], [new])
    assert "trade 0" in report and "entry" in report
    assert repr(trade().entry) in report and "1901.0" in report
    assert "r_net" not in report
    new = json.loads(golden.serialize_trade(trade()))
    new["parts"][0]["fill"] = 1911.0
    assert "parts[0].fill" in golden.compare_trades([old], [new])
    assert golden.compare_trades([old], [old]) is None


@pytest.mark.parametrize("old_count,new_count", [(1, 0), (0, 1), (2, 1), (1, 2)])
def test_missing_and_extra_trades(old_count, new_count):
    row = json.loads(golden.serialize_trade(trade()))
    report = golden.compare_trades([row] * old_count, [row] * new_count)
    assert f"trade {min(old_count, new_count)}" in report
    assert f"old={old_count}, new={new_count}" in report
    assert f"difference={new_count - old_count:+d}" in report


def test_config_is_frozen_and_covers_registry():
    config = golden.GoldenConfig()
    assert set(dict(config.strategies)) == set(REGISTRY)
    assert config.start == date(2023, 1, 1) and config.end == date(2023, 12, 31)
    assert config.folder.as_posix() == "tests/golden"
    assert dict(config.strategies)["no_wick"] == ("XAUUSD", "GBPUSD", "NAS100", "US500")
    with pytest.raises(FrozenInstanceError):
        config.start = date(2022, 1, 1)


def test_cli_write_check_defaults_manifest_and_difference(tmp_path, monkeypatch, capsys):
    config = replace(golden.GoldenConfig(), folder=tmp_path)
    calls = []
    trades = [trade()]

    def run(symbols, start, end, settings, sources, *, workers):
        calls.append((symbols, start, end, settings, sources, workers))
        return SimpleNamespace(trades=trades, notes=(), runs={})

    monkeypatch.setattr(golden, "run_backtests", run)
    monkeypatch.setattr(golden, "git_commit", lambda: "abc123")
    args = ["--strategy", "no_wick", "trend_following", "--workers", "1"]
    assert golden.main(["--write", *args], config=config) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["start"] == "2023-01-01" and manifest["end"] == "2023-12-31"
    assert manifest["git_commit"] == "abc123" and manifest["date"]
    assert manifest["strategies"]["no_wick"]["trade_count"] == 1
    for name, call in zip(("no_wick", "trend_following"), calls):
        assert call[3] == RunSettings(strategy=default_config(name))
        assert call[4] is golden.DEFAULT_SOURCES and call[5] == 1
    assert golden.main(["--check", *args], config=config) == 0
    assert "no_wick: identical" in capsys.readouterr().out
    trades[0] = replace(trades[0], r_net=-1.0)
    assert golden.main(["--check", *args], config=config) == 1
    assert "r_net" in capsys.readouterr().out
    (tmp_path / "no_wick.jsonl").unlink()
    assert golden.main(["--check", "--strategy", "no_wick"], config=config) == 1
    assert "missing" in capsys.readouterr().out


def test_subset_write_preserves_other_manifest_entries(tmp_path, monkeypatch):
    config = replace(golden.GoldenConfig(), folder=tmp_path)
    monkeypatch.setattr(golden, "git_commit", lambda: "abc123")
    monkeypatch.setattr(
        golden, "run_backtests", lambda *a, **k: SimpleNamespace(trades=(), notes=(), runs={})
    )
    for name in ("no_wick", "trend_following"):
        assert golden.main(["--write", "--strategy", name], config=config) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert set(manifest["strategies"]) == {"no_wick", "trend_following"}
