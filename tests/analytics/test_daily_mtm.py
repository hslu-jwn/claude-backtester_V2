"""V2.4d test cases (written before implementation).

1. Long/short, two symbols, three cuts across DST weekend; gap and signed exposure.
2. Intraday commission/swap/funding, exact-cut exit, empty period, invalid/missing marks.
3. Partial closes, entry fill/slippage and persisted trade roundtrip.
4. Cached M1 close-time selection without lookahead; one read per consecutive block.
5. CSV kinds, old trial records, union alignment, zero padding and missing files.
6. Runner saves all development/sensitivity/test series and backfills without replay.
"""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from backtester.analytics import daily, trial_log


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def trade(**kw):
    values = {
        "symbol": "A",
        "direction": "long",
        "entry_time": at("2021-03-26T11:00"),
        "exit_time": at("2021-03-29T10:00"),
        "entry": 100.0,
        "entry_fill": 102.0,
        "initial_stop": 90.0,
        "spread_r": 0.2,
        "commission_r": 0.1,
        "swap_r": -0.3,
        "funding_r": 0.0,
        "r_net": 1.4,
        "parts": (),
    }
    return SimpleNamespace(**(values | kw))


CUTS = [at(t) for t in ["2021-03-26T23:00", "2021-03-27T23:00", "2021-03-28T22:00"]]
START, END = date(2021, 3, 26), date(2021, 3, 30)


def test_three_cuts_weekend_gap_two_symbols_and_costs():
    long = trade()
    short = trade(symbol="B", direction="short", entry_fill=100.0, r_net=0.4)
    marks = {
        (s, c): p
        for s, prices in [("A", [110.0, 110.0, 120.0]), ("B", [90.0, 90.0, 80.0])]
        for c, p in zip(CUTS, prices, strict=True)
    }
    for t in [long, short]:
        net, pos = daily.daily_mtm_from_marks([t], START, END, marks)
        # 0.8 mark - 0.1 entry commission - 0.1 first cut swap = 0.6 Friday.
        assert net[0] == pytest.approx(0.6)
        assert net.sum() == pytest.approx(t.r_net, abs=1e-9)
        assert pos[0] == pytest.approx(0.5 if t.direction == "long" else -0.5)
        assert abs(pos[1]) == pytest.approx(0.5)  # Monday half day; weekend time is not Monday time
        assert pos[2] == 0
    net, pos = daily.daily_mtm_from_marks([long, short], START, END, marks)
    assert net.sum() == pytest.approx(1.8, abs=1e-9)
    assert pos.tolist() == [0.0, 0.0, 0.0]


def test_intraday_and_exact_cut_exit():
    t = trade(exit_time=at("2021-03-26T17:00"), r_net=-0.4, funding_r=-0.1)
    net, pos = daily.daily_mtm_from_marks([t], START, END, {})
    assert net.tolist() == [-0.4, 0.0, 0.0]
    assert pos.tolist() == [0.25, 0.0, 0.0]
    t = trade(exit_time=CUTS[0], r_net=1.0, swap_r=0.0)
    # Brief: exit costs belong to exit day, even at a cut. Friday uses the bid mark;
    # the remainder belongs to Saturday, mapped to Monday. No exit fill in Friday's mark.
    net, pos = daily.daily_mtm_from_marks([t], START, END, {("A", CUTS[0]): 110.0})
    assert net.tolist() == pytest.approx([0.7, 0.3, 0.0])
    assert pos.tolist() == [0.5, 0.0, 0.0]


def test_partial_exit_uses_remaining_share():
    p = SimpleNamespace(time=at("2021-03-26T17:00"), share=0.5, fill=112.0)
    t = trade(parts=(p,), swap_r=0.0, r_net=1.3)
    net, pos = daily.daily_mtm_from_marks([t], START, END, {("A", c): 110.0 for c in CUTS})
    assert net[0] == pytest.approx(0.5 + 0.4 - 0.1)
    assert pos[0] == pytest.approx(0.25 + 0.25 * 0.5)
    assert net.sum() == pytest.approx(1.3, abs=1e-9)


def test_bad_inputs_and_empty_period():
    assert daily.daily_mtm_from_marks([], START, END, {})[0].tolist() == [0.0, 0.0, 0.0]
    assert daily.daily_mtm_from_marks([], date(2021, 3, 27), date(2021, 3, 28), {})[0].size == 0
    with pytest.raises(ValueError, match="mark"):
        daily.daily_mtm_from_marks([trade()], START, END, {})
    with pytest.raises(ValueError, match="risk|stop"):
        daily.daily_mtm_from_marks([trade(initial_stop=100.0)], START, END, {})
    with pytest.raises(ValueError):
        daily.daily_mtm_from_marks([trade()], START, END, {("A", c): np.nan for c in CUTS})


def test_position_only_counts_time_inside_the_named_weekday():
    t = trade(entry_time=at("2021-03-29T22:00"), exit_time=at("2021-03-30T10:00"))
    net, position = daily.daily_mtm_from_marks([t], date(2021, 3, 26), date(2021, 3, 29), {})
    assert net.sum() == pytest.approx(t.r_net, abs=1e-9)
    assert position.tolist() == [0.0, 0.0]


