"""The live bot (ROADMAP 7.2) against a fake MT5 and hand-built M1 bars. No real terminal.

World: US500 (FTMO name US500.cash), server clock = UTC, winter (New York = UTC-5). 15 earlier
sessions each have high 105 / low 95 / close 100, so the daily ATR is 10 and the band (0.25 ATR)
is 100 +/- 2.5. On 2026-01-12 the bar 09:40 New York (14:40 UTC, closes 14:41) closes at 103:
a long at 103, stop 97.5. Risk 0.25 % of 100000 = 250 over the 5.7 points from the ask 103.2 to
the stop at 1.0 per point = 43.86 lots -> 43.8 (step 0.1); R is measured over the signal's 5.5.
The session exit is the bar closing 15:55 New York = 20:55 UTC.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fake_bot_mt5 import Deal2, FakeBotMt5
from fake_mt5 import Position

from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.live import orders
from backtester.live.bot import Bot, BotConfig, BotDisconnected, forward_strategy_config
from backtester.live.orders import MAGIC, DemoLockError
from backtester.live.trading_settings import TradingSettings
from backtester.risk.prop_rules import GuardConfig
from backtester.strategy.opening_range.config import EntryMode, OpeningRangeConfig

NY = ZoneInfo("America/New_York")
SYM, BROKER = "US500", "US500.cash"
DAY = date(2026, 1, 12)


def ny(day: date, hh: int, mm: int) -> datetime:
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=NY).astimezone(UTC)


def row(ts: datetime, o, h, lo, c, spread_points=20):
    return (int(ts.timestamp()), o, h, lo, c, spread_points)


def history_rows() -> list[tuple]:
    rows = []
    day, made = DAY - timedelta(days=1), 0
    while made < 15:
        if day.weekday() < 5:
            rows += [
                row(ny(day, 9, 29), 100, 100, 100, 100),
                row(ny(day, 9, 30), 100, 105, 95, 100),
                row(ny(day, 15, 54), 100, 100, 100, 100),
            ]
            made += 1
        day -= timedelta(days=1)
    return sorted(rows)


def today_rows() -> list[tuple]:
    rows = []
    t, end = ny(DAY, 9, 29), ny(DAY, 15, 59)
    while t <= end:
        if t == ny(DAY, 9, 40):
            rows.append(row(t, 100, 103.5, 100, 103))  # the breakout: closes above 102.5
        else:
            rows.append(row(t, 100, 100, 100, 100))
        t += timedelta(minutes=1)
    return rows


class Clock:
    def __init__(self, t: datetime):
        self.t = t
        self.sleeps: list[float] = []
        self.on_sleep = None

    def __call__(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.t += timedelta(seconds=seconds)
        if self.on_sleep:
            self.on_sleep(self)


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


class World:
    def __init__(self, tmp_path, **fake_kw):
        self.fake = FakeBotMt5(**fake_kw)
        self.fake.initialize()
        self.fake.add_symbol(
            BROKER, digits=2, point=0.01, trade_tick_size=0.01, trade_tick_value=0.01,
            volume_min=0.1, volume_step=0.1, volume_max=500.0, trade_stops_level=0,
        )  # fmt: skip
        self.fake.set_rates(BROKER, self.fake.TIMEFRAME_M1, history_rows() + today_rows())
        self.fake.deals[900] = Deal2(  # the account's first deal: the initial balance
            900, 0, 0, "", 2, 0.0, 0.0, 0, 0, 100_000.0, 0.0, 0.0, 0.0, 1000
        )
        self.set_tick(103.0, 103.2)
        self.clock = Clock(ny(DAY, 9, 38))
        self.out = tmp_path / "live"
        self.settings = TradingSettings(symbols={SYM: BROKER}, server_clock=ServerClock("UTC", 0))

    def set_tick(self, bid, ask):
        self.fake.set_tick(BROKER, bid, ask, 0)

    def config(self, **kw) -> BotConfig:
        base = dict(  # noqa: C408
            symbols=(SYM,),
            strategy=OpeningRangeConfig(
                entry_mode=EntryMode.BAND, band_atr=0.25, min_rel_volume=0.0
            ),
            out_dir=self.out,
            mt5_cache_dir=self.out.parent / "cache_mt5",
            live_cache_dir=self.out.parent / "cache_live",
            update_cache_at_start=False,
            verbose=False,
        )
        return BotConfig(**{**base, **kw})

    def bot(self, **kw) -> Bot:
        return Bot(
            self.config(**kw), self.fake, self.settings, now=self.clock, sleep=self.clock.sleep
        )

    def at(self, t: datetime):
        self.clock.t = t

    def decisions(self) -> list[dict]:
        files = list(self.out.glob("*/orders.jsonl"))
        return [json.loads(line) for f in files for line in f.read_text().splitlines()]

    def csv(self, name: str) -> list[dict]:
        files = list(self.out.glob(f"*/{name}"))
        if not files:
            return []
        with files[0].open(newline="") as f:
            return list(csv.DictReader(f))

    def opens(self) -> list[dict]:
        return [r for r in self.fake.requests if r["action"] == 1 and "position" not in r]

    def closes(self) -> list[dict]:
        return [r for r in self.fake.requests if r["action"] == 1 and "position" in r]


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def started(world: World, t: datetime | None = None, **kw) -> Bot:
    world.at(t or ny(DAY, 9, 38))
    bot = world.bot(**kw)
    bot.connect()
    bot.start()
    return bot


# --- config ----------------------------------------------------------------------------------


def test_forward_test_settings_are_the_spec():
    cfg = forward_strategy_config()
    assert (cfg.entry_mode, cfg.band_atr, cfg.target_r, cfg.min_rel_volume) == (
        EntryMode.BAND,
        0.25,
        0.0,
        1.5,
    )
    bot = BotConfig()
    assert bot.symbols == ("US30", "US500", "NAS100", "US2000")
    assert bot.risk_percent == 0.25 and bot.guard.daily_stop_percent == 2.0


# --- signals and orders ----------------------------------------------------------------------


def test_no_order_before_the_confirming_bar_closes(world):
    bot = started(world)
    world.at(ny(DAY, 9, 40) + timedelta(seconds=30))  # the 09:40 bar is still forming
    assert bot.cycle() == "continue"
    assert world.fake.requests == []
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    assert len(world.opens()) == 1


def test_one_order_per_signal_with_sl_lots_and_magic(world):
    bot = started(world)
    for minute in range(41, 50):
        world.at(ny(DAY, 9, minute) + timedelta(seconds=3))
        bot.cycle()
    (request,) = world.opens()
    # sized from the executable ask 103.2 (review live #7): 250 / (103.2 - 97.5) = 43.86 -> 43.8
    assert request["volume"] == 43.8
    assert request["sl"] == 97.5 and request["tp"] == 0.0
    assert request["magic"] == MAGIC and request["comment"].startswith("orb ")
    assert request["type"] == world.fake.ORDER_TYPE_BUY
    assert len(world.fake.positions) == 1
    paper = world.csv("paper.csv")
    assert len(paper) == 1 and paper[0]["status"] == "filled"
    assert float(paper[0]["sim_fill"]) == pytest.approx(103.2)  # entry 103 + the bar's spread 0.2
    assert float(paper[0]["real_fill"]) == pytest.approx(103.2)
    assert float(paper[0]["slippage"]) == pytest.approx(0.0)


def test_fill_price_comes_from_the_deal_not_from_the_result(tmp_path):
    w = World(tmp_path, delay_polls=3)
    bot = started(w)
    w.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    w.set_tick(103.0, 103.5)
    bot.cycle()
    paper = w.csv("paper.csv")
    assert float(paper[0]["real_fill"]) == pytest.approx(103.5)
    assert float(paper[0]["slippage"]) == pytest.approx(0.3)


def test_exit_at_1555_closes_the_position_once(world):
    bot = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    world.set_tick(104.0, 104.2)
    world.at(ny(DAY, 15, 55) + timedelta(seconds=3))  # the 15:54 bar closes at 15:55
    bot.cycle()
    assert world.fake.positions == {} and len(world.closes()) == 1
    (trade,) = world.csv("trades.csv")
    assert trade["exit_reason"] == "signal"
    assert float(trade["exit_price"]) == pytest.approx(104.0)
    assert float(trade["r_net"]) == pytest.approx((104.0 - 103.2) / 5.5)
    world.at(ny(DAY, 15, 59) + timedelta(seconds=3))
    bot.cycle()
    assert len(world.closes()) == 1 and len(world.opens()) == 1


def test_server_side_stop_is_detected_and_reported_in_r(world):
    bot = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    (ticket,) = world.fake.positions
    world.fake.stop_out(ticket, 97.5, world.fake.DEAL_REASON_SL)
    world.at(ny(DAY, 9, 43) + timedelta(seconds=3))
    bot.cycle()
    (trade,) = world.csv("trades.csv")
    assert trade["exit_reason"] == "stop_loss"
    assert float(trade["r_net"]) == pytest.approx((97.5 - 103.2) / 5.5)
    assert float(trade["sim_r"]) == pytest.approx((97.5 - 103.2) / 5.5)


def test_order_below_minimum_lot_is_skipped_with_a_reason(tmp_path):
    w = World(tmp_path, balance=100.0)
    bot = started(w, guard=GuardConfig(initial_balance=100.0))
    w.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    assert w.fake.requests == []
    skip = [d for d in w.decisions() if d["label"] == "skip"]
    assert skip and "below the minimum lot" in skip[0]["request"]["reason"]
    assert w.csv("paper.csv")[0]["status"] == "skipped"


def test_rejected_order_is_logged_and_not_tracked(world):
    bot = started(world)
    world.fake.reject[(world.fake.TRADE_ACTION_DEAL, None)] = world.fake.TRADE_RETCODE_MARKET_CLOSED
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    assert world.fake.positions == {}
    skip = [d for d in world.decisions() if d["label"] == "skip"]
    assert "market closed" in skip[0]["request"]["reason"]
    assert world.csv("paper.csv")[0]["status"] == "skipped"


# --- the daily guard -------------------------------------------------------------------------


def test_daily_stop_blocks_new_orders(world):
    bot = started(world)
    world.fake.equity = 97_900.0  # -2.1 % today
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    assert bot.cycle() == "continue"
    assert world.fake.requests == []
    assert any("daily stop" in str(d["request"]) for d in world.decisions())


def test_daily_stop_closes_own_positions_and_keeps_the_users(world):
    bot = started(world)
    world.fake.positions[1] = Position(1, BROKER, 0, 1.0, 100.0, 0.0, 0.0, 0, "mine", 0)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    assert len(world.fake.positions) == 2
    world.fake.equity = 97_800.0
    world.at(ny(DAY, 9, 42) + timedelta(seconds=3))
    assert bot.cycle() == "continue"
    assert list(world.fake.positions) == [1]
    assert bot.blocked


def test_ftmo_breach_closes_everything_and_stops(world):
    bot = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    world.fake.equity = 94_000.0
    world.at(ny(DAY, 9, 42) + timedelta(seconds=3))
    assert bot.cycle() == "stop"
    assert world.fake.positions == {}


def test_the_block_ends_with_the_next_prague_day(world):
    bot = started(world)
    world.fake.equity = 97_900.0
    world.at(ny(DAY, 9, 42))
    bot.cycle()
    assert bot.blocked
    world.fake.balance = world.fake.equity = 97_900.0  # next day starts from the new balance
    world.at(ny(DAY + timedelta(days=1), 3, 0))  # 09:00 Prague next day
    bot.cycle()
    assert not bot.blocked


# --- stop files ------------------------------------------------------------------------------


def test_stop_file_stops_and_closes_nothing(world):
    bot = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    world.out.mkdir(parents=True, exist_ok=True)
    (world.out / "STOP").write_text("")
    world.at(ny(DAY, 9, 42) + timedelta(seconds=3))
    assert bot.cycle() == "stop"
    assert len(world.fake.positions) == 1 and world.closes() == []


def test_emergency_file_closes_own_positions_only_and_stops(world):
    bot = started(world)
    world.fake.positions[1] = Position(1, BROKER, 0, 1.0, 100.0, 0.0, 0.0, 0, "mine", 0)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    bot.cycle()
    world.out.mkdir(parents=True, exist_ok=True)
    (world.out / "EMERGENCY").write_text("")
    world.at(ny(DAY, 9, 42) + timedelta(seconds=3))
    assert bot.cycle() == "stop"
    assert list(world.fake.positions) == [1]
    assert not (world.out / "EMERGENCY").exists()


# --- connection ------------------------------------------------------------------------------


def test_real_account_refuses_at_start_without_sending(tmp_path):
    w = World(tmp_path, trade_mode=FakeBotMt5.ACCOUNT_TRADE_MODE_REAL)
    bot = w.bot()
    with pytest.raises(DemoLockError):
        bot.connect()
    assert w.fake.requests == []
    assert bot.run() == 1
    assert w.fake.requests == [] and not w.fake.initialized


def test_connect_retries_with_backoff(world):
    world.fake.shutdown()
    world.fake.fail_init = 2
    bot = world.bot()
    bot.connect()
    assert world.fake.init_calls == 4  # the fixture's own + 2 failures + 1 success
    assert world.clock.sleeps == [5.0, 10.0]


def test_cycle_raises_when_the_terminal_is_gone(world):
    bot = started(world)
    world.fake.shutdown()
    with pytest.raises(BotDisconnected):
        bot.cycle()


def test_run_reconnects_and_does_not_duplicate_the_order(world):
    state = {"n": 0}

    def hook(clock):
        state["n"] += 1
        if clock.t >= ny(DAY, 9, 42) and "down" not in state:
            state["down"] = True
            world.fake.shutdown()
            world.fake.fail_init = 1
        if clock.t >= ny(DAY, 9, 50):
            world.out.mkdir(parents=True, exist_ok=True)
            (world.out / "STOP").write_text("")

    world.clock.on_sleep = hook
    world.at(ny(DAY, 9, 38))
    bot = world.bot()
    assert bot.run() == 0
    assert len(world.opens()) == 1
    assert 5.0 in world.clock.sleeps  # the backoff
    assert world.fake.init_calls >= 3


# --- restart ---------------------------------------------------------------------------------


def test_restart_mid_day_resumes_without_a_second_order(world):
    first = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    first.cycle()
    (ticket,) = world.fake.positions
    world.at(ny(DAY, 10, 20))
    second = world.bot()
    second.connect()
    second.start()
    second.cycle()
    assert len(world.opens()) == 1 and list(world.fake.positions) == [ticket]
    world.set_tick(104.0, 104.2)
    world.at(ny(DAY, 15, 55) + timedelta(seconds=3))
    second.cycle()
    assert world.fake.positions == {} and len(world.closes()) == 1
    assert len(world.csv("trades.csv")) == 1


def test_restart_after_the_trade_ended_does_not_trade_the_old_signal(world):
    first = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    first.cycle()
    (ticket,) = world.fake.positions
    world.fake.stop_out(ticket, 97.5, world.fake.DEAL_REASON_SL)
    world.at(ny(DAY, 10, 20))
    second = world.bot()
    second.connect()
    second.start()
    second.cycle()
    assert len(world.opens()) == 1 and world.fake.positions == {}


def test_a_position_left_open_past_the_exit_is_closed_on_restart(world):
    first = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    first.cycle()
    world.at(ny(DAY, 15, 58))
    second = world.bot()
    second.connect()
    second.start()
    assert world.fake.positions == {} and len(world.closes()) == 1


# --- warm-up history completeness ------------------------------------------------------------


def quote_at(world: World, t: datetime) -> None:
    """The terminal's last quote time for the symbol (server clock = UTC)."""
    world.fake.symbols[BROKER] = world.fake.symbols[BROKER]._replace(time=int(t.timestamp()))


