"""fill_report: signs, spread units, sessions, commission per side, filtering, missing files."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from backtester.engine.costs import CostConfig
from backtester.tools import fill_report as fr

PAPER = "time_utc,symbol,side,signal_entry,sim_fill,sl,spread,lots,status,reason,real_fill,slippage,ticket,comment\n"
TRADES = "symbol,side,ticket,lots,entry_time,exit_time,entry_fill,exit_price,sl,exit_reason,sim_exit,sim_r,r_gross,r_net,money,risk_money\n"
SINCE = datetime(2026, 10, 27, 16, tzinfo=UTC)


def _live(tmp_path: Path, paper: str, trades: str | None) -> Path:
    day = tmp_path / "live" / "2026-10-27"
    day.mkdir(parents=True)
    (day / "paper.csv").write_text(PAPER + paper, encoding="utf-8")
    if trades is not None:
        (day / "trades.csv").write_text(TRADES + trades, encoding="utf-8")
    return tmp_path / "live"


def _fills(tmp_path, paper, trades):
    live = _live(tmp_path, paper, trades)
    p, t, _ = fr.load_live(live, SINCE, "fp")
    f, notes = fr.build_fills(p, t, CostConfig())
    return f.set_index(["ticket", "kind"]), notes


def test_entry_signs_buy_and_sell(tmp_path):
    paper = (
        "2026-10-27T16:00:00+00:00,EURUSD,buy,1.10000,1.1,1.0990,0.00002,0.1,filled,,1.10005,0.0,1,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.10000,1.1,1.1010,0.00002,0.1,filled,,1.09995,0.0,2,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.10000,1.1,1.1010,0.00002,0.1,filled,,1.10003,0.0,3,fp 1\n"
    )
    f, _ = _fills(tmp_path, paper, "")
    buy, sell, sell_better = f.loc[("1", "entry")], f.loc[("2", "entry")], f.loc[("3", "entry")]
    assert buy.slip_raw == pytest.approx(0.00005)  # bought above: adverse
    assert buy.slip == pytest.approx(0.00003)  # minus the bar spread
    assert sell.slip_raw == pytest.approx(0.00005)  # sold below: adverse
    assert sell.slip == pytest.approx(0.00005)  # a sell keeps the raw value
    assert sell_better.slip == pytest.approx(-0.00003)  # sold above: favourable
    assert buy.slip_spreads == pytest.approx(1.5)
    assert buy.slip_model_units == pytest.approx(0.00003 / CostConfig().slippage("EURUSD", 1.10005))
    assert bool(buy.worse_than_model) and not bool(sell_better.worse_than_model)


def test_exit_signs_sl_tp_signal(tmp_path):
    paper = (
        "2026-10-27T16:00:00+00:00,EURUSD,buy,1.1000,1.1,1.0990,0.0,0.1,filled,,1.1000,0,1,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.1000,1.1,1.1010,0.0,0.1,filled,,1.1000,0,2,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,buy,1.1000,1.1,1.0990,0.0,0.1,filled,,1.1000,0,3,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.1000,1.1,1.1010,0.00002,0.1,filled,,1.1000,0,4,fp 1\n"
    )
    e = "2026-10-27T16:00:00+00:00"
    x = "2026-10-27T16:05:00+00:00"
    trades = (
        f"EURUSD,buy,1,0.1,{e},{x},1.1,1.09985,1.0999,stop_loss,1.0999,-1,-1,-1,-1,1\n"  # sell below SL
        f"EURUSD,sell,2,0.1,{e},{x},1.1,1.10105,1.1010,stop_loss,1.1010,-1,-1,-1,-1,1\n"  # buy above SL
        f"EURUSD,buy,3,0.1,{e},{x},1.1,1.10090,1.0990,take_profit,1.1010,1,1,1,1,1\n"  # TP 1.1010, 0.0001 short
        f"EURUSD,sell,4,0.1,{e},{x},1.1,1.09990,1.1010,signal,1.0999,0,0,0,0,1\n"  # buy-to-close at bid + spread
    )
    f, _ = _fills(tmp_path, paper, trades)
    assert f.loc[("1", "stop_loss")].slip == pytest.approx(0.00005)
    assert f.loc[("2", "stop_loss")].slip == pytest.approx(0.00005)
    tp = f.loc[("3", "take_profit")]
    assert tp.ref_price == pytest.approx(1.1010)
    assert tp.slip == pytest.approx(0.0001)  # filled below the TP: adverse
    assert tp.model_slip == 0
    sig = f.loc[("4", "signal")]
    assert sig.slip_raw == pytest.approx(-0.0)  # 1.0999 - ... bought at 1.0999 = ref
    assert sig.slip == pytest.approx(-0.00002)  # spread removed for a short's close


def test_sessions():
    assert [fr.session_of(h) for h in (22, 23, 0, 6, 7, 12, 13, 21)] == [
        "Asia", "Asia", "Asia", "Asia", "London", "London", "New York", "New York",
    ]  # fmt: skip


def test_spread_vs_model(tmp_path):
    c = CostConfig()
    at = datetime(2026, 10, 27, 16, tzinfo=UTC)
    table = c.spread("EURUSD", at, 1.1)
    paper = f"2026-10-27T16:00:00+00:00,EURUSD,sell,1.1,1.1,1.101,{2 * table},0.1,filled,,1.1,0,1,fp 1\n"
    f, _ = _fills(tmp_path, paper, "")
    r = f.loc[("1", "entry")]
    assert r.model_spread_table == pytest.approx(table)
    assert r.spread_vs_table == pytest.approx(2.0)
    assert r.model_spread_fixed > 0
    assert r.session == "New York"


def test_filter_since_comment_and_missing(tmp_path):
    paper = (
        "2026-10-27T15:59:00+00:00,EURUSD,sell,1.1,1.1,1.101,0,0.1,filled,,1.1,0,1,fp 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.1,1.1,1.101,0,0.1,filled,,1.1,0,2,orb 1\n"
        "2026-10-27T16:00:00+00:00,EURUSD,sell,1.1,1.1,1.101,0,0.1,skipped,stale,,,,fp 1\n"
        "2026-10-27T16:30:00+00:00,EURUSD,sell,1.1,1.1,1.101,0,0.1,filled,,1.1,0,4,fp 2\n"
    )
    live = _live(tmp_path, paper, None)  # trades.csv missing
    p, t, notes = fr.load_live(live, SINCE, "fp")
    assert list(p["ticket"]) == ["4"]
    assert t.empty
    assert any("trades.csv" in n for n in notes)
    fills, report = fr.run(live, SINCE, "fp", None, tmp_path / "out")
    assert len(fills) == 1
    assert (tmp_path / "out" / "fills.csv").exists() and "no deals file" in report
    # nothing at all
    fills, report = fr.run(tmp_path / "nope", SINCE, "fp", tmp_path / "x.csv", tmp_path / "o2")
    assert fills.empty and "no date folders" in report


def _deal(**kw):
    base = dict(ticket=1,  # noqa: C408
                position_id=10, symbol="EURUSD", time=1_790_000_000, type=0, entry=0,
                volume=1.0, price=1.1, commission=-2.5, fee=0.0, swap=0.0, profit=0.0,
                comment="fp 1", magic=1)  # fmt: skip
    return SimpleNamespace(**{**base, **kw})


def test_deals_to_csv_and_commission(tmp_path):
    deals = [
        _deal(ticket=1, position_id=10, commission=-2.5),  # $5 round turn / 2: as the model
        _deal(ticket=2, position_id=10, entry=1, type=1, commission=-2.5),
        _deal(ticket=3, position_id=11, symbol="XAUUSD", volume=2.0, price=4000.0, commission=-0.0007 * 4000 * 100 * 2 * 0.01),
        _deal(ticket=4, position_id=12, symbol="XAGUSD", volume=1.0, price=50.0, commission=-1.0, comment=""),
    ]  # fmt: skip
    path = tmp_path / "deals.csv"
    text = fr.deals_to_csv(deals, path)
    assert text.splitlines()[0].split(",") == fr.DEAL_COLUMNS and path.read_text() == text
    assert "2026" in text.splitlines()[1] or "2025" in text.splitlines()[1]
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    assert df["type"].tolist()[:2] == ["buy", "sell"] and df["entry"].tolist()[:2] == ["in", "out"]
    tab = fr.commission_table(df, {"10", "11", "12"}, CostConfig())
    eur = tab.loc["EURUSD"]
    assert eur.real_per_lot_side == pytest.approx(2.5) and eur.model_per_lot_side == pytest.approx(
        2.5
    )
    assert not eur.flag
    # metal: 0.0007 % per side (= 7e-6) x 4000 x 100 oz = $2.8 per lot per side
    xau = tab.loc["XAUUSD"]
    assert xau.model_per_lot_side == pytest.approx(7e-6 * 4000 * 100)
    assert xau.real_per_lot_side == pytest.approx(0.0007 * 4000 * 100 * 0.01)  # = 2.8
    assert not xau.flag
    assert tab.loc["XAGUSD"].flag  # $1 vs 7e-6 x 50 x 5000 = 1.75: -43 %


def test_commission_flag_over_10_percent(tmp_path):
    import pandas as pd

    df = pd.DataFrame([{"ticket": "1", "position_id": "5", "symbol": "EURUSD", "entry": "in",
                        "volume": "1", "price": "1.1", "commission": "-2.8", "fee": "0",
                        "comment": ""}])  # fmt: skip
    tab = fr.commission_table(df, {"5"}, CostConfig())
    assert tab.loc["EURUSD"].diff_pct == pytest.approx(12.0) and tab.loc["EURUSD"].flag


def _deal_df(rows):
    import pandas as pd

    base = {"ticket": "1", "position_id": "5", "symbol": "NATGAS.cash", "entry": "in",
            "volume": "1", "price": "3.0", "commission": "-1", "fee": "0", "comment": "fp 1"}  # fmt: skip
    return pd.DataFrame([{**base, **r} for r in rows])


def test_commission_maps_broker_names_to_ours():
    # review #6: NATGAS.cash / DXY.cash / US100.cash must find the settings of NATGAS / DXY / NAS100
    df = _deal_df(
        [{"symbol": "NATGAS.cash"}, {"symbol": "US100.cash", "ticket": "2", "position_id": "6"}]
    )
    tab = fr.commission_table(df, {"5", "6"}, CostConfig())
    assert set(tab.index) == {"NATGAS", "NAS100"}


def test_commission_only_positions_of_the_selected_fills():
    # review #7: a later-excluded (before --since) fp deal must not count: only the tickets given
    df = _deal_df([{"position_id": "5"}, {"ticket": "2", "position_id": "99", "comment": "fp 2"}])
    tab = fr.commission_table(df, {"5"}, CostConfig())
    assert tab.loc["NATGAS"].deals == 1
