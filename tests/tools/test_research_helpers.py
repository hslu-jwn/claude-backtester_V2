"""Test cases before moving shared helpers: CSV columns preserve first-seen order;
segmented execution reads each cached piece once and merges symbols and entry times.
Existing active tools must use these helpers after sweep removal.
"""

import csv
from datetime import UTC, date, datetime
from types import SimpleNamespace

from backtester.tools import research_helpers as tool


def test_csv_union(tmp_path):
    path = tmp_path / "rows.csv"
    tool.write_csv(path, [{"a": 1}, {"b": 2, "a": 3}])
    with path.open(encoding="utf-8", newline="") as f:
        assert list(csv.DictReader(f)) == [{"a": "1", "b": ""}, {"a": "3", "b": "2"}]


def test_segmented_execution(monkeypatch):
    calls = []
    pieces = [(date(2020, 1, 1), date(2020, 1, 2)), (date(2020, 1, 4), date(2020, 1, 4))]
    monkeypatch.setattr(tool, "segments", lambda symbol, start, end, sources: pieces)

    def run(symbols, start, end, settings, **kw):
        calls.append((symbols, start, end))
        return SimpleNamespace(
            runs={
                s: SimpleNamespace(
                    trades=[
                        SimpleNamespace(
                            symbol=s,
                            entry_time=datetime(start.year, start.month, start.day, tzinfo=UTC),
                        )
                    ]
                )
                for s in symbols
            }
        )

    monkeypatch.setattr(tool, "run_backtests", run)
    result = tool.run_variant(["XAUUSD", "NAS100"], pieces[0][0], pieces[-1][1], None, None, 1)
    assert len(calls) == 2
    assert len(result.trades) == 4
    assert result.trades == tuple(sorted(result.trades, key=lambda t: t.entry_time))
    assert all(len(r.trades) == 2 for r in result.runs.values())