def truncate(world: World, last: datetime) -> list[tuple]:
    """Cut the M1 history after `last` (the terminal has not downloaded the rest); returns the
    full rows so a test can restore them."""
    full = history_rows() + today_rows()
    world.fake.set_rates(
        BROKER, world.fake.TIMEFRAME_M1, [r for r in full if r[0] <= int(last.timestamp())]
    )
    return full


def kinds(world: World) -> list[str]:
    return [d["label"] for d in world.decisions()]


def test_complete_history_has_no_retry_and_no_warning(world):
    quote_at(world, ny(DAY, 9, 38))
    started(world)
    assert world.clock.sleeps == []
    assert "stale_history" not in kinds(world) and "history_complete" not in kinds(world)


def test_truncated_history_is_refetched_fed_once_without_warning(world):
    quote_at(world, ny(DAY, 9, 38))
    full = truncate(world, ny(DAY, 9, 29))
    world.clock.on_sleep = lambda _c: world.fake.set_rates(BROKER, world.fake.TIMEFRAME_M1, full)
    bot = started(world)
    assert world.clock.sleeps == [3.0]
    ks = kinds(world)
    assert "stale_history" not in ks and ks.count("history_complete") == 1
    ts = [c.ts for c in bot.symbols[SYM].candles]
    assert ts == sorted(set(ts)) and ts[-1] == ny(DAY, 9, 37)


