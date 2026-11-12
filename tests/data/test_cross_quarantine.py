"""Quarantine of MT5 FX days whose prices disagree with both their own JPY cross and histdata.

Spec: ARCHITECTURE.md > Data sources (cross-price quarantine); docs/data-fix-check.md (finding:
MT5 GBPUSD Feb-Sep 2019). Written before the implementation.
"""

import json
from datetime import date

import pandas as pd

from backtester.data.cache import cache_path, read_cached_day, write_atomic
from backtester.data.mt5_download import cache_frame

DAY = date(2019, 6, 13)


def fx_day(root, symbol, day, prices, n=400):
    """`n` minutes from 08:00 UTC; `prices(i)` gives the close of minute i."""
    ts = pd.date_range(f"{day} 08:00", periods=n, freq="min", tz="UTC")
    p = [prices(i) for i in range(n)]
    bars = pd.DataFrame({"ts": ts, "open": p, "high": p, "low": p, "close": p,
                         "volume": 1.0, "spread": 0.0})
    write_atomic(cache_frame(bars), cache_path(root, symbol, day))


def wave(i):
    return (i * 37 % 101) / 1e4  # deterministic, irregular, ~0-100 pips


def market(mt5, hist, day=DAY, gbp_mt5=0.0, gbp_hist=0.0, cross=0.0, n=400):
    """GBPUSD = GBPJPY / USDJPY; offsets (price units) make one source wrong."""
    usdjpy = lambda i: 108 + wave(i) * 100
    gbpusd = lambda i: 1.27 + wave(i)
    fx_day(mt5, "USDJPY", day, usdjpy, n)
    fx_day(mt5, "GBPJPY", day, lambda i: gbpusd(i) * usdjpy(i) * (1 + cross), n)
    fx_day(mt5, "GBPUSD", day, lambda i: gbpusd(i) + gbp_mt5, n)
    fx_day(hist, "GBPUSD", day, lambda i: gbpusd(i) + gbp_hist, n)


def test_mt5_day_off_from_cross_and_histdata_is_flagged(tmp_path):
    from backtester.data.cache_repair import cross_mismatch_days

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    market(mt5, hist, gbp_mt5=8e-4)
    flagged = cross_mismatch_days(mt5, hist, "GBPUSD")
    assert list(flagged) == [str(DAY)]
    assert abs(flagged[str(DAY)]["cross_pips"] - 8) < 0.01
    assert abs(flagged[str(DAY)]["histdata_pips"] - 8) < 0.01


def test_a_bad_cross_or_bad_histdata_does_not_blame_the_mt5_day(tmp_path):
    from backtester.data.cache_repair import cross_mismatch_days

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    market(mt5, hist, cross=8e-4)  # GBPJPY wrong: GBPUSD still agrees with histdata
    assert cross_mismatch_days(mt5, hist, "GBPUSD") == {}
    market(mt5, hist, gbp_hist=8e-4)  # histdata wrong: MT5 agrees with its cross
    assert cross_mismatch_days(mt5, hist, "GBPUSD") == {}


def test_small_differences_short_days_and_test_period_stay(tmp_path):
    from backtester.data.cache_repair import cross_mismatch_days

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    market(mt5, hist, gbp_mt5=1.5e-4)  # below 2 pips: normal feed difference
    market(mt5, hist, day=date(2019, 6, 14), gbp_mt5=8e-4, n=200)  # too few minutes to judge
    market(mt5, hist, day=date(2021, 9, 14), gbp_mt5=8e-4)  # test period: FTMO data stays
    assert cross_mismatch_days(mt5, hist, "GBPUSD") == {}


def test_usd_base_pairs_use_usdjpy_over_the_cross(tmp_path):
    from backtester.data.cache_repair import CROSSES, cross_mismatch_days

    assert CROSSES["USDCAD"] == ("USDJPY", "CADJPY")
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    usdjpy = lambda i: 108 + wave(i) * 100
    usdcad = lambda i: 1.32 + wave(i)
    fx_day(mt5, "USDJPY", DAY, usdjpy)
    fx_day(mt5, "CADJPY", DAY, lambda i: usdjpy(i) / usdcad(i))
    fx_day(mt5, "USDCAD", DAY, lambda i: usdcad(i) + 8e-4)
    fx_day(hist, "USDCAD", DAY, usdcad)
    assert list(cross_mismatch_days(mt5, hist, "USDCAD")) == [str(DAY)]


def test_quarantine_moves_files_records_why_and_is_idempotent(tmp_path):
    from backtester.data.adapters.cache_adapter import PreferredCacheAdapter
    from backtester.data.cache_repair import cross_mismatch_days, quarantine_days, quarantined_days

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    market(mt5, hist, gbp_mt5=8e-4)
    original = read_cached_day(cache_path(mt5, "GBPUSD", DAY))
    flagged = cross_mismatch_days(mt5, hist, "GBPUSD")
    assert quarantine_days(mt5, "GBPUSD", flagged) == 1
    assert not cache_path(mt5, "GBPUSD", DAY).exists()
    kept = cache_path(mt5 / "_quarantine", "GBPUSD", DAY)
    pd.testing.assert_frame_equal(read_cached_day(kept), original)  # moved, not lost
    assert quarantined_days(mt5, "GBPUSD") == json.loads(json.dumps(flagged))
    assert quarantine_days(mt5, "GBPUSD", flagged) == 0
    assert PreferredCacheAdapter(hist, mt5)._path("GBPUSD", DAY) == cache_path(hist, "GBPUSD", DAY)


def test_repair_drops_a_quarantined_day_that_a_download_brought_back(tmp_path):
    from backtester.data.cache_repair import cross_mismatch_days, quarantine_days, repair_mt5

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    market(mt5, hist, gbp_mt5=8e-4)
    quarantine_days(mt5, "GBPUSD", cross_mismatch_days(mt5, hist, "GBPUSD"))
    market(mt5, hist, gbp_mt5=8e-4)  # a re-download writes the bad day again
    table = {str(DAY): {"status": "proven", "shift": 0, "readings": {}}}
    decisions = repair_mt5("GBPUSD", mt5, hist, server_table=table, log=lambda *_: None)
    assert not cache_path(mt5, "GBPUSD", DAY).exists()
    assert [d["decision"] for d in decisions if d["day"] == str(DAY)] == [
        "drop: quarantined (price differs from own cross and histdata)"]