def test_cache_close_time_no_lookahead_and_blocks():
    calls = []
    frame = pd.DataFrame(
        {
            "ts": pd.to_datetime(
                [CUTS[0] - timedelta(minutes=1), CUTS[0], CUTS[2] - timedelta(minutes=1)], utc=True
            ),
            "close": [110.0, 999.0, 120.0],
        }
    )

    class Sources:
        def cached_days(self, symbol):
            return [date(2021, 3, 26), date(2021, 3, 27), date(2021, 3, 28)]

        def adapter(self, symbol):
            return self

        def fetch_frame(self, symbol, tf, start, stop):
            calls.append((symbol, start, stop))
            return frame

    net, _ = daily.daily_net_r_mtm([trade()], START, END, Sources())
    assert net[0] == pytest.approx(0.6)  # opening at cut is future, cannot use 999
    assert len(calls) == 1


def record(series=None):
    return trial_log.TrialRecord(
        "f", "s", {}, [], "2021-01-01", "2021-01-05", "dev", "now", series=series
    )


def test_series_reader_and_union_matrix(tmp_path):
    (tmp_path / "a.csv").write_text(
        "date,net_r_exit_booked,net_r_mtm,position\n2021-01-01,0,1,.5\n2021-01-04,3,2,-.5\n"
    )
    (tmp_path / "b.csv").write_text("date,net_r_exit_booked,net_r_mtm,position\n2021-01-05,4,5,0\n")
    dates, values = trial_log.read_series(record("a.csv"), tmp_path, "net_r_mtm")
    assert dates == [date(2021, 1, 1), date(2021, 1, 4)]
    assert values.tolist() == [1.0, 2.0]
    dates, matrix = trial_log.series_matrix(
        [record("a.csv"), record("b.csv"), record()], "net_r_mtm", tmp_path
    )
    assert dates == [date(2021, 1, 1), date(2021, 1, 4), date(2021, 1, 5)]
    assert matrix.tolist() == [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 5.0, 0.0]]
    assert trial_log.read_series(record(), tmp_path)[0] == []
    with pytest.raises(FileNotFoundError):
        trial_log.read_series(record("missing.csv"), tmp_path)
    with pytest.raises(ValueError):
        trial_log.read_series(record("a.csv"), tmp_path, "bad")


def test_persisted_entry_fill_and_partial_details(tmp_path):
    from backtester.analytics.records import TradeRecord

    row = {
        "id": 1,
        "symbol": "A",
        "direction": "long",
        "entry_time": "2021-03-26T11:00+00:00",
        "entry_candle": "2021-03-26T10:59+00:00",
        "entry": 100.0,
        "entry_fill": 103.0,
        "initial_stop": 90.0,
        "exit_time": "2021-03-29T10:00+00:00",
        "exit_price": 120.0,
        "exit_reason": "signal",
        "r_gross": 2.0,
        "r_net": 1.6,
        "commission_r": 0.1,
        "spread_r": 0.2,
        "parts": [{"time": "2021-03-26T17:00+00:00", "share": 0.5, "price": 112.0, "fill": 111.0}],
    }
    t = TradeRecord.from_row(row)
    assert t.entry_fill == 103.0
    net, _ = daily.daily_mtm_from_marks([t], START, END, {("A", c): 110.0 for c in CUTS})
    assert net[0] == pytest.approx(0.5 * 0.8 + 0.5 * 0.7 - 0.1)
    assert net.sum() == pytest.approx(1.6, abs=1e-9)


def test_funding_cut_allocation_and_old_records(tmp_path):
    import json
    from dataclasses import asdict

    t = trade(funding_r=-0.6, r_net=0.8)
    net, _ = daily.daily_mtm_from_marks([t], START, END, {("A", c): 110.0 for c in CUTS})
    assert net[0] == pytest.approx(0.8 - 0.1 - 0.3)
    assert net.sum() == pytest.approx(0.8, abs=1e-9)
    old = asdict(record())
    old.pop("series")
    path = tmp_path / "trials.jsonl"
    path.write_text(json.dumps(old) + "\n")
    assert trial_log.read_all(path)[0].series is None


def test_cache_gap_blocks_and_future_append_do_not_change_first_cut():
    calls = []

    class Sources:
        def cached_days(self, symbol):
            return [date(2021, 3, 26), date(2021, 3, 28)]

        def adapter(self, symbol):
            return self

        def fetch_frame(self, symbol, tf, start, stop):
            calls.append(start.date())
            stamp = CUTS[0] if start.day == 26 else CUTS[2]
            return pd.DataFrame(
                {
                    "ts": pd.to_datetime([stamp - timedelta(minutes=1), stamp], utc=True),
                    "close": [110.0, 999.0],
                }
            )

    net, _ = daily.daily_net_r_mtm([trade()], START, END, Sources())
    assert net[0] == pytest.approx(0.6)
    assert calls == [date(2021, 3, 26), date(2021, 3, 28)]