def test_always_truncated_history_warns_once_and_the_bot_continues(world):
    quote_at(world, ny(DAY, 9, 38))
    truncate(world, ny(DAY, 9, 29))
    bot = started(world, history_attempts=4)
    assert world.clock.sleeps == [3.0, 3.0, 3.0]
    stale = [d for d in world.decisions() if d["label"] == "stale_history"]
    assert len(stale) == 1
    assert bot.symbols[SYM].candles[-1].ts == ny(DAY, 9, 29)
    world.at(ny(DAY, 9, 39) + timedelta(seconds=3))
    assert bot.cycle() is not None


def test_market_closed_weekend_history_counts_as_complete(world):
    quote_at(world, ny(DAY, 16, 0))  # the last quote of Monday's session
    started(world, t=ny(DAY, 16, 30) + timedelta(days=5))
    assert world.clock.sleeps == []
    assert "stale_history" not in kinds(world)


def test_next_cycle_fills_the_gap_left_by_a_short_warm_up(world):
    quote_at(world, ny(DAY, 9, 38))
    full = truncate(world, ny(DAY, 9, 29))
    bot = started(world, history_attempts=1)
    fed = []
    strategy = bot.symbols[SYM].strategy
    original = strategy.on_candle
    strategy.on_candle = lambda now, views: (fed.append(now), original(now, views))[1]
    world.fake.set_rates(BROKER, world.fake.TIMEFRAME_M1, full)
    world.at(ny(DAY, 9, 38) + timedelta(seconds=3))
    bot.cycle()
    ts = [c.ts for c in bot.symbols[SYM].candles]
    assert ts[-1] == ny(DAY, 9, 37)
    assert ts == sorted(set(ts))
    assert all(
        b - a == timedelta(minutes=1)
        for a, b in zip(ts[ts.index(ny(DAY, 9, 29)) :], ts[ts.index(ny(DAY, 9, 29)) + 1 :])
    )
    assert fed == sorted(set(fed)) and fed[0] == ny(DAY, 9, 31)
