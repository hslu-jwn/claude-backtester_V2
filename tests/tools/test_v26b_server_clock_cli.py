"""Frozen shared proof table is reused by queued repairs."""

import json

from backtester.tools import cache_repair


def test_cli_proves_once_then_loads_frozen_table(tmp_path, monkeypatch):
    table = {"2020-03-18": {"status": "proven", "shift": 1, "readings": {"GBPUSD": 1}}}
    target = tmp_path / "clock.json"
    monkeypatch.setattr(cache_repair, "build_server_clock_table", lambda *a, **kw: table)
    assert cache_repair.main(["--prove-clock", "--clock-table", str(target)]) == 0
    assert json.loads(target.read_text())["days"] == table
    seen = []
    monkeypatch.setattr(
        cache_repair, "repair_mt5", lambda *a, **kw: seen.append(kw["server_table"]) or []
    )
    assert cache_repair.main(["US30", "--clock-table", str(target)]) == 0
    assert seen == [table]
