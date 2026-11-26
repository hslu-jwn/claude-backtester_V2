"""I-143 (executable I-105): pre-market ranking price and the forward row (knowledge/ideas.md › I-143)."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sf(monkeypatch):
    monkeypatch.chdir(ROOT)  # the logger loads its sibling screens by relative path
    spec = importlib.util.spec_from_file_location(
        "shelf_forward", ROOT / "research/screens/2026-11-17_shelf_forward.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def bar(ts, close):
    return {"t": ts, "o": close, "h": close, "l": close, "c": close, "v": 1, "n": 1, "vw": close}


def test_premarket_takes_last_bar_closed_by_0927_et(sf):
    # 2026-11-20 is EST (UTC-5): 09:26 ET = 14:26Z is the last bar allowed, 09:27 ET is too late, 03:59 too early
    pages = {
        "bars": {
            "AAA": [
                bar("2026-11-20T08:59:00Z", 9.0),
                bar("2026-11-20T13:10:00Z", 10.0),
                bar("2026-11-20T14:26:00Z", 11.0),
                bar("2026-11-20T14:27:00Z", 99.0),
            ],
            "BBB": [bar("2026-11-20T14:27:00Z", 50.0)],  # only a too-late bar: no price
        }
    }
    calls = []

    def fetch(params):
        calls.append(params)
        return pages

    p = sf.premarket(["AAA", "BBB"], [pd.Timestamp("2026-11-20")], fetch)
    assert calls[0]["start"] == "2026-11-20T09:00:00Z" and calls[0]["end"] == "2026-11-20T14:26:00Z"
    assert list(p.symbol) == ["AAA"]
    assert p.pre.iloc[0] == 11.0 and p.day.iloc[0] == pd.Timestamp("2026-11-20")


def test_rows_rank_on_the_signal_table_not_the_open(sf, monkeypatch):
    monkeypatch.setattr(sf.i102, "MIN_NAMES", 20)
    d0, d1 = pd.Timestamp("2026-11-19"), pd.Timestamp("2026-11-20")
    syms = [f"S{i:02d}" for i in range(20)] + ["SPY"]
    prev = pd.DataFrame(100.0, index=[d0, d1], columns=syms)
    opn = prev.copy()
    close = prev.copy()
    pre = prev.copy()
    # open gaps rank S00 highest; the pre-market price ranks S19 highest (it differs from the open)
    for i, s in enumerate(syms[:20]):
        opn.loc[d1, s] = 100.0 + (20 - i)
        pre.loc[d1, s] = 100.0 + i
        close.loc[d1, s] = opn.loc[d1, s] * (1 + i / 1e4)  # open -> close return i bp
    t = {"open": opn, "close": close, "prev_close": prev}
    members = {"2026-11": syms[:20]}
    by_pre = sf.rows_i105(t, members, d1, sig=pre)
    by_open = sf.rows_i105(t, members, d1)
    # n = 2: long the 2 lowest s, short the 2 highest. By pre: long S00, S01 (0, 1 bp), short S18, S19 (18, 19 bp)
    assert by_pre[0]["gross_bp"] == pytest.approx(0.5 - 18.5)
    assert by_open[0]["gross_bp"] == pytest.approx(18.5 - 0.5)
    assert by_pre[0]["net_bp"] == pytest.approx(by_pre[0]["gross_bp"] - sf.i102.COST)


def test_rows_skip_a_day_without_spy_premarket(sf, monkeypatch):
    monkeypatch.setattr(sf.i102, "MIN_NAMES", 20)
    d = pd.Timestamp("2026-11-20")
    syms = [f"S{i:02d}" for i in range(20)] + ["SPY"]
    t = {k: pd.DataFrame(100.0, index=[d], columns=syms) for k in ("open", "close", "prev_close")}
    pre = t["open"].copy()
    pre.loc[d, "SPY"] = np.nan
    assert sf.rows_i105(t, {"2026-11": syms[:20]}, d, sig=pre) == []
